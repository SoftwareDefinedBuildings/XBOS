#!/bin/bash
set -ex
docker build -t gtfierro/xbospy .
docker push gtfierro/xbospy
