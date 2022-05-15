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
from wca.scheduler.types import (
        ExtenderArgs, TaskName, AppName, NodeName)

from typing import Tuple, List


def extract_common_input(extender_args: ExtenderArgs) \
        -> Tuple[AppName, List[NodeName], str, TaskName]:
    nodes = extender_args.NodeNames
    metadata = extender_args.Pod.get('metadata', {})
    labels = metadata.get('labels', {})
    name = metadata.get('name', '')
    namespace = metadata.get('namespace', '')
    app = labels.get('app', None)
    return app, nodes, namespace, name
