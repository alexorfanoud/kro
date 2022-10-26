#!/bin/bash

while getopts ":S:a:p:i:n:s:" opt; do
  case $opt in
    S)
	  suite=$(echo $OPTARG | xargs)
      ;;
    a)
	  action=$(echo $OPTARG | xargs)
      ;;
    p)
	  packages=$(echo $OPTARG | xargs)
      ;;
    i)
	  input=$(echo $OPTARG | xargs)
      ;;
    n)
	  threads=$(echo $OPTARG | xargs)
      ;;
    s)
	  sleep_time=$(echo $OPTARG | xargs)
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

IFS=','
read -a packages_arr <<< "$packages"
for package in ${packages_arr[@]};do
	sleep $sleep_time
	start_time=$(date '+%y-%m-%d %H:%M:%S')
	echo "Running $package"
	./run -p $package -S $suite -a $action -i $input -n $threads
	echo -e "Parsec_interval\t$package,$start_time,$(date '+%y-%m-%d %H:%M:%S')"
done
