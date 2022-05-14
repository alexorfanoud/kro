# To build

```
# For client
DOCKER_REPO=<docker_repo>
CLIENT_IMAGE=$DOCKER_REPO/cloudsuite-data-caching-client
CLIENT_TAG=client
sudo docker build -t $CLIENT_IMAGE:$CLIENT_TAG ./client
docker push $CLIENT_IMAGE:$CLIENT_TAG

# For rps calculator
DOCKER_REPO=<docker_repo>
RPS_CALCULATOR_IMAGE=$DOCKER_REPO/cloudsuite-data-caching-rps-calculator
RPS_CALCULATOR_TAG=latest
sudo docker build -t $RPS_CALCULATOR_IMAGE:$RPS_CALCULATOR_TAG ./client_rps_calculator
docker push $RPS_CALCULATOR_IMAGE:$RPS_CALCULATOR_TAG
```

# To run

```
docker-compose up -d
# Once the rps_calculator has determined the maximum rps possible, update the '-r' parameter in the client in the docker-compose file and rerun the command
```

# Possible todos
    * Replace the mean() metric being used to determine the QoS with something more accurate (max of the run, or nth percentile of the run)
    * Integrate prometheus + grafana for the graphs (both for rps_calculator-> rps/qos curve and for the client->qos curve)
