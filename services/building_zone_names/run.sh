#!/bin/bash

docker run -it --rm -e BUILDING_ZONE_NAMES_DATA_PATH=. -e BUILDING_ZONE_NAMES_HOST_ADDRESS="50066" building_zone_names
