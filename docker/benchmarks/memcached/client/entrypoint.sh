#!/bin/bash

while getopts ":w:S:D:T:s:t:r:c:g:" opt; do
  case $opt in
    w)
	  threads=$(echo $OPTARG | xargs)
      ;;
    S)
	  scaling_factor=$(echo $OPTARG | xargs)
      ;;
    D)
	  target_server_memory=$(echo $OPTARG | xargs)
      ;;
    T)
	  statistics_interval=$(echo $OPTARG | xargs)
      ;;
    s)
	  server_config=$(echo $OPTARG | xargs)
      ;;
    r)
	  rps_limit=$(echo $OPTARG | xargs)
      ;;
    c)
	  connections=$(echo $OPTARG | xargs)
      ;;
    g)
	  get_set_ratio=$(echo $OPTARG | xargs)
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND-1))

# Builds the dataset by scaling the original dataset by the scaling factor
# Also warms up the server cache
./loader -a ../twitter_dataset/twitter_dataset_unscaled -o ../twitter_dataset/twitter_dataset_scaled -s $server_config -w $threads -S $scaling_factor -D $target_server_memory -j -T $statistics_interval

# Run after we have deducted the maximum RPS that can be served while respecting the QoS
# KRO TODO: keep only the QoS metric for easier use? eg pipe into grep, awk etc
./loader -a ../twitter_dataset/twitter_dataset_scaled -s $server_config -g $get_set_ratio -T $statistics_interval -c $connections -w $threads -e -r $rps_limit
