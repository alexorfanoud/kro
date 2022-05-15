#!/usr/bin/python3

# This script performs multiple runs of the client benchmark of memcached
# In order to gather the RPS / QOS data and determine the max RPS we can use that satisfies the given QOS

import argparse
import os
import subprocess
import pandas as pd

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

class Executor:

    @staticmethod
    def check_output(cmd, fallback = None, **kwargs):
        try:
            ret = subprocess.check_output(cmd, **kwargs)\
                    .decode('utf-8').strip()
            return ret
        except Exception as exception:
            if ARGS is not None and ARGS.verbose is not None and ARGS.verbose:
                Logger.error(exception)
            if fallback is not None:
                fallback()
            return None

    @staticmethod
    def pipe(commands, fallback = None, **kwargs):
        try:
            pipes = [None]
            for idx, cmd in enumerate(commands):
                pipes.append(subprocess.Popen(cmd,
                        stdin = None if pipes[idx] is None else pipes[idx].stdout,
                        stdout = subprocess.PIPE, **kwargs))
            ret = pipes[-1].communicate()[0].decode('utf-8').strip()
            return ret
        except Exception as exception:
            if ARGS is not None and ARGS.verbose is not None and ARGS.verbose:
                Logger.error(exception)
            if fallback is not None:
                fallback()
            return None

def init_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', '-w', type=int, required=False, default=os.cpu_count())
    parser.add_argument('--scaling_factor', '-S', type=int, required=False, default=2)
    parser.add_argument('--target_server_memory', '-D', type=int, required=False, default=4096)
    parser.add_argument('--statistics_interval', '-T', type=int, required=False, default=1)
    parser.add_argument('--server_config', '-s', type=str, required=False, default="./docker_servers.txt")
    parser.add_argument('--timeout', '-t', type=str, required=False, default="15s")
    parser.add_argument('--QOS', '-Q', type=int, required=False, default=10)
    parser.add_argument('--rps_reduction_factor', '-r', type=float, required=False, default=0.1)
    parser.add_argument('--rps_diff_tolerance', '-R', type=float, required=False, default=0.1)
    parser.add_argument('--warmup_server', '-j', required=False, action='store_true', default=False)
    parser.add_argument('--verbose', '-v', required=False, action='store_true')

    global ARGS
    ARGS = parser.parse_args()
    print(ARGS)

def main():
    global ARGS
    init_args()

    if ARGS.warmup_server:
        warmup_server()
    max_rps = calculate_max_rps()

    Logger.success(f"Max rps calculated: {max_rps}")

    return max_rps



# Runs the warmup command and scales the input dataset
def warmup_server():

    Logger.info("Warming up server and scaling the dataset")
    server_warmup = Executor.check_output([
        "./loader",
        "-a", "../twitter_dataset/twitter_dataset_unscaled",
        "-o", "../twitter_dataset/twitter_dataset_scaled",
        "-s", f"{ARGS.server_config}",
        "-w", f"{ARGS.threads}",
        "-S", f"{ARGS.scaling_factor}",
        "-D", f"{ARGS.target_server_memory}",
        "-j",
        "-T", f"{ARGS.statistics_interval}"
    ])

    if server_warmup == "" or server_warmup is None:
        Logger.error("Unable to warmup server")
    else:
        Logger.info("Successfully warmed up server")

    if ARGS.verbose:
        Logger.info(f"server_warmup: {server_warmup}")

    return None



# Runs the benchmark for a given load (requests per second) and returns the statistics
# in the form of a list ["rps, qos", "rps,qos"]
def execute_trial_run(rps):

    Logger.info(f"Executing trial run for rps {rps}")

    trial_run = Executor.pipe([
        [
            "timeout", "--preserve-status", f"{ARGS.timeout}",
            "./loader",
            "-a", "../twitter_dataset/twitter_dataset_scaled",
            "-g", "0.8",
            "-c", "200",
            "-e",
            "-s", f"{ARGS.server_config}",
            "-w", f"{ARGS.threads}",
            "-D", f"{ARGS.target_server_memory}",
            "-T", f"{ARGS.statistics_interval}",
            "-r", f"{rps}"
        ],
        ["grep", "timeDiff", "-A1"],
        ["grep", "-v", "timeDiff"],
        ["awk", "{print $3,$10}"],
        ["grep", "-v", "^ $"],
    ])

    if trial_run == "" or trial_run is None:
        Logger.error("Unable to fetch trial_run statistics")
        return None

    # Remove trailing ',' and split per row
    trial_run_statistics = trial_run[:-1].split(',\n')
    # Split per column
    trial_run_statistics = [el.split(',') for el in trial_run_statistics]
    # Convert to floats
    trial_run_statistics_numeric = []
    for row in trial_run_statistics:
        row_numeric = []
        for el in row:
            f = float(el)
            row_numeric.append(f)
        trial_run_statistics_numeric.append(row_numeric)
    Logger.success(f"Successfully fetched trial_run statistics for rps {rps}")

    if ARGS.verbose:
        Logger.info(f"trial_run_statistics: {trial_run_statistics_numeric}")

    return trial_run_statistics_numeric



def process_run_statistics(rps, statistics):
    # Filter out rows with RPS that does not come close to the given limit for this specific run
    if rps != -1:
        rps_lower = rps * (1 - ARGS.rps_diff_tolerance)
        rps_upper = rps * (1 + ARGS.rps_diff_tolerance)
        statistics = statistics[(statistics['RPS'] >= rps_lower) & (statistics['RPS'] <= rps_upper)]
        
    # KRO TODO: is the mean a good metric to depend on? Should we use the max or something else?
    if ARGS.verbose:
        Logger.warn(statistics)
    rps_mean = statistics['RPS'].mean()
    qos_mean = statistics['QOS'].mean()

    return rps_mean, qos_mean



# Calculates the max load for which the QoS satisfies the requirements
def calculate_max_rps():
    qos = ARGS.QOS + 1
    rps = -1
    stats_output = ""

    while qos > ARGS.QOS and (rps == -1 or rps > 10000):
        trial_run_statistics = execute_trial_run(rps)
        statistics = pd.DataFrame.from_records(trial_run_statistics, columns=['RPS','QOS'])
        rps_mean, qos_mean = process_run_statistics(rps, statistics)

        Logger.warn(f"For run with rps: {rps_mean} found a mean QoS of: {qos_mean}")
        stats_output += f"{rps_mean},{qos_mean}\n"

        # Calculate the rps reduction step on the first run as it uses the maximum rps allowed by the system
        # as 10% of its value
        if rps == -1:
            ARGS.rps_reduction_step = rps_mean * ARGS.rps_reduction_factor

        # Update values
        rps = rps_mean - ARGS.rps_reduction_step
        qos = qos_mean

    if qos < ARGS.QOS:
        Logger.success(stats_output)
        res = rps_mean
    else:
        Logger.error("Could not find rps that satisfies the required QOS")
        res = -1

    return res



if __name__ == "__main__":
    main()
