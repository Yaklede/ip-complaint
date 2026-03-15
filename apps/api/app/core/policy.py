from __future__ import annotations

from ipaddress import ip_address, ip_network


EXTERNAL_UNKNOWN_DISPLAY_NAME = "성명불상"
EXTERNAL_UNKNOWN_GRADE = "D"
EXTERNAL_UNKNOWN_NEXT_STEP = "통신사/플랫폼/수사기관 조회 필요"


def is_external_public_ip(value: str | None) -> bool:
    if not value:
        return False

    parsed = ip_address(value)
    internal_networks = (
        ip_network("10.0.0.0/8"),
        ip_network("172.16.0.0/12"),
        ip_network("192.168.0.0/16"),
        ip_network("fc00::/7"),
    )
    is_internal_range = any(parsed in network for network in internal_networks)
    return not (
        is_internal_range
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_multicast
        or parsed.is_unspecified
    )
