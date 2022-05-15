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
import statistics
from collections import defaultdict
from functools import reduce
from typing import Tuple, List, Dict

from wca.logger import TRACE
from wca.metrics import Metric
from wca.scheduler.algorithms.base import divide_resources, \
    calculate_read_write_ratio, sum_resources, subtract_resources, DEFAULT_DIMENSIONS
from wca.scheduler.algorithms.least_used_bar import LeastUsedBAR
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType, NodeName, Resources

log = logging.getLogger(__name__)

Shape = Tuple[Tuple[ResourceType, float], ...]
ShapeToNodes = Dict[Shape, List[NodeName]]
NodeCapacities = Dict[NodeName, Resources]


def _calc_average_resources(list_of_resources: List[Resources]) -> Resources:
    """Return average resources as sum of all nodes resources divided by number of nodes."""
    if not list_of_resources:
        return {}
    sum_of_resources = reduce(sum_resources, list_of_resources)
    averaged_resources_of_class = divide_resources(
        sum_of_resources,
        {r: len(list_of_resources) for r in sum_of_resources.keys()},
    )
    return averaged_resources_of_class


def _resources_to_shape(resources: Dict[ResourceType, float]) -> Shape:
    # for visualization reasons always normalized to 1 cpu
    # cpus = resources[rt.CPU]
    return tuple(sorted({r: int(v) for r, v in resources.items()}.items()))


def _shape_diff(first: Shape, second: Shape) -> float:
    """Return resources variance between first and second."""
    first_resources = dict(first)
    second_resources = dict(second)
    assert len(first_resources.keys()) > 1, 'variance requires at least 2 data points'
    assert len(second_resources.keys()) > 1, 'variance requires at least 2 data points'
    resdiff = subtract_resources(first_resources, second_resources)
    diff_variance = statistics.stdev(resdiff.values())
    log.log(TRACE, '[Filter2][shape_diff] first=%s second=%s shape_diff=%s',
            first, second, diff_variance)
    return diff_variance


def create_new_shape(shapes_to_nodes: ShapeToNodes,
                     node_capacities: NodeCapacities,
                     shapes: List[Shape]) -> Tuple[Shape, List[NodeName]]:
    """ Take list of shapes and convert it one new shape, based on average of resources capacity
    of nodes from those shapes.
    """
    node_names_for_new_shape = []
    for shape in shapes:
        node_names_for_new_shape.extend(shapes_to_nodes[shape])
    nodes = [node_capacities[n] for n in node_names_for_new_shape]
    avg_resources = _calc_average_resources(nodes)
    new_shape = _resources_to_shape(avg_resources)
    log.log(TRACE, '[Filter2][create_new_shape] shapes=%s new_shape=%s with nodes=%s',
            shapes, new_shape, node_names_for_new_shape)

    return new_shape, node_names_for_new_shape


def _merge_shapes(merge_threshold: float, node_capacities: NodeCapacities,
                  shapes_to_nodes: ShapeToNodes) -> ShapeToNodes:
    old_number_of_shapes = len(shapes_to_nodes)
    if old_number_of_shapes < 2:
        return shapes_to_nodes

    above_shapes = []
    below_shapes = []

    new_shapes_to_nodes = {}
    for shape in shapes_to_nodes.keys():
        shape_resources = dict(shape)
        ratio = calculate_read_write_ratio(shape_resources)
        if ratio is None:
            log.warning('not mergable shape=%r found in shape_to_nodes=%r! ignored!: ', shape,
                        shapes_to_nodes)
            continue
        log.log(TRACE, '[Filter2][merge_shapes] shape=%s ratio=%r merge_threshold=%r',
                shape, ratio, merge_threshold)
        if ratio > merge_threshold:
            above_shapes.append(shape)
        else:
            below_shapes.append(shape)

    above_shape, above_nodes = create_new_shape(shapes_to_nodes, node_capacities, above_shapes)
    below_shape, below_nodes = create_new_shape(shapes_to_nodes, node_capacities, below_shapes)

    if above_shape:
        new_shapes_to_nodes[above_shape] = above_nodes
    if below_shape:
        new_shapes_to_nodes[below_shape] = below_nodes

    if old_number_of_shapes != len(new_shapes_to_nodes):
        log.debug('[Filter2] Merged shapes: %s->%s, new_shapes: %s', old_number_of_shapes,
                  len(new_shapes_to_nodes), new_shapes_to_nodes)

    return new_shapes_to_nodes


def shape_to_str(shape: Shape) -> str:
    return ','.join('%r=%.0f' % (r, v) for r, v in shape)


def resource_to_str(resources: Resources) -> str:
    return ','.join('%r=%.0f' % (r, v) for r, v in sorted(resources.items()))


