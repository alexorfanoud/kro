# Copyright (c) 2020 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Tuple, Dict, Any, List

from wca.metrics import Metric, MetricType
from wca.scheduler.algorithms.bar import BAR, log
from wca.scheduler.algorithms.base import DEFAULT_DIMENSIONS
from wca.scheduler.algorithms.least_used import LeastUsed
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ResourceType


class LeastUsedBAR(LeastUsed, BAR):
    def __init__(self, data_provider: DataProvider,
                 dimensions: List[ResourceType] = DEFAULT_DIMENSIONS,
                 least_used_weights: Dict[ResourceType, float] = None,
                 bar_weights: Dict[ResourceType, float] = None,
                 least_used_weight=1,
                 alias=None,
                 max_node_score: float = 10.,
                 ):
        LeastUsed.__init__(self, data_provider, dimensions, least_used_weights,
                           alias=alias, max_node_score=max_node_score)
        BAR.__init__(self, data_provider, dimensions,
                     bar_weights, alias=alias, max_node_score=max_node_score)
        self.least_used_weight = least_used_weight

    def __str__(self):
        if self.alias:
            return super().__str__()
        return '%s(%d,luw=%.2f)' % (self.__class__.__name__, len(self.dimensions),
                                    self.least_used_weight)

    def priority_for_node(self, node_name: str, app_name: str,
                          data_provider_queried: Tuple[Any]) -> float:
        """Putting together Least-used and BAR"""
        least_used_score = LeastUsed.priority_for_node(self, node_name, app_name,
                                                       data_provider_queried)
        bar_score = BAR.priority_for_node(self, node_name, app_name, data_provider_queried)
        result = least_used_score * self.least_used_weight + bar_score
        log.debug("[Prioritize][app=%s][node=%s] least_used_score=%s"
                  " bar_score=%s least_used_weight=%s result=%s",
                  app_name, node_name, least_used_score, bar_score, self.least_used_weight, result)
        self.metrics.add(
            Metric(name=MetricName.BAR_RESULT,
                   value=result, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        return result
