APP=xbos/microsvc_outdoor_temperature_historical
PORT=5066
build:
	docker build -t $(APP) .
push: build
	docker push xbos/microsvc_outdoor_temperature_historical:latest
