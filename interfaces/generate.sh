#!/bin/bash
pushd genbindings ; go build ; popd
for i in $(ls xbos*.yaml) ; do
    filename=$(basename $i)
    driver=$(echo $filename | sed -e 's/xbos_\(.*\).yaml/\1/')
    genbindings/genbindings $i > ../python/xbos/devices/$driver.py
done
