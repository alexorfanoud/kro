# To build
```
# For client
DOCKER_REPO=aorfanou
CLIENT_IMAGE=$DOCKER_REPO/cloudsuite-data-caching-client
CLIENT_TAG=latest
sudo docker build -t $CLIENT_IMAGE:$CLIENT_TAG ../../../docker/benchmarks/memcached/client
docker push $CLIENT_IMAGE:$CLIENT_TAG

# For rps calculator
DOCKER_REPO=aorfanou
RPS_CALCULATOR_IMAGE=$DOCKER_REPO/cloudsuite-data-caching-rps-calculator
RPS_CALCULATOR_TAG=latest
sudo docker build -t $RPS_CALCULATOR_IMAGE:$RPS_CALCULATOR_TAG ../../../docker/benchmarks/memcached/client_rps_calculator
docker push $RPS_CALCULATOR_IMAGE:$RPS_CALCULATOR_TAG
```
