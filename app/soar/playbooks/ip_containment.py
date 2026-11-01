
"""Validation for temporary IP containment playbooks."""

from dataclasses import dataclass
from ipaddress import ip_address, ip_network


# Infrastructure addresses that must never be blocked.
PROTECTED_NETWORKS = tuple(
    ip_network(network)
    for network in (
        "10.20.0.0/16",  # AWS infrastructure
        "10.30.0.0/24",  # On-premises infrastructure
        "10.40.0.0/30",  # WireGuard tunnel
        "127.0.0.0/8",   # Loopback
        "169.254.0.0/16",  # Link-local / metadata
    )
)


@dataclass(frozen=True)
class ContainmentDecision:
    approved: bool
    ip: str
    duration_seconds: int
    reason: str


def validate_containment(
        source_ip: str,
        duration_seconds: int = 300,
) -> ContainmentDecision:
    """Validate a requested temporary IP block.

    This function only makes a decision.
    It never modifies firewall rules.
    """

    try:
        address = ip_address(source_ip)
    except ValueError:
        return ContainmentDecision(
            False, source_ip, duration_seconds,
            "Invalid IP address.",
        )

    if address.version != 4:
        return ContainmentDecision(
            False, source_ip, duration_seconds,
            "Only IPv4 containment is supported.",
        )

    if not address.is_global:
        return ContainmentDecision(
            False, source_ip, duration_seconds,
            "Non-public address is protected.",
        )

    if any(address in network for network in PROTECTED_NETWORKS):
        return ContainmentDecision(
            False, source_ip, duration_seconds,
            "Infrastructure address is protected.",
        )

    if not 60 <= duration_seconds <= 900:
        return ContainmentDecision(
            False, source_ip, duration_seconds,
            "Duration must be between 60 and 900 seconds.",
        )

    return ContainmentDecision(
        True, str(address), duration_seconds,
        "Address passed containment safety checks.",
    )
