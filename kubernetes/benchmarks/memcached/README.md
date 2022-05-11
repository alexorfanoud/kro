## TODOS
* Find out what exactly are the metrics from memcached
* Increase the load gradually to find the max load. QOS is given
* Have the script parameters be passed from the k8s manifest
* Do i need to export any metrics to prometheus + grafana?
* Do i need to automate the process of running the script and finding the max RPS?

## Work on the existing image vs building a new one on top

### Existing image
* Need to mount the docker_servers file and the new entrypoint into the k8s pod through a configuration

### New image
* We can copy / move the scripts and docker_servers
* We can have the initial commands run as part of the image build -> won't be able to affect the parameters through k8s manifests, only the entrypoint command. Or we have the script


## Ideally what i would want whenever a new server pod is created:

* It builds the dataset (unless i have it mounted?)
* It warms up the server on that dataset
* It starts running the benchmark with various RPS and determines the maximum RPS that the system can serve (with some factor of flexibility?)

<!-- This is the actual task that we want -->
* It runs the actual benchmark so we can start working on cache partitioning

So ideally when i spin up a server pod:
* We already have the dataset and the RPS it can serve
* We just need to warm up the server and run the benchmark with the max RPS
