from __future__ import annotations

import ipaddress
import socket
from typing import Optional, Tuple


def is_private_host(host: str) -> bool:
    host = host.strip().lower().rstrip(".")
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".localhost"):
        return True
    # Honor explicit IPv6 / cloud metadata sinks.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        return bool(ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False
    for fam, st, proto, cannon, sockaddr in infos:
        ipstr = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ipstr)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return True
    return False


def validate_public_host(domain: str) -> Tuple[bool, str]:
    domain = domain.strip().strip("/")
    if "://" in domain:
        domain = domain.split("://", 1)[1].split("/", 1)[0]
    if "/" in domain or "@" in domain:
        return False, "invalid host"
    if is_private_host(domain):
        return False, "private or internal host denied"
    return True, domain


def validate_http_url(url: str) -> Tuple[bool, str]:
    url = url.strip()
    if not (url.lower().startswith("http://") or url.lower().startswith("https://")):
        return False, "only http(s) urls supported"
    try:
        host = url.split("://", 1)[1].split("/", 1)[0]
    except Exception:
        return False, "invalid url"
    if not host:
        return False, "missing host"
    if is_private_host(host):
        return False, "private or internal host denied"
    return True, url
