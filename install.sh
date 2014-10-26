#!/bin/bash

# This is the install script for OpenBAS

if [ $(whoami) != "root" ]
then
	echo "You need to curl this script into 'sudo bash' not just 'bash'"
	exit 1
fi

export DEBIAN_FRONTEND=noninteractive

function notify() {
	msg=$1
	length=$((${#msg}+4))
	buf=$(printf "%-${length}s" "#")
	echo ${buf// /#}
	echo "# "$msg" #"
	echo ${buf// /#}
	sleep 2
}

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
apt-get update
apt-get install -y expect software-properties-common python-pip mongodb npm libssl-dev git-core pkg-config build-essential nmap dhcpdump arp-scan 2>&1 > /tmp/install.0.log

if [ $? != 0 ] ; then
	echo "There was an unexpected error installing the first set of packages"
	exit 1
fi

notify "Installing Meteor..."
curl https://install.meteor.com | sh
if [ $? != 0 ] ; then
	echo "There was an error installing meteor"
	exit 1
fi
echo "export PATH=~/.meteor/tools/latest/bin:\$PATH" >> ~/.profile
export PATH=~/.meteor/tools/latest/bin:$PATH
npm install -g meteorite

notify "Fetching latest node..."
curl -sL https://deb.nodesource.com/setup | sudo bash -
if [ $? != 0 ]; then
	echo "There was an error installing node"
	exit 1
fi
apt-get install -y nodejs nodejs-legacy 2>&1 > /tmp/install.1.log
if [ $? != 0 ]; then
	echo ""
fi

notify "Adding cal-sdb package repository..."
add-apt-repository ppa:cal-sdb/smap
if [ $? != 0 ] ; then
	echo "There was an error adding the repository"
	exit 1
fi

notify "Updating APT for latest packages..."
apt-get update
if [ $? != 0 ] ; then
	echo "There was an error updating the package index"
	exit 1
fi

notify "Installing sMAP and sMAP dependencies... (this will take a few minutes)"
apt-get install -y python-smap readingdb 2>&1 > /tmp/install.2.log
if [ $? != 0 ] ; then
	echo "There was an error installing smap packages"
	exit 1
fi
pip install pymongo netifaces
if [ $? != 0 ] ; then
	echo "There was an error updating installing python packages"
	exit 1
fi
mkdir -p /var/run/smap
mkdir /var/smap
chown -R $SUDO_USER /var/smap
chown -R smap /var/run/smap

notify "Downloading OpenBAS..."
curl -O http://install.openbas.cal-sdb.org/openbas.tgz
tar xzf openbas.tgz

cat <<EOF > openbas.conf
[program:openbas]
command = meteor --settings settings.json
user = $SUDO_USER
directory = /home/$SUDO_USER/openbas
priority = 2
environment = HOME = "/home/$SUDO_USER"
autorestart = true
stdout_logfile = /var/log/openbas.stdout.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile = /var/log/openbas.stderr.log
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

mv openbas.conf /etc/supervisor/conf.d/openbas.conf

cat <<EOF > discovery.ini
[/]
uuid = 85d97cac-9345-11e3-898b-0001c009bf3f

[/discovery]
type = smap.services.discovery.DiscoveryDriver
dhcp_iface = eth0
supervisord_conf_file = supervisord.conf
dhcpdump_path = /usr/sbin/dhcpdump
nmap_path = /usr/bin/nmap
config_repo = /etc/smap
scripts_path = /usr/lib/python2.7/dist-packages/smap/services/scripts
EOF

mv discovery.ini /etc/smap/.

cat <<EOF > discovery.conf
[program:discovery]
command = twistd --pidfile=discovery.pid -n smap --port=7979 /etc/smap/discovery.ini
directory = /var/smap
environment=PYTHONPATH="/home/$SUDO_USER/smap"
priority = 2
autorestart = true
user = root
stdout_logfile = /var/log/discovery.stdout.log
stderr_logfile = /var/log/discovery.stderr.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

mv discovery.conf /etc/supervisor/conf.d/discovery.conf

cat <<EOF > scheduler.ini
[/]
uuid = 6d39e9ba-28b3-11e4-a7d9-e4ce8f4229ee 

[report 1]
ReportDeliveryLocation = http://localhost:8079/add/lVzBMDpnkXApJmpjUDSvm4ceGfpbrLLSd9cq

[server]
port = 8080

[/scheduler]
type = smap.services.scheduler.Scheduler
pollrate = 1
publishrate = 1
source = mongodb://localhost:3001/meteor
Metadata/Building = Soda Hall
Metadata/Site = 0273d18f-1c03-11e4-a490-6003089ed1d0

[/scheduler/temp_heat]
Metadata/Description = Master Heating setpoint
Metadata/System = HVAC
Metadata/Type = Setpoint

[/scheduler/temp_cool]
Metadata/Description = Master Cooling setpoint
Metadata/System = HVAC
Metadata/Type = Setpoint

[/scheduler/hvac_state]
Metadata/Description = Master HVAC State control
Metadata/System = HVAC
Metadata/Type = Command

[/scheduler/on]
Metadata/Description = Master Lighting control
Metadata/System = Lighting
Metadata/Type = Command
EOF

mv scheduler.ini /etc/smap/.

cat <<EOF > scheduler.conf
[program:scheduler]
command = twistd --pidfile=scheduler.pid -n smap /etc/smap/scheduler.ini
directory = /var/smap
environment=PYTHONPATH="/home/$SUDO_USER/smap"
priority = 2
autorestart = true
user = $SUDO_USER
stdout_logfile = /var/log/scheduler.stdout.log
stderr_logfile = /var/log/scheduler.stderr.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

mv scheduler.conf /etc/supervisor/conf.d/scheduler.conf

cat <<EOF > writeback.ini
[/]
uuid = f8b523d6-5a53-11e4-b74e-0cc47a0f7eea

[server]
port = 7979

[/writeback]
type = smap.services.writeback.WriteBack
archiver = http://localhost:8079
smap_dir = /tmp
rate = 60
EOF

mv writeback.ini /etc/smap/.

cat <<EOF > writeback.conf
[program:writeback]
command = twistd --pidfile=writeback.pid -n smap /etc/smap/writeback.ini
directory = /var/smap
environment=PYTHONPATH="/home/$SUDO_USER/smap"
priority = 2
autorestart = true
user = $SUDO_USER
stdout_logfile = /var/log/writeback.stdout.log
stderr_logfile = /var/log/writeback.stderr.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

mv writeback.conf /etc/supervisor/conf.d/writeback.confg

supervisorctl update

npm install -g spin
chown -R $SUDO_USER .npm
chown -R $SUDO_USER tmp
chown -R $SUDO_USER .meteor
mkdir -p .meteorite
chown -R $SUDO_USER .meteorite
chown -R $SUDO_USER openbas
addgroup smap
adduser $SUDO_USER smap
adduser smap smap
chgrp -R smap /var/smap
chmod g+rwx /var/smap
