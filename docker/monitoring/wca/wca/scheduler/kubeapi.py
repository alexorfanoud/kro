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
import os
import pathlib
import requests

from dataclasses import dataclass, field
from typing import Optional, List
from urllib.parse import urljoin

from wca.config import Str, Path, Numeric
from wca.kubernetes import SERVICE_TOKEN_FILENAME, SERVICE_CERT_FILENAME


log = logging.getLogger(__name__)


@dataclass
class Kubeapi:
    host: Str = None
    port: Str = None  # Because !Env is String and another type cast might be problematic

    client_token_path: Optional[Path(absolute=True, mode=os.R_OK)] = SERVICE_TOKEN_FILENAME
    server_cert_ca_path: Optional[Path(absolute=True, mode=os.R_OK)] = SERVICE_CERT_FILENAME

    timeout: Numeric(1, 60) = 5  # [s]
    monitored_namespaces: List[Str] = field(default_factory=lambda: ["default"])

    def __post_init__(self):
        self.endpoint = "https://{}:{}".format(self.host, self.port)

        log.debug("Created kubeapi endpoint %s", self.endpoint)

        with pathlib.Path(self.client_token_path).open() as f:
            self.service_token = f.read()

    def request_kubeapi(self, target):

        full_url = urljoin(
                self.endpoint,
                target)

        r = requests.get(
                full_url,
                headers={
                    "Authorization": "Bearer {}".format(self.service_token),
                    },
                timeout=self.timeout,
                verify=self.server_cert_ca_path)

        if not r.ok:
            log.error('An unexpected error occurred for target "%s": %i %s - %s',
                      target, r.status_code, r.reason, r.raw)
        r.raise_for_status()

        return r.json()

    def delete(self, target):
        full_url = urljoin(
                self.endpoint,
                target)

        r = requests.delete(
                full_url,
                headers={
                    "Authorization": "Bearer {}".format(self.service_token),
                    },
                timeout=self.timeout,
                verify=self.server_cert_ca_path)

        if not r.ok:
            log.error('An unexpected error occurred for target "%s": %i %s - %s',
                      target, r.status_code, r.reason, r.raw)
        r.raise_for_status()

        return r.json()
