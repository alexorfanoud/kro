#!/usr/bin/python3

import argparse
import pandas as pd
import numpy as np
from datetime import datetime
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
    parser.add_argument('--compare', action="store_true", required=False, default=False)
    parser.add_argument('--memcached_metrics_path_compare', "-m2", type=str, required=False)
    parser.add_argument('--parsec_package_times_path_compare', "-p2", type=str, required=False)
    parser.add_argument('--verbose', '-v', required=False, action='store_true')

    global ARGS
    ARGS = parser.parse_args()
    print(ARGS)

def plot_parsec_times(parsec_times, parsec_times_compare, labels):

    # Parsec times per package
    plt.figure(figsize=(15,7))

    X_axis = np.arange(len(labels))

    plt.bar(X_axis - 0.2, parsec_times, 0.4, label = 'no-split')
    plt.bar(X_axis + 0.2, parsec_times_compare, 0.4, label = 'split-cache')
    plt.xticks(X_axis, labels)
    plt.xlabel("Package")
    plt.ylabel("Time (s)")
    plt.title("Time per package")
    plt.legend()

def plot_memcached_metrics(memcached_metrics, memcached_metrics_compare, memcached_labels):

    plt.figure(figsize=(20,7))
    plt.xlabel("Package")
    plt.ylabel("95th percentile of memcached requests")
    X_axis = np.arange(len(memcached_labels))
    plt.boxplot(memcached_metrics, positions = X_axis - 0.2, widths = 0.35, )
    plt.boxplot(memcached_metrics_compare, positions = X_axis + 0.2, widths = 0.35, )
    plt.xticks(X_axis, memcached_labels)


def process_metrics(parsec_package_times_path: str, memcached_metrics_path: str):
    parsec_times = pd.read_csv(parsec_package_times_path)
    time_fmt = "%Y-%m-%d %H:%M:%S"
    parsec_durations = [datetime.strptime(row["finish"], time_fmt) - datetime.strptime(row["start"], time_fmt) for _,row in parsec_times.iterrows()]
    memcached_metrics = pd.read_csv(memcached_metrics_path)

    metrics = {}
    metrics["no-stress"] = memcached_metrics[memcached_metrics["time"] <= parsec_times["start"].min()]["95th"]
    for _, parsec_row in parsec_times.iterrows():
        if parsec_row["package"] != "test":
            metrics[parsec_row["package"]] = memcached_metrics[(memcached_metrics['time'] >= parsec_row["start"]) & (memcached_metrics['time'] <= parsec_row["finish"])]["95th"]

    if ARGS.verbose:
        Logger.warn(metrics)

    return metrics.values(), metrics.keys(), [duration.total_seconds() for duration in parsec_durations], list(metrics.keys())[1:]


def compare_metrics(parsec_package_times_path: str, parsec_package_times_path_compare: str, memcached_metrics_path: str, memcached_metrics_path_compare: str):
    memcached_metrics, memcached_metrics_labels, parsec_times, parsec_times_labels = process_metrics(parsec_package_times_path, memcached_metrics_path)
    memcached_metrics_2, _, parsec_times_2, _ = process_metrics(parsec_package_times_path_compare, memcached_metrics_path_compare)

    plot_parsec_times(parsec_times, parsec_times_2, parsec_times_labels)
    plot_memcached_metrics(memcached_metrics, memcached_metrics_2, memcached_metrics_labels)

    plt.show()

def main():
    global ARGS
    init_args()
    if ARGS.compare:
        compare_metrics(ARGS.parsec_package_times_path, ARGS.parsec_package_times_path_compare, ARGS.memcached_metrics_path, ARGS.memcached_metrics_path_compare)
    else:
        process_metrics(ARGS.parsec_package_times_path, ARGS.memcached_metrics_path)


# Runs the warmup command and scales the input dataset
if __name__ == "__main__":
    main()
