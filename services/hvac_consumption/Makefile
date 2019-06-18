APP=xbos/microsvc_hvac_consumption
PORT=5066
build:
	docker build -t $(APP) .
push: build
	docker push xbos/microsvc_hvac_consumption:latest
