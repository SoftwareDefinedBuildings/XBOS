import subprocess
import sys

inis = sys.argv[1:]

processes = []
for ini in inis:
    command = "twistd --pidfile {0}.pid -n smap {0}.ini".format(ini)
    p = subprocess.Popen(command, shell=True)
    processes.append(p)
# run smap query to see if the streams are registered
# This is partly to get around the race condition arising when
# a driver subscribes to the output of another
# However, top handle the mutual dependence case, it really needs to
# restart the services
# Note that this encodes the uri of the archiver
    print subprocess.Popen('smap-query -u http://localhost:8079/api "select uuid"', shell=True, stdout=subprocess.PIPE).stdout.read()
try:
    raw_input()
except:
    for p in processes:
        print "killing",p
        p.terminate()
