#!/bin/bash

memcached_workdir=/usr/src/memcached/memcached_client
memcached_workdir_volumes=/usr/src/memcached/memcached_client/volumes

# Builds the dataset by scaling the original dataset x30 times
# Also warms up the server cache
$memcached_workdir/loader -a $memcached_workdir/../twitter_dataset/twitter_dataset_unscaled -o $memcached_workdir/../twitter_dataset/twitter_dataset_30x -s $memcached_workdir_volumes/docker_servers.txt -w 4 -S 30 -D 4096 -j -T 1

# Runs the benchmark on the scaled dataset with a get/set ratio of 0.8 and 200 connections. Use to find the maximum RPS that satisfies the QoS (95% of requests within 10ms)
$memcached_workdir/loader -a $memcached_workdir/../twitter_dataset/twitter_dataset_30x -s $memcached_workdir_volumes/docker_servers.txt -g 0.8 -T 1 -c 200 -w 8 -e -r  70000

# Run after we have deducted the maximum RPS that can be served while respecting the QoS
# $memcached_workdir/loader -a $memcached_workdir/../twitter_dataset/twitter_dataset_30x -s $memcached_workdir_volumes/docker_servers.txt -g 0.8 -T 1 -c 200 -w 8 -e -r <MAX RPS>

# RPS          | 95th percentile
# 1k requests -> 0.8
# 10k requests ->  2
# 20k requests ->  6.5
# 30k requests ->  7.5
# 40k requests ->  7.5
# 50k requests ->  7.5
# 80k requests -> stabilises at ~9
# 90k requests -> 10
# 100k requests ->  160
