FROM ubuntu:xenial
MAINTAINER Gabe Fierro <gtfierro@eecs.berkeley.edu>

RUN apt-get update && apt-get install -y software-properties-common wget curl build-essential

ADD xbos /bin/xbos

ENTRYPOINT /bin/bash
