# To build parsec image

```
# For client and rps calculator
DOCKER_REPO=aorfanou
CLIENT_IMAGE=$DOCKER_REPO/parsec
CLIENT_TAG=latest
sudo docker build -t $CLIENT_IMAGE:$CLIENT_TAG ../../../docker/stressors/parsec/README.md
docker push $CLIENT_IMAGE:$CLIENT_TAG
```
