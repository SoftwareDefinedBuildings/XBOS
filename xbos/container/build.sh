#!/bin/bash

set -x

cd .. ; go build -o xbos ; cd -
cp ../xbos .
docker build -t gtfierro/xbosclitest .
