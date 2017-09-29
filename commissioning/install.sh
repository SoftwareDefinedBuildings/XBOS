#!/bin/bash


RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
INFO=$YELLOW
PROMPT=$BLUE
ERROR=$RED
OK=$GREEN
NC='\033[0m' # No Color

# Black        0;30     Dark Gray     1;30
# Red          0;31     Light Red     1;31
# Green        0;32     Light Green   1;32
# Brown/Orange 0;33     Yellow        1;33
# Blue         0;34     Light Blue    1;34
# Purple       0;35     Light Purple  1;35
# Cyan         0;36     Light Cyan    1;36
# Light Gray   0;37     White         1;37

command_exists() {
	command -v "$@" > /dev/null 2>&1
}

full_path() {
    command -v "$@"
}

confirmY() {
    # call with a prompt string or use a default
    #read -r -p "${1:-Are you sure? [Y/n]} " response
    echo -ne "${1:-Are you sure? [Y/n]}"
    read -r response
    case "$response" in
        [nN][oO]|[nN])
            false
            ;;
        *)
            true
            ;;
    esac
}

confirmN() {
    # call with a prompt string or use a default
    echo -ne "${1:-Are you sure? [y/N]}"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY])
            true
            ;;
        *)
            false
            ;;
    esac
}

sleep_til_valid() {
    echo -e "${INFO}Waiting until ${1} is valid${NC}..."
    valid=$(bw2 i ${1} | sed -n 's/.*Registry: \(.*\).*/\1/p')
    while [ "$valid" != "valid" ]; do
        sleep 5
        valid=$(bw2 i ${1} | sed -n 's/.*Registry: \(.*\).*/\1/p')
    done
}


do_install() {
	cat >&2 <<'EOF'
    logo goes here :)
