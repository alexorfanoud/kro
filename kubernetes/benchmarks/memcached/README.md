# To build
```
# For client and rps calculator
DOCKER_REPO=aorfanou
CLIENT_IMAGE=$DOCKER_REPO/cloudsuite-data-caching-client
CLIENT_TAG=latest
sudo docker build -t $CLIENT_IMAGE:$CLIENT_TAG ../../../docker/benchmarks/memcached/client
docker push $CLIENT_IMAGE:$CLIENT_TAG
```
