FROM jhkolb/spawnpoint:amd64
MAINTAINER Gabe Fierro <gtfierro@eecs.berkeley.edu>

RUN apt-get update
RUN apt-get install -y tar git curl nano wget dialog net-tools build-essential

RUN apt-get install -y python python-dev python-distribute python-pip
ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
ENV BW2_AGENT 172.17.0.1:28589
ENV BW2_DEFAULT_ENTITY /entity.ent
