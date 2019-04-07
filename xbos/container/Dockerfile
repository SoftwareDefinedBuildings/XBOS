FROM ubuntu:xenial
MAINTAINER Gabe Fierro <gtfierro@eecs.berkeley.edu>

RUN apt-get update && apt-get install -y software-properties-common wget curl git
ENV GOVERSION 1.8
ENV GOROOT /opt/go
ENV GOPATH /root/.go

RUN cd /opt && wget https://storage.googleapis.com/golang/go${GOVERSION}.linux-amd64.tar.gz && \
        tar zxf go${GOVERSION}.linux-amd64.tar.gz && rm go${GOVERSION}.linux-amd64.tar.gz && \
        ln -s /opt/go/bin/go /usr/bin/ && \
        mkdir $GOPATH

ADD xbos /xbos

ENTRYPOINT /bin/bash
