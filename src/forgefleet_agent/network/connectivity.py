"""Network connectivity management."""

import asyncio
from typing import Optional

import httpx

from ..logging import get_logger

logger = get_logger(__name__)


class ConnectivityChecker:
    """Checks network connectivity."""

    # Common public DNS services to check
    CONNECTIVITY_CHECKS = [
        "https://api.github.com",
        "https://8.8.8.8",
        "https://1.1.1.1",
    ]

    @staticmethod
    async def check_internet_connectivity(timeout_seconds: int = 5) -> bool:
        """Check if device has internet connectivity.

        Args:
            timeout_seconds: Timeout for connectivity check

        Returns:
            True if internet connectivity available
        """
        logger.debug("Checking internet connectivity")

        for check_url in ConnectivityChecker.CONNECTIVITY_CHECKS:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.head(
                        check_url, timeout=timeout_seconds, verify=False
                    )
                    if response.status_code < 500:
                        logger.debug("Internet connectivity confirmed")
                        return True
            except Exception:
                pass

        logger.warning("No internet connectivity detected")
        return False

    @staticmethod
    async def check_cloud_connectivity(
        api_url: str, timeout_seconds: int = 5
    ) -> bool:
        """Check connectivity to ForgeFleet Cloud API.

        Args:
            api_url: ForgeFleet API URL
            timeout_seconds: Timeout for connectivity check

        Returns:
            True if cloud connectivity available
        """
        logger.debug("Checking cloud connectivity", api_url=api_url)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.head(
                    api_url, timeout=timeout_seconds
                )
                is_reachable = response.status_code < 500
                if is_reachable:
                    logger.debug("Cloud connectivity confirmed")
                else:
                    logger.warning(
                        "Cloud returned error",
                        status_code=response.status_code,
                    )
                return is_reachable
        except Exception as e:
            logger.warning("Cloud connectivity failed", error=str(e))
            return False

    @staticmethod
    async def check_printer_connectivity(
        printer_ip: str, port: int = 8898, timeout_seconds: int = 5
    ) -> bool:
        """Check connectivity to a printer.

        Args:
            printer_ip: Printer IP address
            port: Printer port (default FlashForge HTTP port)
            timeout_seconds: Timeout for connectivity check

        Returns:
            True if printer is reachable
        """
        logger.debug("Checking printer connectivity", printer_ip=printer_ip)

        try:
            async with httpx.AsyncClient() as client:
                url = f"http://{printer_ip}:{port}/api/version"
                response = await client.get(url, timeout=timeout_seconds)
                is_reachable = response.status_code == 200
                if is_reachable:
                    logger.debug("Printer connectivity confirmed")
                return is_reachable
        except Exception as e:
            logger.debug("Printer connectivity failed", error=str(e))
            return False
