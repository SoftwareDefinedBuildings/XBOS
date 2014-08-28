#!/bin/bash

# This is the install script for OpenBAS

export DEBIAN_FRONTEND=noninteractive

function notify() {
msg=$1
length=$((${#msg}+4))
buf=$(printf "%-${length}s" "#")
echo ${buf// /#}
echo "# "$msg" #"
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

notify "Installing APT packages... (this will take a few minutes)"
sudo apt-get install -y expect mongodb npm libssl-dev git-core pkg-config build-essential 2>&1 > /dev/null

notify "Installing Meteor..."
curl https://install.meteor.com | sh
export PATH=~/.meteor/tools/latest/bin:$PATH
sudo npm install -g meteorite

notify "Fetching latest node..."
curl -sL https://deb.nodesource.com/setup | sudo bash -

sudo apt-get install -y nodejs nodejs-legacy 2>&1 > /dev/null

notify "Adding cal-sdb package repository..."
sudo add-apt-repository ppa:cal-sdb/smap

notify "Updating APT for latest packages..."
sudo apt-get update

notify "Installing sMAP and sMAP dependencies... (this will take a few minutes)"
sudo apt-get install -y python-smap readingdb 2>&1 > /dev/null

notify "Downloading OpenBAS..."
curl -O http://install.openbas.cal-sdb.org/openbas.tgz
tar xzf openbas.tgz

cat <<EOF > openbas.conf
[program:openbas]
command = mrt --settings settings.json
user = oski
directory = /home/oski/openbas
priority = 2
autorestart = true
stdout_logfile = /var/log/openbas.stdout.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile = /var/log/openbas.stderr.log
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

sudo mv openbas.conf /etc/supervisor/conf.d/openbas.conf

sudo supervisorctl update

sudo npm install -g spin
sudo chown -R oski .npm
sudo chown -R oski tmp
sudo chown -R oski .meteor
sudo mkdir -p .meteorite
sudo chown -R oski .meteorite
sudo chown -R oski openbas
