#!/bin/bash

# This is the install script for the virtual building drivers

if [ $(whoami) != "root" ]
then
	echo "You need to curl this script into 'sudo bash' not just 'bash'"
	exit 1
fi

curl http://install.openbas.cal-sdb.org/vbuilding.ini > /etc/smap/vbuilding.ini

cat <<EOF > vbuilding.conf
[program:vbuilding]
command = /usr/bin/twistd --pidfile=/var/run/smap/vbuilding.pid -n smap /etc/smap/vbuilding.ini
priority = 2
autorestart = true
user = smap
stdout_logfile = /var/log/vbuilding.stdout.log
stdout_logfile_maxbytes = 50MB
stdout_logfile_backups = 5
stderr_logfile = /var/log/vbuilding.stderr.log
stderr_logfile_maxbytes = 50MB
stderr_logfile_backups = 5
EOF

mv vbuilding.conf /etc/supervisor/conf.d/

supervisorctl update
