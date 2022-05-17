## To build
```
DOCKER_REPO=<docker_repo>
MAZES_IMAGE=$DOCKER_REPO/mazes_backend
MAZES_TAG=latest
sudo docker build -t $MAZES_IMAGE:$MAZES_TAG ../server/
docker push $MAZES_IMAGE:$MAZES_TAG
```

## To build benchmarks / stressors
```
# Benchmark
DOCKER_REPO=<docker_repo>
MAZES_IMAGE=$DOCKER_REPO/mazes_benchmark
MAZES_TAG=latest
sudo docker build -t $MAZES_IMAGE:$MAZES_TAG ../benchmark/
docker push $MAZES_IMAGE:$MAZES_TAG

# Parsec wrapper for multiple packages
MAZES_IMAGE=$DOCKER_REPO/parsec
MAZES_TAG=latest
sudo docker build -t $MAZES_IMAGE:$MAZES_TAG ../parsec/
docker push $MAZES_IMAGE:$MAZES_TAG
```
* Uncomment the commented out lines in [kustomization.yaml](kustomization.yaml)

## To run
* Replace the `newName` and `newTag` field in [kustomization.yaml](kustomization.yaml) with the newly created images and tag
```
kubectl apply -k .
```
