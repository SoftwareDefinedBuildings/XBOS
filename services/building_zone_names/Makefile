APP=xbos/microsvc_building_zone_names
PORT=5066
build:
	docker build -t $(APP) .
run: build
	docker run -it --rm -e BUILDING_ZONE_NAMES_DATA_PATH=. -e BUILDING_ZONE_NAMES_HOST_ADDRESS=$(PORT) $(APP)
push: build
	docker push xbos/microsvc_building_zone_names:latest
shell: build
	docker run -it --rm -e BUILDING_ZONE_NAMES_DATA_PATH=. -e BUILDING_ZONE_NAMES_HOST_ADDRESS=$(PORT) $(APP) /bin/sh
