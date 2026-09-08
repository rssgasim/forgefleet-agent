"""Subnet and IP address utilities."""

import ipaddress
from typing import Generator, List, Optional, Tuple

from ..logging import get_logger

logger = get_logger(__name__)


class SubnetCalculator:
    """Calculates subnet information."""

    @staticmethod
    def parse_network(ip_address: str, netmask: str) -> Optional[ipaddress.IPv4Network]:
        """Parse IP and netmask into network object."""
        try:
            network = ipaddress.IPv4Network(
                f"{ip_address}/{netmask}", strict=False
            )
            return network
        except (ipaddress.AddressValueError, ValueError) as e:
            logger.warning(
                "Failed to parse network",
                ip=ip_address,
                netmask=netmask,
                error=str(e),
            )
            return None

    @staticmethod
    def get_network_range(
        network: ipaddress.IPv4Network,
    ) -> Tuple[ipaddress.IPv4Address, ipaddress.IPv4Address]:
        """Get first and last usable addresses in network."""
        return network.network_address + 1, network.broadcast_address - 1

    @staticmethod
    def generate_ips(
        network: ipaddress.IPv4Network, exclude_gateway: bool = True
    ) -> Generator[str, None, None]:
        """Generate all usable IPs in network."""
        start, end = SubnetCalculator.get_network_range(network)
        for ip in range(int(start), int(end) + 1):
            yield str(ipaddress.IPv4Address(ip))

    @staticmethod
    def ip_in_subnet(ip_address: str, subnet: str) -> bool:
        """Check if IP is in subnet."""
        try:
            ip = ipaddress.IPv4Address(ip_address)
            network = ipaddress.IPv4Network(subnet, strict=False)
            return ip in network
        except (ipaddress.AddressValueError, ValueError):
            return False
