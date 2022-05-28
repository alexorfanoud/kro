#!/bin/bash

cbm_rotation=("7" "3" "1" "0")
current_cbm=("f" "f" "f" "f" "f")

function join_by { local IFS="$1"; shift; echo "$*"; }

function run_benchmark_with_cbm {
    echo "----------------------"
	echo "applying new rdt config $1"
    sed -i "s/L3:0=\(.*\)\"/L3:0=$1\"/" ../../monitoring/wca/configs/static_allocation.yaml
	echo "applying k8s manifest for wca"
    kubectl apply -k ../../monitoring/ 1>/dev/null
	echo "deleting nginx-client pod"
    kubectl delete -n kro $(kubectl get pod -n kro -oname | grep client)
    client_status=$(kubectl get pod -n kro | grep client | awk '{print $2}')
    while [ $client_status != "1/1" ] 
    do
        client_status=$(kubectl get pod -n kro | grep client | awk '{print $2}')
    done
	echo "greping for logs on nginx-client"
    logs=$(kubectl logs -n kro $(kubectl get pod -n kro -oname | grep client) -f | grep -iP "Requests|Replies|reply rate|reply time|Net I/O|Total connections" | tail -n6)
    echo "logs: $logs"
	echo "----------------" >> data.csv
	echo "allocation: $1" >> data.csv
    echo "$logs" >> data.csv
}

echo "RUN: $(date) ----------------- \n" >> data.csv
run_benchmark_with_cbm $(join_by "" ${current_cbm[@]})
for idx in ${!current_cbm[@]}
do
    for bit_mask in ${cbm_rotation[@]}
    do
        current_cbm[idx]=$bit_mask
        if [ ${current_cbm[@]} == "0 0 0 0 0"]
        then
            exit 0
        fi
        run_benchmark_with_cbm $(join_by "" ${current_cbm[@]})
    done
done

