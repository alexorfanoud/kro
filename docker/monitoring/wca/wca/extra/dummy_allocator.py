from dataclasses import dataclass
import logging
from typing import List

from wca.allocators import Allocator, TasksAllocations
from wca.detectors import Anomaly, TasksData
from wca.metrics import Metric
from wca.platforms import Platform

log = logging.getLogger(__name__)

@dataclass
class DummyAllocator(Allocator):

    def allocate(
            self,
            platform: Platform,
            tasks_data: TasksData
        ) -> tuple((TasksAllocations, List[Anomaly], List[Metric])):
        log.info(f"hello aorf {tasks_data}, {platform}")
        return ({}, [], [])
