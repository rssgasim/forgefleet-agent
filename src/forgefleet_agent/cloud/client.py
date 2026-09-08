"""ForgeFleet Cloud API client."""

import json
from typing import Any, Dict, Optional

import httpx

from ..logging import get_logger
from .authentication import CloudAuthenticator
from .models import AgentRegistration, CommandResult, Heartbeat, PrinterEvent, TelemetryData

logger = get_logger(__name__)


class CloudAPIClient:
    """Client for ForgeFleet Cloud API."""

    def __init__(
        self,
        api_url: str,
        agent_token: Optional[str] = None,
        timeout_seconds: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize cloud API client.

        Args:
            api_url: ForgeFleet Cloud API base URL
            agent_token: Agent authentication token
            timeout_seconds: HTTP request timeout
            verify_ssl: Verify SSL certificates
        """
        self.api_url = api_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.verify_ssl = verify_ssl
        self.authenticator = CloudAuthenticator(agent_token)
        self.http_client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Connect to cloud API.

        Returns:
            True if connection successful
        """
        try:
            self.http_client = httpx.AsyncClient(
                timeout=self.timeout_seconds,
                verify=self.verify_ssl,
            )
            logger.info("Connected to cloud API", api_url=self.api_url)
            return True
        except Exception as e:
            logger.error("Failed to connect to cloud API", error=str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from cloud API."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
            logger.info("Disconnected from cloud API")

    async def register_agent(
        self, registration: AgentRegistration
    ) -> bool:
        """Register agent with cloud.

        Args:
            registration: Agent registration data

        Returns:
            True if registration successful
        """
        if not self.http_client:
            logger.error("Not connected to cloud API")
            return False

        try:
            response = await self.http_client.post(
                f"{self.api_url}/agent/register",
                json=registration.to_dict(),
                headers=self.authenticator.get_headers(),
            )
            if response.status_code in (200, 201):
                logger.info("Agent registered successfully")
                return True
            else:
                logger.error(
                    "Agent registration failed",
                    status_code=response.status_code,
                    response=response.text,
                )
                return False
        except Exception as e:
            logger.error("Error registering agent", error=str(e))
            return False

    async def send_heartbeat(self, heartbeat: Heartbeat) -> bool:
        """Send heartbeat to cloud.

        Args:
            heartbeat: Heartbeat data

        Returns:
            True if heartbeat sent successfully
        """
        if not self.http_client:
            return False

        try:
            response = await self.http_client.post(
                f"{self.api_url}/agent/heartbeat",
                json=heartbeat.to_dict(),
                headers=self.authenticator.get_headers(),
            )
            if response.status_code == 200:
                logger.debug("Heartbeat sent successfully")
                return True
            else:
                logger.warning(
                    "Heartbeat failed",
                    status_code=response.status_code,
                )
                return False
        except Exception as e:
            logger.debug("Error sending heartbeat", error=str(e))
            return False

    async def send_printer_event(
        self, event: PrinterEvent
    ) -> bool:
        """Send printer event to cloud.

        Args:
            event: Printer event data

        Returns:
            True if event sent successfully
        """
        if not self.http_client:
            return False

        try:
            response = await self.http_client.post(
                f"{self.api_url}/agent/events",
                json=event.to_dict(),
                headers=self.authenticator.get_headers(),
            )
            if response.status_code in (200, 201):
                logger.debug(
                    "Printer event sent",
                    event_type=event.event_type,
                )
                return True
            else:
                logger.warning(
                    "Printer event failed",
                    status_code=response.status_code,
                )
                return False
        except Exception as e:
            logger.debug("Error sending printer event", error=str(e))
            return False

    async def send_telemetry(
        self, telemetry_list: list
    ) -> bool:
        """Send telemetry data to cloud.

        Args:
            telemetry_list: List of telemetry data points

        Returns:
            True if telemetry sent successfully
        """
        if not self.http_client:
            return False

        try:
            payload = {
                "telemetry": [
                    t.to_dict() if hasattr(t, "to_dict") else t
                    for t in telemetry_list
                ]
            }
            response = await self.http_client.post(
                f"{self.api_url}/agent/telemetry",
                json=payload,
                headers=self.authenticator.get_headers(),
            )
            if response.status_code in (200, 201):
                logger.debug(
                    "Telemetry sent",
                    count=len(telemetry_list),
                )
                return True
            else:
                logger.warning(
                    "Telemetry send failed",
                    status_code=response.status_code,
                )
                return False
        except Exception as e:
            logger.debug("Error sending telemetry", error=str(e))
            return False

    async def send_command_result(
        self, result: CommandResult
    ) -> bool:
        """Send command result to cloud.

        Args:
            result: Command result data

        Returns:
            True if result sent successfully
        """
        if not self.http_client:
            return False

        try:
            response = await self.http_client.post(
                f"{self.api_url}/agent/command-result",
                json=result.to_dict(),
                headers=self.authenticator.get_headers(),
            )
            if response.status_code == 200:
                logger.debug(
                    "Command result sent",
                    command_id=result.command_id,
                )
                return True
            else:
                logger.warning(
                    "Command result send failed",
                    status_code=response.status_code,
                )
                return False
        except Exception as e:
            logger.debug("Error sending command result", error=str(e))
            return False
