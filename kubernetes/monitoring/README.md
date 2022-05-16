### To deploy to k8s

```
kubectl create -k prometheus/crd
```
* On the master node of the cluster, execute:
```
sudo mkdir /var/lib/prometheus
sudo chmod 777 /var/lib/prometheus
sudo mkdir /var/lib/grafana
sudo chmod 777 /var/lib/grafana
sudo mount -t resctrl resctrl /sys/fs/resctrl
```
* Now apply the resource manifests
```
kubectl apply -k .
```

## TODOS
* Figure out the RDT allocations https://github.com/intel/workload-collocation-agent/blob/master/docs/allocation.rst#rdt : `find /sys/devices/system/cpu -name "*id" | grep cache | xargs cat | sort` -> cache id's
* Remember to uncomment the resctrl mounts
