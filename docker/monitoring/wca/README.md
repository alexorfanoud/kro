This is a fork from https://github.com/intel/workload-collocation-agent. 

### To build WCA

```
# For devel build
docker build . -t aorfanou/wca:devel --network host --target devel

# For standalone buid
docker build . -t aorfanou/wca:latest --network host --target standalone

docker push aorfanou/wca:<tag>
```

### To deploy to k8s

* Change the `newName` field in [wca manifest](kubernetes/monitoring/wca/kustomization.yaml) to be the newly created `WCA_IMAGE` name
