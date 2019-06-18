APP=xbos/microsvc_meter_data_historical
PORT=5066
build:
	docker build -t $(APP) .
push: build
	docker push xbos/microsvc_meter_data_historical:latest
