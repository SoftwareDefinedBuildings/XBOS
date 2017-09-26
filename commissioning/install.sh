#!/bin/bash

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

    echo "If you want this to go faster, pre-install BOSSWAVE (curl get.bw2.io/agent | bash)"

    confirmY "Are you setting up a namespace? [Y/n]"
    doingNS=$?
    if [ $doingNS -eq 0 ]; then
        confirmN "Do you have a namespace entity already? [y/N]"
        if [ $? -eq 0 ]; then
            read -p "Path to entity file: " nspath
            echo "Copying to this directory"
            cp $nspath namespace.ent
        fi
        confirmY "Do you want to set up an alias? [Y/n]"
        setupAlias=$?
        if [ $setupAlias -eq 0 ]; then
            read -p "Namespace alias: " alias
        fi
    fi
    read -p "Contact (full name <email>): " contact


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
			Error: this installer needs the ability to run commands as root.
			We are unable to find either "sudo" or "su" available to make this happen.
			EOF
			exit 1
		fi
	fi

    # install dependencies
    echo "Updating apt repos and installing dependencies"

    $sh_c 'apt-get update >/dev/null'
    $sh_c 'apt-get install -y git python2.7 python-pip python-dev curl bc'

    # trick to get directory of executing script, and move there
    dot="$(cd "$(dirname "$0")"; pwd)"
    cd $dot


    # set up local git repository
    git init

    # check if bosswave is installed, but update it either way
    if command_exists bw2; then
        echo "Bosswave already installed! Updating..."
    else
        echo "Installing Bosswave"
    fi

    $sh_c $(curl get.bw2.io/agent | bash)
    sleep 10
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
        echo "Rewriting BW2_AGENT to 172.17.0.1:28589 for docker"
        $sh_c "sed -i -e 's/ListenOn=127.0.0.1:28589/ListenOn=172.17.0.1:28589/' /etc/bw2/bw2.ini"
        export BW2_AGENT="172.17.0.1:28589"
        echo "restarting..."
        $sh_c systemctl daemon-reload -q --no-pager > /dev/null 2>&1
        $sh_c systemctl restart -q --no-pager bw2.service > /dev/null 2>&1
        sleep 10
    else
        export BW2_AGENT="127.0.0.1:28589"
    fi

    # configure BW2_DEFAULT_ENTITY
    echo $BW2_AGENT
    bw2 inspect $BW2_DEFAULT_ENTITY 
    if [ -z "$BW2_DEFAULT_ENTITY" ] || [ $? -ne 0 ]; then
        echo "Could not find BW2_DEFAULT_ENTITY. Creating defaultentity.ent"
        bw2 mke -o defaultentity.ent -e 100y -m "Administrative key" -c $contact -n
        export BW2_DEFAULT_ENTITY="$(pwd)/defaultentity.ent"
    fi

    bw2 inspect $BW2_DEFAULT_BANKROLL 
    if [ -z "$BW2_DEFAULT_BANKROLL" ] || [ $? -ne 0 ]; then
        echo "Could not fine BW2_DEFAULT_BANKROLL. Setting it to defaultentity.ent"
        export BW2_DEFAULT_ENTITY="$(pwd)/defaultentity.ent"
    fi

    # get the monEH
    address=$(bw2 i $BW2_DEFAULT_BANKROLL | sed -n 's/.* 0 (\(0x.*\)) .*/\1/p')
    funds=$(bw2 i $BW2_DEFAULT_BANKROLL | sed -n 's/.* 0 (0x.*) \([0-9]*\).* .*/\1/p')
    if [[ "$funds" -lt 500 ]] ; then
        echo "You only have $funds Ξ, but we recommend 500 Ξ. Ask someone to send $((500 - $funds)) Ξ to address $address. We'll wait"
		confirmY "Do you have the funds? If you don't, we will try our best, but some commands may fail. Continue? [Y/n]"
        if [ $? -eq 0 ]; then exit ;fi
    fi

    # publish default entity
    bw2 i $BW2_DEFAULT_ENTITY -p

    if [ $doingNS -eq 0 ]; then
        # setup namespace entity
        if [ ! -f "namespace.ent" ]; then
            if [ $? -ne 0 ]; then
                echo "Creating a namespace entity"
                bw2 mke -o namespace.ent -e 100y -m "Namespace entity" -c $contact
            fi
        fi

        set -e
        nsvk=$(bw2 i namespace.ent | sed -n 's/.*Entity VK: \(.*\).*/\1/p')
        #alias=$(bw2 i namespace.ent | sed -n 's/.*Alias: \(.*\).*/\1/p')

        if [ $setupAlias -eq 0 ] && [ ! -z "$nsvk" ] ; then 
        #    # setup an alias
            echo "Creating namespace alias"
            bw2 mkalias --long "$alias" --b64 "$nsvk"
        else
            echo "Already have alias $alias"
        fi
        set +e

        # confirm admin privileges on namespace for defaultentity.ent
        bw2 bc -u "$alias/*"
        if [ $? -ne 0 ]; then
            echo "Make DOT on $alias/*"
            set -e
            bw2 mkdot -f namespace.ent -t $BW2_DEFAULT_ENTITY -u "$alias/*" -m "Admin access to $alias" --ttl 10 -c $contact
            set +e
        fi

        # setup designated router
        set -e
        echo "Now we need to set up the designated router (DR) for this namespace. Ask someone who runs a DR to run the following:"
        echo "bw2 mkdroffer --dr /etc/bw2/router.ent --ns $alias"
        echo "Now type in the VK of the DR router entity (obtained by bw2 lsdro --ns $alias, or by asking)"
        routervk=""
        while [ -z "$routervk"]; do
            read -p "vk: " routervk
        done
        bw2 adro --dr $routervk --ns namespace.ent
        set +e
    fi

	echo "XBOS installed successfully"
	exit 0
}

do_install
