#!/bin/bash

while getopts ":w:S:D:T:s:t:Q:r:" opt; do
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
    t)
	  timeout=$(echo $OPTARG | xargs)
      ;;
    Q)
	  QOS=$(echo $OPTARG | xargs)
      ;;
    r)
	  rps_factor=$(echo $OPTARG | xargs)
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

# Runs the benchmark on the scaled dataset with a get/set ratio of 0.8 and 200 connections. 
# Use to find the maximum RPS that satisfies the QoS (95% of requests within 10ms)
trial_run_output=$(timeout $timeout ./loader -a ../twitter_dataset/twitter_dataset_scaled -s $server_config -g 0.8 -T $statistics_interval -c 200 -w $threads -e | grep timeDiff -A 1 | grep -v timeDiff | awk '{print $3,$10}' | grep -v "^ $" | sort | tail -n1)

echo $trial_run_output
trial_run_max_rps=$(echo $trial_run_output | awk -F',' '{print $1}' | xargs)
trial_run_max_rps_10_percent=$(expr $trial_run_max_rps '/' 10)
trial_run_95th_delay_ms_int=$(echo $trial_run_output | awk -F',' '{print $2}' | xargs | cut -d. -f1)
echo "max_rps: '$trial_run_max_rps', max_rps_10_percent: $trial_run_max_rps_10_percent, 95th delay ms: '$trial_run_95th_delay_ms_int'"

while [ $trial_run_95th_delay_ms_int -gt $QOS ]
do
    # Max RPS = 90% of previous run
    trial_run_max_rps=$(expr $trial_run_max_rps_10_percent '*' $rps_factor)
    echo "Starting run with rps = $trial_run_max_rps"
    # Runs the benchmark on the scaled dataset with a get/set ratio of 0.8 and 200 connections. 
    # Use to find the maximum RPS that satisfies the QoS (95% of requests within 10ms)
    trial_run_output=$(timeout $timeout ./loader -a ../twitter_dataset/twitter_dataset_scaled -s $server_config -g 0.8 -T $statistics_interval -c 200 -w $threads -e -r $trial_run_max_rps | grep timeDiff -A 1 | grep -v timeDiff | awk '{print $3,$10}' | grep -v "^ $" | sort | tail -n1)

    echo $trial_run_output
    trial_run_max_rps=$(echo $trial_run_output | awk -F',' '{print $1}' | xargs)
    trial_run_max_rps_10_percent=$(expr $trial_run_max_rps '/' 10)
    trial_run_95th_delay_ms_int=$(echo $trial_run_output | awk -F',' '{print $2}' | xargs | cut -d. -f1)
    echo "max_rps: '$trial_run_max_rps', max_rps_10_percent: $trial_run_max_rps_10_percent, 95th delay ms: '$trial_run_95th_delay_ms_int'"
done
# Consider having a docker image with a python server that listens for data requests and gathers some data around them - with http requests - can also expose that data to prometheus so we can get visual representation of the knee curves?

# Run after we have deducted the maximum RPS that can be served while respecting the QoS
./loader -a ../twitter_dataset/twitter_dataset_scaled -s $server_config -g 0.8 -T $statistics_interval -c 200 -w $threads -e -r $trial_run_max_rps
