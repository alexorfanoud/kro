## Examples

### Pin pods to cores statically

* After having set up your cluster with the pods you wish to manage:
* Follow instructions in [Readme](../../../README.md) to build the wca image
* Change the `newName` field in [wca manifest](kustomization.yaml) to be the newly created `WCA_IMAGE` name
* Configure the [allocator config manifest](configs/allocator_config.yaml) to monitor your namespace
* With the current configuration, wca is configured to run on all nodes of the cluster. If you wish to only target specific nodes, you need to create a node affinity component in the [daemonset manifest](daemonset.yaml) of wca, as demonstrated with the commented example.
* Configure the [static allocation config](configs/static_allocation.yaml) to pin labeled pods to specific cores based on the `labels` field
```
kubectl create namespace wca
kubectl apply -k .
# Verify the allocations
# Hash names correspond to container ids
kubectl logs -n wca $(k get pod -n wca -oname | head -1) -c wca | grep -oP "(Current allocations).*" | tail -1 | sed 's/Current allocations: //g' | sed "s/'/\"/g" | jq 2>/dev/null
```
