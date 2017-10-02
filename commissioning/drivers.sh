#!/bin/bash

DIALOG_CANCEL=1
DIALOG_ESC=255
HEIGHT=0
WIDTH=0

list_drivers() {
    return $(ls bw2-contrib/driver)
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
        if [ ! -f "bw2-contrib" ]; then
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
        drivernospaces=$(echo $drivername | sed 's/ /_/g')
        mkdir -p $drivernospaces
        params_file=$drivernospaces/params.yml
        archive_file=$drivernospaces/archive.yml
        deploy_file=$drivernospaces/deploy.yml
        entity_file=$drivernospaces/entity.ent

        confirmY "Edit config file? [Y/n] "
        if [ $? -eq 0 ]; then 
            cp bw2-contrib/driver/$driver/params.yml $params_file
            $EDITOR $params_file
        fi
        baseuri=$(cat $drivernospaces/params.yml | sed -ne 's/svc_base_uri:\(.*\)/\1/p' | xargs)
        echo "Base URI for driver: $baseuri"

        if [ ! -f "$entity_file" ]; then
            confirmY "Do you already have an entity for this driver? [Y/n] "
            if [ $? -eq 0 ]; then
                read -r -p "Driver entity path: " entitypath
                cp $entitypath $drivernospaces/entity.ent
            else
                bw2 mke -o $entity_file -m "Driver entity for ${drivername}"
                sleep_til_valid $entity_file
            fi
        fi

        # build chain for driver
        bw2 bc -t $drivernospaces/entity.ent -u "$baseuri"
        haschain=$?
        echo "has chain?", $haschain

        confirmY "Configure deployment? [Y/n] "
        if [ $? -eq 0 ]; then 
            cp bw2-contrib/driver/$driver/deploy.yml $drivernospaces/.
            $EDITOR $drivernospaces/deploy.yml
        fi

        confirmY "Configure archival? [Y/n] "
        if [ $? -eq 0 ]; then 
            cp bw2-contrib/driver/$driver/archive.yml $drivernospaces/.
            $EDITOR $drivernospaces/archive.yml
        fi


        ;;
esac
