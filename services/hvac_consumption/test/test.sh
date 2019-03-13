#!/bin/sh

# Change if needed
SERVICE="hvac_consumption"
SERVICES_PATH="/home/dlengyel/xbos-services"

export export XBOS_SERVICES_UTILS3_DATA_PATH="$SERVICES_PATH/data/utils"
export HVAC_CONSUMPTION_HOST_ADDRESS="localhost:50061"

# Do not change
$SERVICES_PATH/deployment/$SERVICE/.venv/bin/python $SERVICES_PATH/src/$SERVICE/test/test.py
