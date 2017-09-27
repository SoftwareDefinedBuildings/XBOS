#!/bin/bash

RED='\033[1;31m'
BLUE='\033[1;34m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
INFO=YELLOW
PROMPT=BLUE
ERROR=RED
OK=GREEN
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
    read -r -p "${1:-Are you sure? [Y/n]} " response
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
    read -r -p "${1:-Are you sure? [y/N]} " response
    case "$response" in
        [yY][eE][sS]|[yY])
            true
            ;;
        *)
            false
            ;;
    esac
}


do_install() {
	cat >&2 <<'EOF'
    logo goes here :)
EOF

    echo "Automated installer for XBOS"

    echo "${INFO}If you want this to go faster, pre-install BOSSWAVE (curl get.bw2.io/agent | bash)${NC}"

    confirmY "${PROMPT}Are you setting up a namespace? [Y/n]${NC}"
    doingNS=$?
    if [ $doingNS -eq 0 ]; then
        confirmN "${PROMPT}Do you have a namespace entity already? [y/N]${NC}"
        if [ $? -eq 0 ]; then
            read -p "${PROMPT}Path to entity file: ${NC}" nspath
            echo "${INFO}Copying to this directory${NC}"
            cp $nspath namespace.ent
        fi
        confirmY "${PROMPT}Do you want to set up an alias? [Y/n]${NC}"
        setupAlias=$?
        if [ $setupAlias -eq 0 ]; then
            read -p "${PROMPT}Namespace alias: ${NC}" alias
        fi
    fi
    read -p "${PROMPT}Contact (full name <email>): ${NC}" contact


    # setup $user, $sh_c and $curl like from bosswave
	user="$(id -un 2>/dev/null || true)"

    export SYSTEMD_PAGER=''

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
    echo "${INFO}Updating apt repos and installing dependencies${NC}"

    $sh_c 'apt-get update >/dev/null'
    $sh_c 'apt-get install -y git python2.7 python-pip python-dev curl bc docker.io'

    # trick to get directory of executing script, and move there
    dot="$(cd "$(dirname "$0")"; pwd)"
    cd $dot


    # set up local git repository
    git init

    # check if bosswave is installed, but update it either way
    if command_exists bw2; then
        echo "${INFO}BOSSWAVE already installed! Updating...${NC}"
    else
        echo "${INFO}Installing Bosswave${NC}"
    fi

    $sh_c $(curl get.bw2.io/agent | bash)
    sleep 5
    $sh_c 'systemctl start -q --no-pager bw2 > /dev/null 2>&1'
    echo "${INFO}Wait for agent to restart${NC}"
    sleep 20
    # xargs trick to remove surrounding whitespace
    current_block=$(bw2 status  | sed -n -e 's/Current block: \(.*\).*/\1/p' | xargs)
    seen_block=$(bw2 status  | sed -n -e 's/Seen block: \(.*\).*/\1/p' | xargs)
    diff=$(($seen_block - $current_block))
    waited=0
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

    if [ $doingNS -eq 0 ]; then
        # configure BW2_AGENT
        echo "${INFO}Rewriting BW2_AGENT to 172.17.0.1:28589 for docker${NC}"
        $sh_c "sed -i -e 's/ListenOn=127.0.0.1:28589/ListenOn=172.17.0.1:28589/' /etc/bw2/bw2.ini"
        export BW2_AGENT="172.17.0.1:28589"
        echo "${INFO}restarting...${NC}"
        $sh_c "systemctl daemon-reload -q --no-pager > /dev/null 2>&1"
        $sh_c "systemctl restart -q --no-pager bw2.service > /dev/null 2>&1"
        sleep 10
    else
        export BW2_AGENT="127.0.0.1:28589"
    fi

    # configure BW2_DEFAULT_ENTITY
    echo $BW2_AGENT
    bw2 inspect $BW2_DEFAULT_ENTITY > /dev/null 2>&1
    if [ -z "$BW2_DEFAULT_ENTITY" ] || [ $? -ne 0 ]; then
	if [ ! -f defaultentity.ent ]; then
	    echo "${INFO}Could not find BW2_DEFAULT_ENTITY. Creating defaultentity.ent${NC}"
	    bw2 mke -o defaultentity.ent -e 100y -m "Administrative key" -c "$contact" -n
	fi
        export BW2_DEFAULT_ENTITY="$(pwd)/defaultentity.ent"
    fi

    bw2 inspect $BW2_DEFAULT_BANKROLL > /dev/null 2>&1
    if [ -z "$BW2_DEFAULT_BANKROLL" ] || [ $? -ne 0 ]; then
        echo "${INFO}Could not find BW2_DEFAULT_BANKROLL. Setting it to defaultentity.ent${NC}"
        export BW2_DEFAULT_BANKROLL="$(pwd)/defaultentity.ent"
    fi

    # get the monEH
    address=$(bw2 i $BW2_DEFAULT_BANKROLL | sed -n 's/.* 0 (\(0x.*\)) .*/\1/p')
    funds=$(bw2 i $BW2_DEFAULT_BANKROLL | sed -n 's/.* 0 (0x.*) \([0-9]*\).* .*/\1/p')
    if [[ "$funds" -lt 500 ]] ; then
        echo "${INFO}You only have $funds Ξ, but we recommend 500 Ξ. Ask someone to send $((500 - $funds)) Ξ to address $address. We'll wait${NC}"
		confirmY "${PROMPT}Do you have the funds? If you don't, we will try our best, but some commands may fail. Continue? [Y/n]${NC}"
        if [ $? -ne 0 ]; then exit ;fi
    fi

    # publish default entity
    bw2 i $BW2_DEFAULT_ENTITY -p

    if [ $doingNS -eq 0 ]; then
        # setup namespace entity
        if [ ! -f "namespace.ent" ]; then
            echo "${INFO}Creating a namespace entity${NC}"
            bw2 mke -o namespace.ent -e 100y -m "Namespace entity" -c "$contact"
        fi

        set -e
        nsvk=$(bw2 i namespace.ent | sed -n 's/.*Entity VK: \(.*\).*/\1/p')
        #alias=$(bw2 i namespace.ent | sed -n 's/.*Alias: \(.*\).*/\1/p')

        if [ $setupAlias -eq 0 ] && [ ! -z "$nsvk" ] ; then
        #    # setup an alias
            echo "${INFO}Creating namespace alias${NC}"
            bw2 mkalias --long "$alias" --b64 "$nsvk"
        else
            echo "${OK}Already have alias $alias${NC}"
        fi
        set +e

        # confirm admin privileges on namespace for defaultentity.ent
        bw2 bc -u "$alias/*"
        if [ $? -ne 0 ]; then
            echo "${INFO}Make DOT on $alias/*${NC}"
            set -e
            bw2 mkdot -f namespace.ent -t $BW2_DEFAULT_ENTITY -u "$alias/*" -m "Admin access to $alias" --ttl 10 -c "$contact"
            set +e
        fi

        # setup designated router
        set -e
        echo "${INFO}Now we need to set up the designated router (DR) for this namespace. Ask someone who runs a DR to run the following:${NC}"
        echo "${INFO}bw2 mkdroffer --dr /etc/bw2/router.ent --ns $alias${NC}"
        echo "${INFO}Now type in the VK of the DR router entity (obtained by bw2 lsdro --ns $alias, or by asking)${NC}"
        routervk=""
        while [ -z "$routervk" ]; do
            read -p "vk: " routervk
        done
        bw2 adro --dr $routervk --ns namespace.ent
        set +e
    fi

	echo "${OK}XBOS installed successfully${NC}"
	exit 0
}

do_install
