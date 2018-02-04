#!/bin/bash

DIALOG_CANCEL=1
DIALOG_ESC=255
HEIGHT=0
WIDTH=0

list_drivers() {
    return $(ls bw2-contrib/driver)
}

check_variables() {
    if [ -z "$BW2_DEFAULT_CONTACT" ]; then
        echo "You need to provide a default contact \$BW2_DEFAULT_CONTACT "
        exit 1
    fi

    if [ -z "$BW2_NAMESPACE" ]; then
        echo "You need to provide a namespace \$BW2_NAMESPACE "
        exit 1
    fi

    if [ -z "$BW2_DEFAULT_ENTITY" ]; then
        echo "You need to provide a namespace \$BW2_DEFAULT_ENTITY "
        exit 1
    fi

    if [ -z "$BW2_DEFAULT_BANKROLL" ]; then
        echo "You need to provide a namespace \$BW2_DEFAULT_BANKROLL "
        exit 1
    fi

    if [ -z "$EDITOR" ]; then
        echo "You need to provide an editor \$EDITOR "
        exit 1
    fi
}


sleep_til_valid() {
    echo -e "${INFO}Waiting until ${1} is valid${NC}..."
    valid=$(bw2 i ${1} | sed -n 's/.*Registry: \(.*\).*/\1/p')
    while [ "$valid" != "valid" ]; do
        sleep 5
        valid=$(bw2 i ${1} | sed -n 's/.*Registry: \(.*\).*/\1/p')
    done
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

command_exists() {
    command -v "$@" > /dev/null 2>&1
}

install_dependencies() {
    # install dependencies
    echo "${INFO}Updating apt repos and installing dependencies${NC}"

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
    $sh_c 'apt-get update >/dev/null'
    $sh_c 'apt-get install -y git dialog'
}

install_dependencies
check_variables

exec 3>&1
selection=$(dialog \
    --backtitle "XBOS Driver Management" \
    --title "Driver Manaagement" \
    --clear \
    --cancel-label "Exit" \
    --menu "Please select:" $HEIGHT $WIDTH 2 \
    "1" "Configure a new driver" \
    "2" "Configure an existing driver" \
    2>&1 1>&3)
exit_status=$?
exec 3>&-
case $exit_status in
    $DIALOG_CANCEL)
        clear
        exit
        ;;
    $DIALOG_ESC)
        clear
        exit 1
        ;;
esac
case $selection in
    0 )
        clear
        exit
        ;;
    1 )
        echo "Configure"

        # get the driver repo
        if [ ! -d "bw2-contrib" ]; then
            git clone https://github.com/SoftwareDefinedBuildings/bw2-contrib
        else
            cd bw2-contrib; git pull; cd -
        fi

        declare -a drivers
        declare -a driverindexes
        index=0
        for file in $(ls bw2-contrib/driver); do
            drivers=("${drivers[@]}" "$file")
            driverindexes+="$index $file "
            index=$((index + 1))
        done
        exec 3>&1
        selection=$(dialog \
        --backtitle "Driver" \
        --title "Choose a driver to instantiate" \
        --clear \
        --cancel-label "Exit" \
        --menu "Please select:" $HEIGHT $WIDTH $index ${driverindexes[@]} \
        2>&1 1>&3)
        exit_status=$?
        exec 3>&-
        driver=${drivers[$selection]}

        # create that driver!

        echo "Create params file and edit"

        read -r -p "Driver name: " drivername
        foldername=$(echo $drivername | sed 's/ /_/g')
        params_file=$foldername/params.yml
        archive_file=$foldername/archive.yml
        deploy_file=$foldername/deploy.yml
        entity_file=$foldername/entity.ent

        if [ -d "$foldername" ]; then
            echo "Config folder $foldername already exists"
        else
            mkdir -p $foldername
        fi

        confirmY "Edit config file? [Y/n] "
        if [ $? -eq 0 ]; then 
            if [ ! -f "$params_file" ]; then
                cp bw2-contrib/driver/$driver/params.yml $params_file
            fi
            $EDITOR $params_file
        fi
        baseuri=$(cat $foldername/params.yml | sed -ne 's/svc_base_uri:\(.*\)/\1/p' | xargs)
        echo "Base URI for driver: $baseuri"

        if [ ! -f "$entity_file" ]; then
            confirmN "Do you already have an entity for this driver? [y/N] "
            if [ $? -eq 0 ]; then
                read -r -p "Driver entity path: " entitypath
                cp $entitypath $entity_file
            else
                bw2 mke -o $entity_file -m "Driver entity for ${drivername}"
                sleep_til_valid $entity_file
            fi
        fi

        # build chain for driver
        bw2 bc -t $entity_file -u "$baseuri/*"
        haschain=$?
        if [ "$haschain" -ne 0 ]; then
            # make DoT using default entity
            bw2 mkdot -t $entity_file -u "$baseuri/*" -m "${drivername} operation"
        fi

        confirmY "Configure deployment? [Y/n] "
        if [ $? -eq 0 ]; then 
            if [ ! -f "$deploy_file" ]; then
                cp bw2-contrib/driver/$driver/deploy.yml $deploy_file
            fi
            $EDITOR $deploy_file
        fi

        confirmY "Configure archival? [Y/n] "
        if [ $? -eq 0 ]; then 
            if [ ! -f "$archive_file" ]; then
                cp bw2-contrib/driver/$driver/archive.yml $archive_file
            fi
            $EDITOR $archive_file
        fi

        # get spawnpoint url
        spawnpoint_url=$(spawnctl scan $BW2_NAMESPACE | sed -ne "s/.* ago at \(.*\)\$/\1/p")
        if [ -z "$spawnpoint_url" ];then
            echo "No spawnpoint deployed at $BW2_NAMESPACE"
            exit 1
        fi

        confirmY "Deploy? [Y/n] "
        if [ $? -eq 0 ]; then
            cd $foldername
            pundat addreq -c $(basename $archive_file)
            spawnctl deploy -c $(basename $deploy_file) -n $foldername -u $spawnpoint_url
        fi

        ;;
esac