EOF
    echo='echo -e'

    $echo "${INFO}Automated installer for XBOS${NC}"

    $echo "${INFO}If you want this to go faster, pre-install BOSSWAVE (curl get.bw2.io/agent | bash)${NC}"

    #confirmY "${PROMPT}Are you setting up a namespace? [Y/n]${NC}"
    #doingNS=$?
    #if [ $doingNS -eq 0 ]; then
    #    confirmN "${PROMPT}Do you have a namespace entity already? [y/N]${NC}"
    #    if [ $? -eq 0 ]; then
    #        echo -ne "${PROMPT}Path to entity file: ${NC}"
    #        read nspath
    #        $echo "${INFO}Copying to this directory${NC}"
    #        cp $nspath namespace.ent
    #    fi
    #    confirmY "${PROMPT}Do you want to set up an alias? [Y/n]${NC}"
    #    setupAlias=$?
    #    if [ $setupAlias -eq 0 ]; then
    #        echo -ne "${PROMPT}Namespace alias: ${NC}"
    #        read alias
    #    fi
    #fi
    #echo -ne "${PROMPT}Contact (full name <email>): ${NC}"
    #read BW2_DEFAULT_CONTACT


    # setup $user, $sh_c and $curl like from bosswave
	user="$(id -un 2>/dev/null || true)"

    export SYSTEMD_PAGER=''

    # handle systemd/init
    $sh_c "systemctl > /dev/null 2>&1"
    if [ $? -ne 0 ]; then
        # use init
        start_bw2="/etc/init.d/bw2 start > /dev/null 2>&1"
        reload_bw2="/etc/init.d/bw2 restart > /dev/null 2>&1"
    else
        start_bw2="systemctl start -q --no-pager bw2.service > /dev/null 2>&1"
        reload_bw2="systemctl daemon-reload -q --no-pager > /dev/null 2>&1 && systemctl restart -q --no-pager bw2.service > /dev/null 2>&1"
    fi

	sh_c='sh -c'
	if [ "$user" != 'root' ]; then
		if command_exists sudo; then
			sh_c='sudo -E sh -c'
		elif command_exists su; then
			sh_c='su -c'
		else
			cat >&2 <<-'EOF'
            ${ERROR}
			Error: this installer needs the ability to run commands as root.
			We are unable to find either "sudo" or "su" available to make this happen.
            ${NC}
			EOF
			exit 1
		fi
	fi

    # install dependencies
    $echo "${INFO}Updating apt repos and installing dependencies${NC}"

    $sh_c 'apt-get update >/dev/null'
    $sh_c 'apt-get install -y git python2.7 python-pip python-dev curl bc docker.io'

    # trick to get directory of executing script, and move there
    dot="$(cd "$(dirname "$0")"; pwd)"
    cd $dot

    # import config
    source config.sh


    # set up local git repository
    $sh_c "git init"

    # check if bosswave is installed, but update it either way
    if command_exists bw2; then
        $echo "${INFO}BOSSWAVE already installed! Updating...${NC}"
    else
        $echo "${INFO}Installing Bosswave${NC}"
    fi

    $sh_c $(curl get.bw2.io/agent | bash)
    sleep 5
    $sh_c "$start_bw2"
    $echo "${INFO}Wait for agent to restart${NC}"
    sleep 20
    # xargs trick to remove surrounding whitespace
    current_block=$(bw2 status  | sed -n -e 's/Current block: \(.*\).*/\1/p' | xargs)
    seen_block=$(bw2 status  | sed -n -e 's/Seen block: \(.*\).*/\1/p' | xargs)
    diff=$(($seen_block - $current_block))
    waited=0
    $echo "${INFO}Wait for agent catch up on chain${NC}"
    while [ $diff -ne 0 ] || [ $seen_block -eq 0 ]; do
        current_block=$(bw2 status  | sed -n -e 's/Current block: \(.*\).*/\1/p' | xargs)
        seen_block=$(bw2 status  | sed -n -e 's/Seen block: \(.*\).*/\1/p' | xargs)
        if [ $seen_block -ne 0 ]; then
            diff=$(($seen_block - $current_block))
            pct=$(bc <<< "scale=2; 100*$current_block/$seen_block")
            human_waited=$(date -u -d @${waited} +"%T")
            printf "\r$current_block/$seen_block ($pct%% done). Waited $human_waited so far..."
        else
            printf "\rWaiting for peers to send blocks..."
        fi
        sleep 1
        waited=$(($waited + 1))
    done
    $echo "${OK}Installed BOSSWAVE${NC}"

    if $CONFIGURE_NAMESPACE ; then
        # configure BW2_AGENT
        $echo "${INFO}Rewriting BW2_AGENT to 172.17.0.1:28589 for docker${NC}"
        $sh_c "sed -i -e 's/ListenOn=127.0.0.1:28589/ListenOn=172.17.0.1:28589/' /etc/bw2/bw2.ini"
        export BW2_AGENT="172.17.0.1:28589"
        $echo "${INFO}restarting...${NC}"
        $sh_c "$reload_bw2"
        sleep 10
    else
        export BW2_AGENT="127.0.0.1:28589"
    fi
    $echo "${OK}Reconfigured BOSSWAVE${NC}"

    # configure BW2_DEFAULT_ENTITY
    bw2 inspect $BW2_DEFAULT_ENTITY > /dev/null 2>&1
    if [ -z "$BW2_DEFAULT_ENTITY" ] || [ $? -ne 0 ]; then
        if [ ! -f defaultentity.ent ]; then
            $echo "${INFO}Could not find BW2_DEFAULT_ENTITY. Creating defaultentity.ent${NC}"
            bw2 mke -o defaultentity.ent -e 100y -m "Administrative key" -n
            # sleep_til_valid defaultentity.ent
        fi
        export BW2_DEFAULT_ENTITY="$(pwd)/defaultentity.ent"
    fi

    bw2 inspect $BW2_DEFAULT_BANKROLL > /dev/null 2>&1
    if [ -z "$BW2_DEFAULT_BANKROLL" ] || [ $? -ne 0 ]; then
        $echo "${INFO}Could not find BW2_DEFAULT_BANKROLL. Setting it to ${BW2_DEFAULT_ENTITY} ${NC}"
        export BW2_DEFAULT_BANKROLL="$BW2_DEFAULT_ENTITY"
    fi

    # get the monEH
    address=$(bw2 i $BW2_DEFAULT_BANKROLL | sed -n 's/.* 0 (\(0x.*\)) .*/\1/p')
    funds=$(bw2 i $BW2_DEFAULT_BANKROLL | sed -n 's/.* 0 (0x.*) \([0-9]*\).* .*/\1/p')
    if [[ "$funds" -lt 500 ]] ; then
        $echo "${INFO}You only have $funds Ξ, but we recommend 500 Ξ. ${NC}"
        $echo "${INFO}Ask someone to send $((500 - $funds)) Ξ to address $address . We'll wait${NC}"
		confirmY "${PROMPT}Do you have the funds? If you don't, we will try our best, but some commands may fail. Continue? [Y/n]${NC}"
        if [ $? -ne 0 ]; then exit ;fi
    fi

    # publish default entity
    bw2 i $BW2_DEFAULT_ENTITY -p
    $echo "${OK}Now have \$BW2_DEFAULT_ENTITY, \$BW2_DEFAULT_BANKROLL${NC}"

    if $CONFIGURE_NAMESPACE ; then
        $echo "${INFO}Setting up namespace${NC}"
        # setup namespace entity

        # copy over existing entity if configured
        if [ ! -z "$NAMESPACE_ENTITY" ]; then
            $sh_c "cp $NAMESPACE_ENTITY namespace.ent"
        fi

        # setup entity if it doesn't exist
        if [ ! -f "namespace.ent" ]; then
            $echo "${INFO}Creating a namespace entity${NC}"
            bw2 mke -o namespace.ent -e 100y -m "Namespace entity"
            sleep_til_valid namespace.ent
        fi

        set -e
        nsvk=$(bw2 i namespace.ent | sed -n 's/.*Entity VK: \(.*\).*/\1/p')

        # setup alias if its null
        if [ -z "$NAMESPACE_ALIAS" ] && [ ! -z "$nsvk" ] ; then
            $echo "${INFO}Creating namespace alias${NC}"
            bw2 mkalias --long "$NAMESPACE_ALIAS" --b64 "$nsvk"
        else
            export NAMESPACE_ALIAS=$(bw2 i namespace.ent | sed -n 's/.*Alias: \(.*\).*/\1/p')
            if [ -z "$NAMESPACE_ALIAS" ]; then
                $echo "${ERROR}No alias configured, using VK ${NC}"
                export NAMESPACE_ALIAS=$nsvk
            fi
            $echo "${OK}Already have alias $NAMESPACE_ALIAS${NC}"
        fi
        set +e

        # confirm admin privileges on namespace for defaultentity.ent
        bw2 bc -u "$NAMESPACE_ALIAS/*"
        if [ $? -ne 0 ]; then
            $echo "${INFO}Make DOT on $NAMESPACE_ALIAS/*${NC}"
            set -e
            bw2 mkdot -f namespace.ent -t $BW2_DEFAULT_ENTITY -u "$NAMESPACE_ALIAS/*" -m "Admin access to $NAMESPACE_ALIAS" --ttl 10
            set +e
        fi

        # setup designated router
        if [ ! -z "$DESIGNATED_ROUTER_VK" ]; then
            $echo "${INFO}Now we need to set up the designated router (DR) for this namespace. Ask someone who runs a DR to run the following:${NC}"
            $echo "${INFO}bw2 mkdroffer --dr /etc/bw2/router.ent --ns $NAMESPACE_ALIAS${NC}"
            #$echo "${INFO}Now type in the VK of the DR router entity (obtained by bw2 lsdro --ns $NAMESPACE_ALIAS, or by asking)${NC}"
            $echo "${INFO}Waiting...${NC}"
            bw2 adro --dr $DESIGNATED_ROUTER_VK --ns namespace.ent
            while [ $? -ne 0 ]; do
                sleep 30
                bw2 adro --dr $DESIGNATED_ROUTER_VK --ns namespace.ent
            done
        fi
        $echo "${GO}Namespace configured${NC}"
    fi

    # install go
    if $INSTALL_GO ; then
        $echo "${YELLOW}Installing Go${NC}"
        $sh_c "curl -O https://storage.googleapis.com/golang/go1.9.linux-amd64.tar.gz"
        $sh_c "tar -C /usr/local -xzvf go1.9.linux-amd64.tar.gz"
        export PATH=/usr/local/go/bin:$PATH
        $echo "${OK}Installed go${NC}"
    fi

    if $INSTALL_SPAWNPOINT_SERVER ; then
        # create spawnpoint entity
        $echo "${YELLOW}Installing spawnpoint${NC}"

        # copy spawnd entity over if configured
        if [ ! -z "$SPAWND_ENTITY" ]; then
            $sh_c "cp $SPAWND_ENTITY spawnpoint.ent"
        fi

        # or create it if it doesn't exist
        if [ ! -f spawnpoint.ent ]; then
            set -e
            $echo "${INFO}Could not find spawnpoint.ent. Creating...${NC}"
            bw2 mke -o spawnpoint.ent -e 100y -m "Spawnpoint entity"
            sleep_til_valid spawnpoint.ent
            $echo "${INFO}Updating permissions for spawnpoint.ent${NC}"
            bw2 mkdot -f namespace.ent -t spawnpoint.ent -u "$NAMESPACE_ALIAS/sp/*" -m "Spawnpoint access"
            set +e
        fi

        # install spawnpoint server
        export SPAWND_INSTALLER_ENTITY=spawnpoint.ent
        export SPAWND_INSTALLER_PATH="$NAMESPACE_ALIAS/sp"
        export SPAWND_INSTALLER_MEM_ALLOC="$SPAWND_MEM_ALLOC"
        export SPAWND_INSTALLER_CPU_SHARES="$SPAWND_CPU_SHARES"
        $sh_c $(curl get.bw2.io/spawnpoint | bash)
    fi

    if $INSTALL_SPAWNPOINT_CLIENT ; then
        $echo "${YELLOW} we would install spawnctl here ${NC}"
    fi

    if $INSTALL_PUNDAT_CLIENT ; then
        $echo "${YELLOW} we would install pundat here ${NC}"
    fi


	$echo "${OK}XBOS installed successfully${NC}"

    $echo "${OK}Add the following to your .bashrc or .bash_profile${NC}"
    echo "export BW2_AGENT=\"$BW2_AGENT\""
    echo "export BW2_DEFAULT_ENTITY=\"$BW2_DEFAULT_ENTITY\""
    echo "export BW2_DEFAULT_BANKROLL=\"$BW2_DEFAULT_BANKROLL\""
    echo "export BW2_DEFAULT_EXPIRY=\"50y\""
    echo "export BW2_DEFAULT_CONTACT=\"$contact\""
    echo "export PATH=\"$PATH\""
	exit 0
}

do_install
