#!/bin/bash

# This is the install script for OpenBAS

function notify() { 
sleep 1
msg=$1
length=$((${#msg}+4))
buf=$(printf "%-${length}s" "#")
echo ${buf// /#}
echo "  "$msg
echo ${buf// /#}
sleep 2 ;}

# display on stderr
exec 1>&2

UNAME=$(uname)
if [ "$UNAME" != "Linux" ] ; then
    echo "Requires Ubuntu 14.04"
    exit 1
fi

ISUBUNTU=$(lsb_release -is)
UBUNTUVERSION=$(lsb_release -rs)
if [ "$ISUBUNTU" != "Ubuntu" -o "$UBUNTUVERSION" != "14.04" ] ; then
    echo "Requires Ubuntu 14.04"
    exit 1
fi

notify "Installing APT packages..."
`sudo apt-get install -y expect mongodb npm libssl-dev git-core pkg-config build-essential gcc g++`

notify "Adding cal-sdb package repository..."
sudo add-apt-repository ppa:cal-sdb/smap

notify "Updating to receive packages from cal-sdb..."
sudo apt-get update

notify "Installing NVM and latest NodeJS..."
git clone git://github.com/creationix/nvm.git $HOME/nvm
source $HOME/nvm/nvm.sh
latestnode=$(nvm ls-remote | tail -n 1)
nvm install $latestnode
nvm use $latestnode

notify "Installing sMAP and sMAP dependencies..."
`sudo apt-get install -y python-smap readingdb`

expect -c "
spawn sudo apt-get install -y powerdb2
expect {
 'Would you like to create one now' {
    send \"yes\r\"
    expect \"Username\"
    send \"oski\r\"
    expect \"E-mail\"
    send \"\r\"
    expect \"Password\"
    send \"openbas\r\"
    expect \"Password\"
    send \"openbas\r\"
    exp_continue
 }
}
"

notify "Downloading OpenBAS..."
curl -O http://54.183.169.17/openbas.tgz
tar xzf openbas.tgz

sudo mkdir -p /data/mongodb
cat <<EOF >> /etc/supervisor/conf.d/openbas.conf
[program:openbas]
command = /usr/bin/nodejs main.js
directory = /home/oski/bundle
priority = 2
autorestart = true
environment = PORT=3000, MONGO_URL=mongodb://localhost:27017/meteor
stdout_logfile = /var/log/openbas.stdout.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile = /var/log/openbas.stderr.log
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

sudo dpkg --configure -a

