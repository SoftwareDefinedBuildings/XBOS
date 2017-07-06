#!/bin/bash

set -x

cd .. ; go build -o xbos ; cd -
cp ../xbos .
docker build --rm -t gtfierro/xbosclitest .
