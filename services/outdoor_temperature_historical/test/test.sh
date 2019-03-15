#!/bin/sh

# Change if needed
SERVICE="outdoor_temperature_historical"
SERVICES_PATH="/home/dlengyel/xbos-services"

export OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS="0.0.0.0:50065"

export export XBOS_SERVICES_UTILS2_DATA_PATH="$SERVICES_PATH/data/utils"

# Do not change
$SERVICES_PATH/deployment/$SERVICE/.venv/bin/python $SERVICES_PATH/src/$SERVICE/test/test.py
