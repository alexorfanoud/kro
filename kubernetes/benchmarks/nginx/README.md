# To build
```
DOCKER_REPO=aorfanou
CLIENT_IMAGE=$DOCKER_REPO/cloudsuite-media-streaming-client
CLIENT_TAG=latest
sudo docker build -t $CLIENT_IMAGE:$CLIENT_TAG ../../../docker/benchmarks/nginx/client
docker push $CLIENT_IMAGE:$CLIENT_TAG
```