def calculate_class_variances(app_name: str,
                              node_capacities: NodeCapacities,
                              requested: Resources,
                              shapes_to_nodes: ShapeToNodes
                              ) -> Tuple[Dict[Shape, float], List[Metric]]:
    """Calculate all classes bar (fitness) score"""
    metrics = []
    class_variances: Dict[Shape, float] = {}  # dict: class_shape->fit
    for class_shape, node_names_of_this_shape in shapes_to_nodes.items():
        node_capacities_of_this_shape = [node_capacities[node_name] for node_name in
                                         node_names_of_this_shape]
        averaged_resources_of_class = _calc_average_resources(
            node_capacities_of_this_shape)
        requested_empty_fraction = divide_resources(
            requested,
            averaged_resources_of_class,
            calculate_read_write_ratio(averaged_resources_of_class)
        )

        variance = statistics.stdev(requested_empty_fraction.values())
        log.log(TRACE, '[Filter2] class_shape=%s average_resources_of_class=%s '
                       'requested=%s requested_fraction=%s variance=%s', class_shape,
                averaged_resources_of_class, requested, requested_empty_fraction, variance)
        class_variances[class_shape] = variance

        class_shape_str = shape_to_str(class_shape)
        metrics.extend([
            Metric(
                name='wca_scheduler_hierbar_node_shape_app_variance',
                labels=dict(app=app_name,
                            app_requested=resource_to_str(requested),
                            shape=class_shape_str),
                value=variance
            ),
            Metric(
                name='wca_scheduler_hierbar_node_shape_numbers',
                labels=dict(shape=class_shape_str),
                value=len(node_capacities_of_this_shape),
            )
        ])
    return class_variances, metrics


def reverse_node_shapes(node_shapes: Dict[NodeName, Shape]) -> ShapeToNodes:
    """Reverse node_capacities to find type of node."""
    shapes_to_nodes = defaultdict(list)
    for node_name, shape in node_shapes.items():
        shapes_to_nodes[shape].append(node_name)
    shapes_to_nodes = dict(shapes_to_nodes)
    return shapes_to_nodes


def _create_shapes_from_nodes(node_capacities: NodeCapacities) -> Dict[NodeName, Shape]:
    """ Build mapping from node names to shapes."""
    node_shapes = {node_name: _resources_to_shape(node_capacity)
                   for node_name, node_capacity in node_capacities.items()}
    return node_shapes


class HierBAR(LeastUsedBAR):

    def __init__(self,
                 data_provider: DataProvider,
                 dimensions: List[ResourceType] = DEFAULT_DIMENSIONS,
                 alias=None,
                 merge_threshold: float = None,
                 max_node_score: float = 10.
                 ):
        LeastUsedBAR.__init__(self, data_provider, dimensions, alias=alias,
                              max_node_score=max_node_score)
        self.merge_threshold = merge_threshold

    def __str__(self):
        if self.alias:
            return super().__str__()
        return '%s(%d%s)' % (
            self.__class__.__name__, len(self.dimensions),
            ',merge=%s' % self.merge_threshold if self.merge_threshold is not None else '')

    def app_fit_nodes(self, node_names, app_name, data_provider_queried
                      ) -> Tuple[List[NodeName], Dict[NodeName, str]]:

        log.log(TRACE, '[Filter2] -> nodes_names=[%s]', ','.join(node_names))

        # TODO: Optimize - this context should be calculated earlier (add passed for every node)
        node_capacities, _, apps_spec, _ = data_provider_queried

        node_shapes = _create_shapes_from_nodes(node_capacities)
        shapes_to_nodes = reverse_node_shapes(node_shapes)

        # Merging similar node shapes (less_shapes)
        if self.merge_threshold is not None:
            shapes_to_nodes = _merge_shapes(self.merge_threshold, node_capacities, shapes_to_nodes)
            # After shape merging build inverse relation node->shape.
            node_shapes = {}
            for shape, nodes in shapes_to_nodes.items():
                for node in nodes:
                    node_shapes[node] = shape

        # Number of nodes of each class
        # number_of_nodes_each_shape = dict(Counter(node_shapes.values()))

        requested = apps_spec[app_name]

        class_variances, metrics = calculate_class_variances(
            app_name, node_capacities, requested, shapes_to_nodes)

        self.metrics.extend(metrics)

        log.log(TRACE, '[Filter2][app=%s] app_shape=%s scores for each class of nodes: %s',
                app_name, _resources_to_shape(requested), class_variances)

        # Start with best class (least variance)
        failed = {}  # node_name to error string

        for class_shape, class_variance in sorted(class_variances.items(),
                                                  key=lambda x: x[1]):
            class_shape: Shape
            class_variance: float
            best_node_names_according_shape = shapes_to_nodes[class_shape]

            accepted_node_names = list(set(node_names) & set(best_node_names_according_shape))
            # If we found at least one node is this class then leave.
            if accepted_node_names:
                matching_class_variance = class_variance
                break
            else:
                log.debug(
                    '[Filter2][app=%s] no enough nodes '
                    'in best class (shape=%s, nodes=[%s] variance=%.2f), take next class',
                    app_name, class_shape, ','.join(best_node_names_according_shape),
                    class_variance)
        else:
            assert False, 'Last class has to match!'

        failed_names = set(node_names) - set(accepted_node_names)
        for failed_node_name in failed_names:
            failed_node_variance = class_variances[node_shapes[failed_node_name]]
            failed[failed_node_name] = 'Not best class (best_variance=%.2f this=%.2f)' % (
                matching_class_variance, failed_node_variance)

        log.info(
            '[Filter2][app=%s] nodes=[%s] best_class=%r best_class_variance=%.3f best_nodes=[%s]',
            app_name, ','.join(node_names), dict(class_shape),
            matching_class_variance, ','.join(accepted_node_names))

        log.log(TRACE, '[Filter2][app=%s] <- accepted_node_names=[%s]', app_name,
                ','.join(accepted_node_names))
        return accepted_node_names, failed
