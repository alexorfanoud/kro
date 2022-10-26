#!/usr/bin/env bash

while true
do 
    sleep 1s
    echo "Running benchmark with parameters $@"
    /benchmarks/movielens-als/run_benchmark.sh "$@"
done
