"""FlashForge printer discovery over local network."""

import asyncio
import ipaddress
from typing import Dict, List, Optional

from ..logging import get_logger
from .interfaces import NetworkInterface, NetworkDetector
from .subnet import SubnetCalculator

logger = get_logger(__name__)


class PrinterDiscoveryEngine:
    """Discovers FlashForge printers on local network."""

    # Known FlashForge default ports
    FLASHFORGE_HTTP_PORT = 8898
    FLASHFORGE_TCP_PORT = 8899

    def __init__(self, timeout_seconds: int = 5) -> None:
        """Initialize discovery engine.

        Args:
            timeout_seconds: Timeout for each discovery attempt
        """
        self.timeout_seconds = timeout_seconds
        self.network_detector = NetworkDetector()
        self.discovered_printers: Dict[str, Dict] = {}

    async def discover_printers(self) -> Dict[str, Dict]:
        """Discover all FlashForge printers on active networks.

        Returns:
            Dictionary of discovered printers {printer_id: printer_info}
        """
        logger.info("Starting printer discovery")

        # Detect active network interfaces
        interfaces = await self.network_detector.detect_interfaces()
        active_interfaces = self.network_detector.get_active_interfaces()

        if not active_interfaces:
            logger.warning("No active network interfaces found")
            return {}

        logger.info(
            "Found active interfaces",
            count=len(active_interfaces),
            interfaces=[i.name for i in active_interfaces],
        )

        # Scan each subnet
        discovered = {}
        for interface in active_interfaces:
            subnet_printers = await self._scan_subnet(interface)
            discovered.update(subnet_printers)

        self.discovered_printers = discovered
        logger.info("Discovery complete", printers_found=len(discovered))
        return discovered

    async def _scan_subnet(self, interface: NetworkInterface) -> Dict[str, Dict]:
        """Scan a single subnet for printers.

        Args:
            interface: Network interface to scan

        Returns:
            Dictionary of printers found on this subnet
        """
        if not interface.subnet:
            logger.warning(
                "Cannot scan interface without subnet",
                interface=interface.name,
            )
            return {}

        logger.info(
            "Scanning subnet",
            interface=interface.name,
            subnet=interface.subnet,
        )

        network = SubnetCalculator.parse_network(
            interface.ipv4_address, interface.ipv4_netmask
        )
        if not network:
            return {}

        # Generate list of IPs to check
        ips_to_check = list(SubnetCalculator.generate_ips(network))
        logger.debug(
            "Generated IP list",
            interface=interface.name,
            ip_count=len(ips_to_check),
        )

        # Scan IPs concurrently
        printers = {}
        tasks = [
            self._check_ip(ip, interface.name) for ip in ips_to_check
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict) and result:
                printer_id = result.get("id")
                if printer_id:
                    printers[printer_id] = result
                    logger.info(
                        "Printer discovered",
                        printer_id=printer_id,
                        model=result.get("model"),
                        ip=result.get("ip"),
                    )

        return printers

    async def _check_ip(self, ip: str, interface_name: str) -> Optional[Dict]:
        """Check if IP is a FlashForge printer.

        Args:
            ip: IP address to check
            interface_name: Name of interface being scanned

        Returns:
            Printer info if found, None otherwise
        """
        try:
            # Try to connect to FlashForge HTTP port
            result = await asyncio.wait_for(
                self._probe_flashforge_http(ip),
                timeout=self.timeout_seconds,
            )
            if result:
                result["interface"] = interface_name
                return result
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.debug(f"Error checking IP {ip}: {e}")

        return None

    async def _probe_flashforge_http(self, ip: str) -> Optional[Dict]:
        """Probe FlashForge HTTP API.

        Args:
            ip: IP address to probe

        Returns:
            Printer info if valid FlashForge printer found
        """
        import httpx

        url = f"http://{ip}:{self.FLASHFORGE_HTTP_PORT}/api/version"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout_seconds)

            if response.status_code == 200:
                # Parse FlashForge response
                return self._parse_printer_response(ip, response.text)
        except Exception:
            pass

        return None

    def _parse_printer_response(self, ip: str, response_text: str) -> Optional[Dict]:
        """Parse FlashForge API response.

        Args:
            ip: IP address of printer
            response_text: Response from printer API

        Returns:
            Parsed printer information or None
        """
        try:
            import json
            data = json.loads(response_text)
            
            # FlashForge returns model info
            model = data.get("model", "Unknown")
            serial = data.get("serial_number", "")
            firmware = data.get("version", "")

            # Validate it's a supported model
            if not self._is_supported_model(model):
                logger.debug(f"Unsupported printer model: {model}")
                return None

            printer_id = f"{model}-{serial}" if serial else f"{model}-{ip.replace('.', '')}"

            return {
                "id": printer_id,
                "ip": ip,
                "model": model,
                "serial_number": serial,
                "firmware_version": firmware,
                "status": "ONLINE",
            }
        except Exception as e:
            logger.debug(f"Failed to parse printer response: {e}")
            return None

    def _is_supported_model(self, model: str) -> bool:
        """Check if printer model is supported.

        Args:
            model: Printer model string

        Returns:
            True if model is supported
        """
        supported_models = ["AD5M", "AD5X", "Adventurer", "Guider"]
        return any(m.lower() in model.lower() for m in supported_models)

    def get_discovered_printers(self) -> Dict[str, Dict]:
        """Get previously discovered printers.

        Returns:
            Dictionary of discovered printers
        """
        return self.discovered_printers
