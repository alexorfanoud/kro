from dataclasses import dataclass, field
import logging
import os
from typing import List

from wca.allocators import Allocator, RDTAllocation, TasksAllocations
from wca.detectors import Anomaly, TasksData
from wca.metrics import Metric
from wca.platforms import Platform
from wca.config import load_config, Path
from extra.static_allocator import _build_allocations_from_rules

from wca.logger import TRACE
from wca.prometheus import Prometheus
log = logging.getLogger(__name__)

@dataclass
class CacheSplitAllocator(Allocator):

    appname: str
    contestant: str
    prom_host: str
    prom_port: int
    qos_limit: int
    qos_metric: str
    rules: List[dict] = None
    config: Path =  None
    initial_run: bool = True
    prometheus: Prometheus = None

    def __post_init__(self):
        self.prometheus = Prometheus(self.prom_host, self.prom_port)

    def get_qos(self):
        query_result = self.prometheus.do_query(self.qos_metric)
        try:
            value = float(query_result[0]['value'][1])
        except Exception:
            value = None

        return value
        
    def get_taskdata_from_labels(self, tasks_data: TasksData, name: str, values: List[str]):
        ret = {}
        for task_data in tasks_data.values():
            if task_data.labels.get(name) in values:
                ret[task_data.labels.get(name)] = task_data
        return ret

    def load_config_rules(self, tasks_data: TasksData):
        rules = []
        if self.rules:
            rules.extend(self.rules)

        if self.config:
            if not os.path.exists(self.config):
                log.warning('CacheSplitAllocator: cannot find config file %r - ignoring!', self.config)
            else:
                rules.extend(load_config(self.config))

        if len(rules) == 0:
            log.warning('CacheSplitAllocator: no rules were provided!')
            return {}, [], []

        log.log(TRACE,
                'CacheSplitAllocator: handling allocations for %i tasks. ', len(tasks_data))
        for _, data in tasks_data.items():
            log.log(TRACE, '%s', ' '.join(
                '%s=%s' % (k, v) for k, v in sorted(data.labels.items())))

        tasks_allocations = _build_allocations_from_rules(tasks_data, rules)

        return tasks_allocations

    def create_split_cache_allocation(self, app_data: dict):
        split_allocations = {
            app_data[self.appname].task_id: {
                'rdt': RDTAllocation(name=self.appname, l3="L3:0=0000f")
            },
            app_data[self.contestant].task_id: {
                'rdt': RDTAllocation(name=self.contestant, l3="L3:0=000f0")
            },
        }
            
        return split_allocations

    def allocate(
            self,
            _: Platform,
            tasks_data: TasksData
        ) -> tuple((TasksAllocations, List[Anomaly], List[Metric])):

        task_allocations = {}

        if self.initial_run:
            self.initial_run = False
            return (self.load_config_rules(tasks_data), [], [])

        app_data = self.get_taskdata_from_labels(tasks_data, "app", [self.appname, self.contestant])
        if app_data is None:
            return (task_allocations, [], [])

        current_qos = self.get_qos()
        if current_qos > self.qos_limit:
            task_allocations = self.create_split_cache_allocation(app_data)

        return (task_allocations, [], [])
