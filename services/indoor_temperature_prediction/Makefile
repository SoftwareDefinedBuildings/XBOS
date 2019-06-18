APP=xbos/microsvc_indoor_temperature_prediction
PORT=5066
build:
	docker build -t $(APP) .
push: build
	docker push xbos/microsvc_indoor_temperature_prediction:latest
