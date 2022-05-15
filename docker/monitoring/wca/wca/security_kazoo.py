# Copyright (c) 2019 Kazoo
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

import errno
import time
import socket
import ssl
from kazoo.handlers.utils import _set_default_tcpsock_options


# Definition copied from kazoo.handlers.utils and modified.
# Same code is commited in master but not released yet.
# After release version 2.6.2 it would be removed.
# Added possibility to set ssl options and ciphers.
def create_tcp_connection(module, address, timeout=None,
                          use_ssl=False, ca=None, certfile=None,
                          keyfile=None, keyfile_password=None,
                          verify_certs=True, options=None, ciphers=None):
    end = None
    if timeout is None:
        # thanks to create_connection() developers for
        # this ugliness...
        timeout = module.getdefaulttimeout()
    if timeout is not None:
        end = time.time() + timeout
    sock = None

    while True:
        timeout_at = end if end is None else end - time.time()
        # The condition is not '< 0' here because socket.settimeout treats 0 as
        # a special case to put the socket in non-blocking mode.
        if timeout_at is not None and timeout_at <= 0:
            break

        if use_ssl:
            # Disallow use of SSLv2 and V3 (meaning we require TLSv1.0+)
            context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

            if options is not None:
                context.options = options
            else:
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3

            if ciphers:
                context.set_ciphers(ciphers)

            # Load default CA certs
            context.load_default_certs(ssl.Purpose.SERVER_AUTH)
            context.verify_mode = (
                ssl.CERT_OPTIONAL if verify_certs else ssl.CERT_NONE
            )
            if ca:
                context.load_verify_locations(ca)
            if certfile and keyfile:
                context.verify_mode = (
                    ssl.CERT_REQUIRED if verify_certs else ssl.CERT_NONE
                )
                context.load_cert_chain(certfile=certfile,
                                        keyfile=keyfile,
                                        password=keyfile_password)
            try:
                # Query the address to get back it's address family
                addrs = socket.getaddrinfo(address[0], address[1], 0,
                                           socket.SOCK_STREAM)
                conn = context.wrap_socket(module.socket(addrs[0][0]))
                conn.settimeout(timeout_at)
                conn.connect(address)
                sock = conn
                break
            except ssl.SSLError:
                raise
        else:
            try:
                # if we got a timeout, lets ensure that we decrement the time
                # otherwise there is no timeout set and we'll call it as such
                sock = module.create_connection(address, timeout_at)
                break
            except Exception as ex:
                errnum = ex.errno if isinstance(ex, OSError) else ex[0]
                if errnum == errno.EINTR:
                    continue
                raise

    if sock is None:
        raise module.error

    _set_default_tcpsock_options(module, sock)
    return sock
