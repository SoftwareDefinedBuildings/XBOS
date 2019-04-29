#!/bin/sh

# Change if needed
SERVICE="price"
SERVICES_PATH="/home/dlengyel/xbos-services"

export export XBOS_SERVICES_UTILS2_DATA_PATH="$SERVICES_PATH/data/utils"
export PRICE_HOST_ADDRESS="localhost:50063"

# Do not change
$SERVICES_PATH/deployment/$SERVICE/.venv/bin/python $SERVICES_PATH/src/$SERVICE/test/test.py
