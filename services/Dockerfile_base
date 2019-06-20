FROM python:3.7-slim-stretch

RUN apt-get update && apt-get install -y \
        && apt install -y python3-dev \
        && rm -rf /var/lib/apt/lists/*
RUN pip install grpcio grpcio-tools numpy pandas PyYAML pytz sklearn matplotlib
  
#COPY . /app
#RUN pip install xbos_services_getter
