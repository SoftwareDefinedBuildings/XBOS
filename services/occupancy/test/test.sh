#!/bin/sh

# Change if needed
SERVICE="occupancy"
SERVICES_PATH="/home/dlengyel/xbos-services"

export export XBOS_SERVICES_UTILS3_DATA_PATH="$SERVICES_PATH/data/utils"
export OCCUPANCY_HOST_ADDRESS="localhost:50064"

# Do not change
$SERVICES_PATH/deployment/$SERVICE/.venv/bin/python $SERVICES_PATH/src/$SERVICE/test/test.py
