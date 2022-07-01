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

    prometheus: Prometheus
    appname: str
    rules: List[dict] = None
    config: Path =  None
    initial_run: bool = True

    def get_taskdata_from_label(self, tasks_data: TasksData, name: str, value: str):
        for task_data in tasks_data.values():
            if task_data.labels.get(name) == value:
                return task_data
        return None

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

    def allocate(
            self,
            _: Platform,
            tasks_data: TasksData
        ) -> tuple((TasksAllocations, List[Anomaly], List[Metric])):


        if self.initial_run:
            self.initial_run = False
            return (self.load_config_rules(tasks_data), [], [])

        query_result = self.prometheus.do_query('memcached_metrics{metric="95th"}')
        log.error("aorf here1")
        log.error(query_result)

        app_data = self.get_taskdata_from_label(tasks_data, "app", self.appname)
        if app_data is None:
            return ({}, [], [])

        task_allocations_app = {
            app_data.task_id: {
                'rdt': RDTAllocation(name=self.appname, l3="L3:0=fffff")
            } 
        }

        return (task_allocations_app, [], [])
