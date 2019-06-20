FROM xbos/microsvc_base:latest
WORKDIR /app

ADD req.txt /app/
RUN pip install -r req.txt

COPY . /app

CMD ["python", "server.py"]
