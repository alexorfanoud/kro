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
import logging
from typing import Dict, List, Tuple

from wca.logger import TRACE
from wca.metrics import Metric, MetricType
from wca.scheduler.algorithms.base import get_requested_fraction, DEFAULT_DIMENSIONS
from wca.scheduler.algorithms.fit import Fit
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.metrics import MetricName
from wca.scheduler.types import ResourceType

log = logging.getLogger(__name__)


def calculate_least_used_score(
        requested_fraction: Dict[ResourceType, float], weights: Dict[ResourceType, float]) \
        -> Tuple[Dict[ResourceType, float], float]:
    """Least used score based on requested_fraction and weigths for resources."""
    weights_sum = sum([weight for weight in weights.values()])
    free_fraction = {dim: 1.0 - fraction for dim, fraction in requested_fraction.items()}
    least_used_score = \
        sum([free_fraction * weights[dim] for dim, free_fraction in free_fraction.items()]) \
        / weights_sum
    return free_fraction, least_used_score


class LeastUsed(Fit):
    def __init__(self, data_provider: DataProvider,
                 dimensions: List[ResourceType] = DEFAULT_DIMENSIONS,
                 least_used_weights: Dict[ResourceType, float] = None,
                 alias=None,
                 max_node_score: float = 10.,
                 ):
        Fit.__init__(self, data_provider, dimensions, alias=alias, max_node_score=max_node_score)
        if least_used_weights is None:
            self.least_used_weights = {dim: 1 for dim in self.dimensions}
            self.least_used_weights[ResourceType.MEMBW_FLAT] = 1
        else:
            self.least_used_weights = least_used_weights

    def priority_for_node(self, node_name, app_name, data_provider_queried) -> float:
        """ Least used """
        nodes_capacities, assigned_apps, apps_spec, unassigned_apps_counts = \
            data_provider_queried
        requested_fraction, metrics = get_requested_fraction(
            app_name, apps_spec, assigned_apps, node_name, nodes_capacities, self.dimensions)
        self.metrics.extend(metrics)

        log.log(TRACE,
                "[Prioritize][app=%s][node=%s] (requested+used) "
                "fraction ((requested+used)/capacity): %s",
                app_name, node_name, requested_fraction)

        free_fraction, least_used_score = calculate_least_used_score(
            requested_fraction, self.least_used_weights)
        log.log(TRACE,
                "[Prioritize][app=%s][node=%s][least_used] "
                "free fraction (after new scheduling new pod) (1-requested_fraction): %s",
                app_name, node_name, free_fraction)
        log.log(TRACE, "[Prioritize][app=%s][node=%s][least_used] free fraction linear sum: %s",
                app_name, node_name, sum(free_fraction.values()))
        log.debug(
            "[Prioritize][app=%s][node=%s][least_used] "
            "Least used score (weighted linear sum of free_fraction): %s",
            app_name, node_name, least_used_score)
        self.metrics.add(
            Metric(name=MetricName.BAR_LEAST_USED_SCORE,
                   value=least_used_score, labels=dict(app=app_name, node=node_name),
                   type=MetricType.GAUGE))

        return least_used_score
