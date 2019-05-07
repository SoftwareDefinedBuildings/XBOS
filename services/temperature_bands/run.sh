#!/bin/sh
export TEMPERATURE_BANDS_HOST_ADDRESS="localhost:50062"
export TEMPERATURE_BAND_PATH="../../config/band_data"
python server.py
