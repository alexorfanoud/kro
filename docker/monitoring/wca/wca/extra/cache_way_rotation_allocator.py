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
log = logging.getLogger(__name__)

@dataclass
class CacheWayRotationAllocator(Allocator):

    appname: str
    rules: List[dict] = None
    config: Path =  None
    cbm_rotation: List[str] = field(default_factory=lambda: ["7", "3", "1", "0"])
    initial_cbm: List[str] = field(default_factory=lambda: ["f", "f", "f", "f", "f"])
    cbm: List[str] = field(default_factory=list)
    cbm_idx: int = 0
    initial_run: bool = True
    run_idx: int = 0

    def generate_cbm(self):
        self.cbm.append("".join(self.initial_cbm))
        for bit_index, _ in enumerate(self.initial_cbm):
            for bit_mask in self.cbm_rotation:
                self.initial_cbm[bit_index]=bit_mask
                self.cbm.append("".join(self.initial_cbm))
        self.cbm.pop()

    def get_taskdata_from_label(self, tasks_data: TasksData, name: str, value: str):
        for task_data in tasks_data.values():
            if task_data.labels.get(name) == value:
                return task_data
        return None

    def get_next_cbm_allocation(self):
        if len(self.cbm) == 0:
            self.generate_cbm()

        ret = "L3:0=" + self.cbm[self.cbm_idx]

        # Apply next allocation every 3 runs of wca's intervals (in our case 3m)
        if self.cbm_idx < len(self.cbm) - 1 and self.run_idx % 3 == 0:
            self.cbm_idx += 1

        return ret
        

    def load_config_rules(self, tasks_data: TasksData):
        rules = []
        if self.rules:
            rules.extend(self.rules)

        if self.config:
            if not os.path.exists(self.config):
                log.warning('CacheWayRotationAllocator: cannot find config file %r - ignoring!', self.config)
            else:
                rules.extend(load_config(self.config))

        if len(rules) == 0:
            log.warning('CacheWayRotationAllocator: no rules were provided!')
            return {}, [], []

        log.log(TRACE,
                'CacheWayRotationAllocator: handling allocations for %i tasks. ', len(tasks_data))
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

        self.run_idx += 1

        if self.initial_run:
            self.initial_run = False
            return (self.load_config_rules(tasks_data), [], [])

        app_data = self.get_taskdata_from_label(tasks_data, "app", self.appname)
        if app_data is None:
            return ({}, [], [])

        task_allocations_app = {
            app_data.task_id: {
                'rdt': RDTAllocation(name=self.appname, l3=self.get_next_cbm_allocation())
            } 
        }

        return (task_allocations_app, [], [])
