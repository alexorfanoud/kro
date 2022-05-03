#!/bin/bash

memcached_workdir=/usr/src/memcached/memcached_client
memcached_workdir_volumes=/usr/src/memcached/memcached_client/volumes

$memcached_workdir/loader -a $memcached_workdir/../twitter_dataset/twitter_dataset_unscaled -o $memcached_workdir/../twitter_dataset/twitter_dataset_30x -s $memcached_workdir_volumes/docker_servers.txt -w 4 -S 30 -D 4096 -j -T 1
$memcached_workdir/loader -a $memcached_workdir/../twitter_dataset/twitter_dataset_30x -s $memcached_workdir_volumes/docker_servers.txt -g 0.8 -T 1 -c 200 -w 8
# $memcached_workdir/loader -a $memcached_workdir/../twitter_dataset/twitter_dataset_30x -s $memcached_workdir_volumes/docker_servers.txt -g 0.8 -T 1 -c 200 -w 8 -e -r rps
