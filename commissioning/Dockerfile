FROM ubuntu:xenial
MAINTAINER Gabe Fierro <gtfierro@eecs.berkeley.edu>

RUN apt-get -y update && apt-get install -y git python2.7 python-pip python-dev curl bc
ADD install.sh /opt

ENTRYPOINT [ "/bin/bash" ]
