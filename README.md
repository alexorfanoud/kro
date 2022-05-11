# kro
Kubernetes resource optimisation

# Process
* Setup one or multiple apps in the k8s cluster
* We need to first define their QoS ( = what performance we expect when the app is running with full resources and maximum load ) by sampling their performance for gradually increasing loads. This the "knee" that was mentioned in the call.
* After we have the QoS we also need to determine how much cache is consumed by the app by sampling performance for gradually decreasing cache size (through wca cache masks)
* After we have max cache needed and QoS -> we can create an algorithm that partitions cache ?
