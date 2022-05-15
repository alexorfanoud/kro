This is a fork from https://github.com/intel/workload-collocation-agent. 

### To build WCA

```
WCA_IMAGE=<docker repo>/wca
WCA_TAG=latest
# You can use devel target for a dev/debug friendly deployment
docker build . -t $WCA_IMAGE:$WCA_TAG --network host -f Dockerfile --target standalone
docker push $WCA_IMAGE:$WCA_TAG
```

### To deploy to k8s

* Change the `newName` field in [wca manifest](kubernetes/monitoring/wca/kustomization.yaml) to be the newly created `WCA_IMAGE` name

## TODOS
* Figure out the RDT allocations https://github.com/intel/workload-collocation-agent/blob/master/docs/allocation.rst#rdt : `find /sys/devices/system/cpu -name "*id" | grep cache | xargs cat | sort` -> cache id's
