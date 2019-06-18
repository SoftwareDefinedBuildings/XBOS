APP=xbos/microsvc_temperature_bands
PORT=5066
build:
	docker build -t $(APP) .
push: build
	docker push xbos/microsvc_temperature_bands:latest
