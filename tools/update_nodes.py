#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright © 2025 The TokTok team
import json
import os
import re
import socket
from dataclasses import asdict
from dataclasses import dataclass
from functools import cache as memoize
from typing import Any
from typing import Optional

import requests

_NODES_URL = "https://nodes.tox.chat/json"
_NODES_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "res",
                           "nodes.json")

_IPV4_REGEX = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
# https://stackoverflow.com/a/17871737
_IPV6_REGEX = re.compile(
    r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
)


@dataclass
class Node:
    ipv4: Optional[str]
    ipv6: Optional[str]
    port: int
    tcp_ports: list[int]
    public_key: str
    maintainer: str
    location: str
    status_udp: bool
    status_tcp: bool
    version: str
    motd: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Node":
        return Node(
            ipv4=data.get("ipv4"),
            ipv6=data.get("ipv6"),
            port=data["port"],
            tcp_ports=sorted(data["tcp_ports"]),
            public_key=data["public_key"],
            maintainer=data["maintainer"],
            location=data["location"],
            status_udp=data["status_udp"],
            status_tcp=data["status_tcp"],
            version=data["version"],
            motd=data["motd"],
        )


def _get_nodes() -> list[Node]:
    response = requests.get(_NODES_URL)
    response.raise_for_status()
    return [Node.from_dict(node) for node in response.json()["nodes"]]


@memoize
def _resolve(host: str, port: int,
             family: socket.AddressFamily) -> Optional[str]:
    """Resolve a hostname to an IP address."""
    if _IPV4_REGEX.match(host) or _IPV6_REGEX.match(host):
        return host
    try:
        result = socket.getaddrinfo(host, port, family, socket.SOCK_DGRAM)
        if not result:
            return None
        address = result[0][4][0]
        print(f"Resolved {host}:{port} ({family.name}) to {address}")
        return address
    except socket.error:
        return None


def _resolve_nodes(nodes: list[Node]) -> None:
    for node in nodes:
        if node.ipv4:
            node.ipv4 = _resolve(node.ipv4, node.port, socket.AF_INET)
        if node.ipv6:
            node.ipv6 = _resolve(node.ipv6, node.port, socket.AF_INET6)


def main() -> None:
    nodes = _get_nodes()
    _resolve_nodes(nodes)
    with open(_NODES_JSON, "w") as f:
        json.dump(
            {
                "nodes":
                [asdict(node) for node in nodes if node.ipv4 or node.ipv6]
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
