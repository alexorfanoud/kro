#!/usr/bin/python3

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Globals
ARGS = None

class Colors:
    RED='\033[0;31m'
    CYAN='\033[0;96m'
    YELLOW='\033[1;33m'
    GREEN='\033[0;32m'
    LIGHT_GREEN='\033[1;32m'
    NC='\033[0m'

class Logger:
    @staticmethod
    def info(msg, color = Colors.NC):
        print(color + str(msg) + Colors.NC)

    @staticmethod
    def warn(msg):
        print(Colors.YELLOW + str(msg) + Colors.NC)

    @staticmethod
    def error(msg):
        print(Colors.RED + str(msg) + Colors.NC)

    @staticmethod
    def success(msg):
        print(Colors.GREEN + str(msg) + Colors.NC)


def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--memcached_metrics_path', '-m', type=str, required=True)
    parser.add_argument('--parsec_package_times_path', '-p', type=str, required=True)
    parser.add_argument('--verbose', '-v', required=False, action='store_true')

    global ARGS
    ARGS = parser.parse_args()
    print(ARGS)

def process_metrics(parsec_package_times_path: str, memcached_metrics_path: str):
    parsec_times = pd.read_csv(parsec_package_times_path)
    memcached_metrics = pd.read_csv(memcached_metrics_path)

    metrics = {}
    metrics["no-stress"] = memcached_metrics[memcached_metrics["Time"] <= parsec_times["start"].min()]["95th"]
    for _, parsec_row in parsec_times.iterrows():
        if parsec_row["package"] != "test":
            metrics[parsec_row["package"]] = memcached_metrics[(memcached_metrics['Time'] >= parsec_row["start"]) & (memcached_metrics['Time'] <= parsec_row["finish"])]["95th"]

    if ARGS.verbose:
        Logger.warn(metrics)

    plt.figure(figsize=(15,7))
    plt.boxplot(metrics.values(), labels=metrics.keys())
    plt.show()

def main():
    global ARGS
    init_args()
    process_metrics(ARGS.parsec_package_times_path, ARGS.memcached_metrics_path)


# Runs the warmup command and scales the input dataset
if __name__ == "__main__":
    main()
