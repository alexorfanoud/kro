# To run

```
docker-compose up -d
# Once the rps_calculator has determined the maximum rps possible, update the '-r' parameter in the client in the docker-compose file and rerun the command
```

# Possible todos
    * Replace the mean() metric being used to determine the QoS with something more accurate (max of the run, or nth percentile of the run)
    * Integrate prometheus + grafana for the graphs (both for rps_calculator-> rps/qos curve and for the client->qos curve)
