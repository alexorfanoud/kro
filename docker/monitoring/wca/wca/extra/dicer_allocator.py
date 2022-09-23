from dataclasses import dataclass, field
import logging
import os
import math
from typing import List

from wca.allocators import Allocator, RDTAllocation, TasksAllocations
from wca.detectors import Anomaly, TasksData
from wca.metrics import Metric
from wca.platforms import Platform
from wca.config import load_config, Path
from extra.static_allocator import _build_allocations_from_rules

from wca.prometheus import Prometheus
log = logging.getLogger(__name__)

@dataclass
class DicerAllocator(Allocator):

    appname_hp: str
    appname_be: str
    prom_host: str
    prom_port: int
    bw_limit: int
    qos_metric: str
    qos_limit: int
    phase_threshold: float
    max_ways_available: int
    rules: List[dict] = None
    config: Path =  None
    initial_run: bool = True
    prometheus: Prometheus = None
    min_cache_ways_limit: int = 1
    performance_drop_tolerance_percentage: float = 0.2
    metrics: dict = field(default_factory=lambda: {
                              "previous_mem_bw_hp_values": [],
                              "qos_opt": None,
                              "performance_diff": None,
                              "current_mem_bw_hp": 0,
                              "current_mem_bw_hp_diff": 0,
                              "current_mem_bw_be": 0,
                              "current_mem_bw_be_diff": 0,
                              "previous_qos_hp": None,
                              "current_qos_hp": None,
                              "bw_saturated": None,
                              "allocation_qos": {},
    })
    configuration: dict = field(default_factory=lambda: {
                                    "qos_perf_diff": 0.2,
                                    "current_allocation_hp": 19,
                                    "optimal_allocation_hp": 19,
                                    "rollback_allocation_hp": 19,
                                    "performing_allocation_reset": False,
                                    "performing_sampling": False,
                                })

    def __post_init__(self):
        self.prometheus = Prometheus(self.prom_host, self.prom_port)
        self.configuration["optimal_allocation_hp"] = self.max_ways_available - 1
        self.configuration["current_allocation_hp"] = self.max_ways_available - 1
        self.configuration["rollback_allocation_hp"] = self.max_ways_available - 1
        

    def get_qos(self):
        query_result = self.prometheus.do_query(self.qos_metric)
        try:
            value = float(query_result[0]['value'][1])
        except Exception:
            value = None

        log.warn(f'DicerAllocator: HP application QOS: {value}')
        return value
        
    def get_taskdata_from_labels(self, tasks_data: TasksData, label_name: str, values: List[str]):
        ret = {}
        for val in values:
            ret[val] = []
        for task_data in tasks_data.values():
            if task_data.labels.get(label_name) in values:
                ret[task_data.labels.get(label_name)].append(task_data)

        return ret

    def load_config_rules(self, tasks_data: TasksData):
        rules = []
        if self.rules:
            rules.extend(self.rules)

        if self.config:
            if not os.path.exists(self.config):
                log.warning('DicerAllocator: cannot find config file %r - ignoring!', self.config)
            else:
                rules.extend(load_config(self.config))

        if len(rules) == 0:
            log.warning('DicerAllocator: no rules were provided!')
            return {}, [], []


        tasks_allocations = _build_allocations_from_rules(tasks_data, rules)

        return tasks_allocations

    def allocate(
            self,
            _: Platform,
            tasks_data: TasksData
        ) -> tuple((TasksAllocations, List[Anomaly], List[Metric])):

        task_allocations = self.load_config_rules(tasks_data)

        # Get the app metrics from wca
        app_data = self.get_taskdata_from_labels(tasks_data, "app", [self.appname_hp, self.appname_be])

        # Wait for both HP and BE to be up
        if app_data is None or len(app_data.get(self.appname_hp)) == 0 or len(app_data.get(self.appname_be)) == 0:
            return (task_allocations, [], [])

        # Apply the static allocation once (for CPU pinning etc)
        if self.initial_run:
            self.monitor(app_data)
            self.initial_run = False
            return (task_allocations, [], [])

        # Monitor HP performance and memory bandwidth
        self.monitor(app_data)

        if self.configuration["performing_sampling"]:
            self.sample()
        # Optimise current allocation through sampling or reducing HP cache ways
        elif self.metrics["bw_saturated"] == True:
            self.allocation_sampling()
        else:
            self.allocation_optimisation()

        task_allocations.update(self.create_allocations(app_data))

        return (task_allocations, [], [])

    # Tracks app metrics and HP performance
    def monitor(self, app_data: dict):

        log.warn(f"DicerAllocator - monitor {self.metrics}")

        # Track HP app QOS
        current_qos = self.get_qos()
        self.metrics["previous_qos_hp"] = self.metrics["current_qos_hp"]
        self.metrics["current_qos_hp"] = current_qos

        # Store the QOS achieved with this allocation in memory
        self.metrics["allocation_qos"][self.configuration["current_allocation_hp"]] = current_qos

        # Keep track of the best allocation / QOS
        if self.metrics["qos_opt"] is None or current_qos < self.metrics["qos_opt"]:
            self.metrics["qos_opt"] = current_qos

        # Compare current QOS with previous
        self.assess_performance()

        # Find out how many bytes were transfered during the last monitoring period
        current_mem_bw_hp = sum(elem.measurements["task_mem_bandwidth_bytes"] for elem in app_data[self.appname_hp])
        # current_mem_bw_hp = app_data[self.appname_hp].measurements["task_mem_bandwidth_bytes"]
        mem_bw_hp_diff = current_mem_bw_hp - self.metrics["current_mem_bw_hp"]
        # current_mem_bw_be = app_data[self.appname_be].measurements["task_mem_bandwidth_bytes"]
        current_mem_bw_be = sum(elem.measurements["task_mem_bandwidth_bytes"] for elem in app_data[self.appname_be])
        mem_bw_be_diff = current_mem_bw_hp - self.metrics["current_mem_bw_be"]

        self.metrics["current_mem_bw_hp"] = current_mem_bw_hp
        self.metrics["current_mem_bw_be"] = current_mem_bw_be
        self.metrics["current_mem_bw_hp_diff"] = mem_bw_hp_diff
        self.metrics["current_mem_bw_be_diff"] = mem_bw_be_diff

        # store previous bw metrics for detecting phase change on HP app
        self.keep_mem_bw_metrics(self.metrics["current_mem_bw_hp_diff"])

        # Bandwidth saturation
        if mem_bw_hp_diff + mem_bw_be_diff > self.bw_limit:
            self.metrics["bw_saturated"] = True
        else:
            self.metrics["bw_saturated"] = False

        return

    def calculate_optimal_allocation(self):
        for cache_ways in range(self.max_ways_available):
            cache_ways_performance = self.metrics["allocation_qos"].get(cache_ways)
            # starting from the lowest ways allocated, look for an allocation within 20% of the optimal qos
            if cache_ways_performance is not None and cache_ways_performance < self.qos_limit:
                self.configuration["optimal_allocation_hp"] = cache_ways
                return

        # If we didn't find any acceptable allocation, just apply the max
        self.configuration["optimal_allocation_hp"] = self.max_ways_available - 1

    def allocation_sampling(self):
        log.warn(f"DicerAllocator - allocation_sampling {self.metrics}")

        # Apply max ways so that we begin resampling from the top
        self.configuration["current_allocation_hp"] = self.max_ways_available - 1
        self.configuration["performing_sampling"] = True
        return

    def sample(self):
        log.warn(f"DicerAllocator - sample {self.metrics}")
        # Completed sampling, apply optimal allocation
        if self.configuration["current_allocation_hp"] == self.min_cache_ways_limit:
            self.calculate_optimal_allocation()
            self.configuration["current_allocation_hp"] = self.configuration["optimal_allocation_hp"]
            self.configuration["performing_sampling"] = False
            return

        # Continue sampling downwards
        self.configuration["current_allocation_hp"] -= 1

        return

    # Optimises LLC allocation by reducing HP ways gradually
    def allocation_optimisation(self):
        log.warn(f"DicerAllocator - allocation_optimisation {self.metrics}")
        if self.phase_change():
            log.warn(f"DicerAllocator - detected phase change")
            self.allocation_reset()
            return

        # If performance has reached over a certain limit, we need to reset no matter if it improved or not
        if self.metrics["current_qos_hp"] > self.qos_limit * pow(1 + self.performance_drop_tolerance_percentage, 2) and not self.configuration["performing_allocation_reset"]:
            self.allocation_reset()
            return

        # stable performance
        if self.metrics["performance_diff"] == 0 and self.configuration["current_allocation_hp"] > self.min_cache_ways_limit:
            # Remove 1 LLC way from the HP app
            self.configuration["current_allocation_hp"] -= 1
        # improved performance
        elif self.metrics["performance_diff"] == 1:
            return
        # performance drop
        elif self.metrics["performance_diff"] == -1:
            # If performance dropped during reset, rollback to previous allocation
            if self.configuration["performing_allocation_reset"] == True:
                self.configuration["current_allocation_hp"] = self.configuration["rollback_allocation_hp"]
            else:
                self.allocation_reset()
                return
        self.configuration["performing_allocation_reset"] = False
        
    # Measures HP qos
    def assess_performance(self):
        if self.metrics["previous_qos_hp"] is None or self.metrics["current_qos_hp"] is None:
            return

        # stable performance
        if self.metrics["current_qos_hp"] <= self.qos_limit \
            or (self.metrics["previous_qos_hp"] * (1 - self.performance_drop_tolerance_percentage) <= self.metrics["current_qos_hp"] and \
                self.metrics["current_qos_hp"] <= self.metrics["previous_qos_hp"] * (1 + self.performance_drop_tolerance_percentage)):
            self.metrics["performance_diff"] = 0
        # improved performance
        elif self.metrics["current_qos_hp"] < self.metrics["previous_qos_hp"]:
            self.metrics["performance_diff"] = 1
        # performance drop
        elif self.metrics["current_qos_hp"] > self.metrics["previous_qos_hp"]:
            self.metrics["performance_diff"] = -1

    # Detects phase change for HP app
    def phase_change(self):
        if len(self.metrics["previous_mem_bw_hp_values"]) < 3:
            return False
        return math.abs(self.metrics["current_mem_bw_hp_diff"]) > (1 + self.phase_threshold) * (math.abs((self.metrics["previous_mem_bw_hp_values"][0] * self.metrics["previous_mem_bw_hp_values"][1] * self.metrics["previous_mem_bw_hp_values"][2])) ** (1/3))

    # Stores previous mem bw metrics
    def keep_mem_bw_metrics(self, metric: int):
        self.metrics["previous_mem_bw_hp_values"].append(metric)
        if len(self.metrics["previous_mem_bw_hp_values"]) > 3:
            del self.metrics["previous_mem_bw_hp_values"][0]

    def allocation_reset(self):
        log.warn(f"DicerAllocator - allocation_reset {self.metrics}")
        self.calculate_optimal_allocation()
        self.configuration["rollback_allocation_hp"] = self.configuration["current_allocation_hp"]
        self.configuration["current_allocation_hp"] = self.configuration["optimal_allocation_hp"]
        self.configuration["performing_allocation_reset"] = True

    def performance_near_opt(self, qos):
        if qos is None or qos <= 0:
            return False
        return abs((qos - self.metrics["qos_opt"]) / qos) <= self.configuration["qos_perf_diff"]

    def create_allocations(self, app_data: dict):
        hp_cache_ways = int("1" * self.configuration["current_allocation_hp"], 2)
        be_cache_ways = hp_cache_ways ^ int("1" * self.max_ways_available, 2)
        hp_cache_ways = hex(hp_cache_ways)[2:]
        be_cache_ways = hex(be_cache_ways)[2:]
        try:
            allocations = {}
            for task_hp in app_data[self.appname_hp]:
                allocations.setdefault(task_hp.task_id, {'rdt': RDTAllocation(name=self.appname_hp, l3=f"L3:0={hp_cache_ways}")})
            for task_be in app_data[self.appname_be]:
                allocations.setdefault(task_be.task_id, {'rdt': RDTAllocation(name=self.appname_be, l3=f"L3:0={be_cache_ways}")})
        except Exception as e:
            log.warn(f"dicer allocator exception: {e}")
            allocations = {}
        
        log.warn(f"DicerAllocator: create_allocations allocations={allocations}")
        return allocations
