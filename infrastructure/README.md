# XBOS Service Architecture

<img src="XBOSservices.png"></img>

## Core Infrastructure

These services *can* be run on a local node, but we recommend to run these on a more capable server or cluster.

### BTrDB

We currently only support [BTrDB](http://btrdb.io/) as our timeseries storage backend.
There are instructions for a single-machine development setup [here](https://docs.smartgrid.store/development-environment.html), but for a production installation we recommend the [full installation](https://docs.smartgrid.store/).

### Pundat

[Pundat](https://github.com/gtfierro/pundat) subscribes to data published over BOSSWAVE and saves it in BTrDB.
Pundat should be run on the same cluster or node as your BTrDB installation.


#### Run with Kubernetes

If you are running Kubernetes on your node/cluster, then you can easily install Pundat by using its Kubernetes file

```bash
curl -O https://github.com/gtfierro/pundat/blob/master/kubernetes/pundat.yaml
# edit pundat.yaml
kubectl create -f pundat.yaml
```

#### Run with Docker

If you are not running Kubernetes, you can invoke the Pundat container directly

```bash
# install jq:  https://stedolan.github.io/jq/
docker run -d --name pundat-mongo mongo:latest
MONGOIP=$(docker inspect pundat-mongo | jq .[0].NetworkSettings.Networks.bridge.IPAddress | tr -d '"')
docker run -d --name pundat -e BTRDB_SERVER=<btrdb ip>:4410 \
                            -e MONGO_SERVER=$MONGOIP:27017 \
                            -e GILES_BW_ENTITY=/etc/pundat/<archiver entity.ent> \
                            -e GILES_BW_NAMESPACE=<namespace to deploy on> \
                            -e GILES_BW_ADDRESS=172.17.0.1:28589 \
                            -e GILES_BW_LSTEN="space-separated list of namespaces to listen on" \
                            -e COLLECTION_PREFIX="pundat_" \
                            -v <host config directory>:/etc/pundat \
                            gtfierro/pundat:latest
```


### HodDB

### MDAL

MDAL is shipped as a Docker container image `gtfierro/mdal:latest` (most recent version is `gtfierro/mdal:0.0.2`.
You can build this container yourself by running `make container` in a cloned copy of the [MDAL repository](https://github.com/gtfierro/mdal).

### Run with Kubernetes

If you are running Kubernetes on your node/cluster, then you can easily install Pundat by using its Kubernetes file.

Keep in mind that MDAL currently requires a volume mount where the `mdal.yaml` configuration file is stored.
```yaml
# snippet of MDAL kubernetes file
...
    spec:
        containers:
            - name: mdal
              image:  gtfierro/mdal:0.0.2
              imagePullPolicy: Always
              volumeMounts:
                - name: mdal
                  mountPath: /etc/mdal  # <-- this is how your host folder gets mounted in the container.
        volumes:
            - name: mdal
              hostPath:
                path: /etc/mdal   # <-- create this host folder and place the mdal.yaml config file there
```

To execute MDAL as a Kubernetes service, use the following:

```bash
curl -O https://github.com/gtfierro/mdal/blob/master/kubernetes/k8mdal.yaml
# edit /etc/mdal/mdal.yaml and k8mdal.yaml appropriately
kubectl create -f k8mdal.yaml
```


### Run with Docker

If you are not running Kubernetes, you can invoke the MDAL container directly

```bash
docker run -d --name mdal -v /etc/mdal:/etc/mdal gtfierro/mdal:latest
```

Don't forget to forward the HTTP port if that interface is enabled

