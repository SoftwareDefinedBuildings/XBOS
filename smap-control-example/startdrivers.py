import subprocess
import sys

inis = sys.argv[1:]

processes = []
for ini in inis:
    command = "twistd --pidfile {0}.pid -n smap {0}.ini".format(ini)
    p = subprocess.Popen(command, shell=True)
    processes.append(p)

try:
    raw_input()
except:
    for p in processes:
        print "killing",p
        p.terminate()
