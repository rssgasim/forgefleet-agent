"""Network interface detection and management."""

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

from ..logging import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkInterface:
    """Represents a network interface."""

    name: str
    status: str  # UP, DOWN
    ipv4_address: Optional[str] = None
    ipv4_netmask: Optional[str] = None
    gateway: Optional[str] = None
    interface_type: str = "UNKNOWN"  # Ethernet, Wi-Fi, etc.

    @property
    def subnet(self) -> Optional[str]:
        """Calculate subnet from IP and netmask."""
        if not self.ipv4_address or not self.ipv4_netmask:
            return None
        try:
            network = ipaddress.IPv4Network(
                f"{self.ipv4_address}/{self.ipv4_netmask}", strict=False
            )
            return str(network)
        except (ipaddress.AddressValueError, ValueError) as e:
            logger.warning("Failed to calculate subnet", error=str(e))
            return None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status,
            "ipv4_address": self.ipv4_address,
            "ipv4_netmask": self.ipv4_netmask,
            "subnet": self.subnet,
            "gateway": self.gateway,
            "interface_type": self.interface_type,
        }


class NetworkDetector:
    """Detects and manages network interfaces."""

    def __init__(self) -> None:
        """Initialize network detector."""
        self.interfaces: Dict[str, NetworkInterface] = {}

    async def detect_interfaces(self) -> Dict[str, NetworkInterface]:
        """Detect all active network interfaces."""
        logger.info("Detecting network interfaces")

        if psutil is None:
            logger.warning("psutil not available, using socket-based detection")
            return await self._detect_interfaces_socket()

        return await self._detect_interfaces_psutil()

    async def _detect_interfaces_psutil(self) -> Dict[str, NetworkInterface]:
        """Detect interfaces using psutil."""
        try:
            interfaces = {}
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            for interface_name, addrs in net_if_addrs.items():
                stats = net_if_stats.get(interface_name)
                if not stats:
                    continue

                ipv4_address = None
                ipv4_netmask = None

                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        ipv4_address = addr.address
                        ipv4_netmask = addr.netmask
                        break

                if ipv4_address:
                    interface = NetworkInterface(
                        name=interface_name,
                        status="UP" if stats.isup else "DOWN",
                        ipv4_address=ipv4_address,
                        ipv4_netmask=ipv4_netmask,
                        interface_type=self._detect_interface_type(interface_name),
                    )
                    interfaces[interface_name] = interface
                    logger.info(
                        "Interface detected",
                        name=interface_name,
                        ip=ipv4_address,
                        subnet=interface.subnet,
                        status=interface.status,
                    )

            self.interfaces = interfaces
            return interfaces
        except Exception as e:
            logger.error("Failed to detect interfaces", error=str(e))
            return {}

    async def _detect_interfaces_socket(self) -> Dict[str, NetworkInterface]:
        """Fallback interface detection using socket."""
        interfaces = {}
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            interface = NetworkInterface(
                name="Default",
                status="UP",
                ipv4_address=ip_address,
                ipv4_netmask="255.255.255.0",  # Assume Class C
                interface_type="UNKNOWN",
            )
            interfaces["Default"] = interface
            logger.info("Default interface detected", ip=ip_address)
        except Exception as e:
            logger.error("Failed to detect default interface", error=str(e))

        return interfaces

    def _detect_interface_type(self, interface_name: str) -> str:
        """Detect interface type from name."""
        name_lower = interface_name.lower()
        if "ethernet" in name_lower or "eth" in name_lower:
            return "Ethernet"
        elif "wifi" in name_lower or "wlan" in name_lower or "wireless" in name_lower:
            return "Wi-Fi"
        elif "vpn" in name_lower or "tap" in name_lower:
            return "VPN"
        return "Unknown"

    def get_active_interfaces(self) -> List[NetworkInterface]:
        """Get all active interfaces."""
        return [iface for iface in self.interfaces.values() if iface.status == "UP"]

    def get_interface_by_name(self, name: str) -> Optional[NetworkInterface]:
        """Get interface by name."""
        return self.interfaces.get(name)

    def get_subnets(self) -> List[str]:
        """Get all active subnets."""
        subnets = []
        for iface in self.get_active_interfaces():
            if iface.subnet:
                subnets.append(iface.subnet)
        return subnets
