#!/bin/sh

# This is the install script for OpenBAS

set -e
set -u

# display on stderr
#exec 1>&2

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

sudo apt-get install -y expect

echo "Adding cal-sdb package repository..."
sudo add-apt-repository ppa:cal-sdb/smap

echo "Updating to receive packages from cal-sdb..."
sudo apt-get update

echo "Installing npm..."
sudo apt-get install -y npm

echo "Installing sMAP and sMAP dependencies..."
sudo apt-get install -y python-smap readingdb

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

curl -O http://54.183.169.17/openbas.tgz
tar xzf openbas.tgz

#echo "Installing Meteor..."
#curl https://install.meteor.com | sh
#
#echo "Adding Meteor's Node to PATH..."
#export PATH=~/.meteor/tools/latest/bin:$PATH
#
#echo "Installing meteorite..."
#sudo -H npm install -g meteorite
