APP=xbos/microsvc_occupancy
PORT=5066
build:
	docker build -t $(APP) .
push: build
	docker push xbos/microsvc_occupancy:latest
