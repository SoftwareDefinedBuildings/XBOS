#!/bin/sh

# Change if needed
SERVICE="temperature_bands"
SERVICES_PATH="/home/dlengyel/xbos-services"

export export XBOS_SERVICES_UTILS3_DATA_PATH="$SERVICES_PATH/data/utils"
export TEMPERATURE_BANDS_HOST_ADDRESS="localhost:50062"

# Do not change
$SERVICES_PATH/deployment/$SERVICE/.venv/bin/python $SERVICES_PATH/src/$SERVICE/test/test.py
