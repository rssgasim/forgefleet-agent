"""FlashForge base adapter implementation."""

import json
from typing import Optional

import httpx

from ...logging import get_logger
from ..adapter import PrinterAdapter
from ..models import PrinterCapabilities, PrinterState, PrinterStatus

logger = get_logger(__name__)

# FlashForge protocol configuration
FLASHFORGE_HTTP_PORT = 8898
FLASHFORGE_TIMEOUT = 5.0


class FlashForgeAdapter(PrinterAdapter):
    """Base adapter for FlashForge printers."""

    MODEL = "FlashForge"
    SUPPORTED_FIRMWARE = ["5.1.8+"]

    def __init__(self, printer_info) -> None:
        """Initialize FlashForge adapter.

        Args:
            printer_info: Printer information
        """
        super().__init__(printer_info)
        self.http_client: Optional[httpx.AsyncClient] = None
        self.base_url = f"http://{printer_info.ip}:{FLASHFORGE_HTTP_PORT}"

    async def _connect(self) -> bool:
        """Connect to FlashForge printer.

        Returns:
            True if connection successful
        """
        try:
            self.http_client = httpx.AsyncClient(timeout=FLASHFORGE_TIMEOUT)

            # Test connection with version endpoint
            response = await self.http_client.get(f"{self.base_url}/api/version")
            if response.status_code == 200:
                logger.info(
                    "FlashForge connection successful",
                    printer_ip=self.printer_info.ip,
                )
                return True
            else:
                logger.error(
                    "FlashForge connection failed",
                    printer_ip=self.printer_info.ip,
                    status_code=response.status_code,
                )
                return False
        except Exception as e:
            logger.error(
                "FlashForge connection error",
                printer_ip=self.printer_info.ip,
                error=str(e),
            )
            return False

    async def _disconnect(self) -> None:
        """Disconnect from FlashForge printer."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None

    async def _get_status(self) -> PrinterStatus:
        """Get printer status from FlashForge API.

        Returns:
            Printer status
        """
        if not self.http_client:
            raise RuntimeError("Printer not connected")

        response = await self.http_client.get(f"{self.base_url}/api/status")
        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to get status: HTTP {response.status_code}"
            )

        data = response.json()
        return self._parse_status(data)

    def _parse_status(self, data: dict) -> PrinterStatus:
        """Parse FlashForge status response.

        Args:
            data: Raw status data from printer

        Returns:
            Parsed PrinterStatus
        """
        status = PrinterStatus(
            printer_id=self.printer_info.id,
            state=PrinterState.UNKNOWN,
            native_state=data.get("status", ""),
        )

        # Extract temperature data
        if "nozzle_temp" in data:
            status.nozzle_temperature = float(data["nozzle_temp"])
        if "bed_temp" in data:
            status.bed_temperature = float(data["bed_temp"])

        # Extract progress
        if "progress" in data:
            status.progress = float(data["progress"])

        # Extract current file
        if "current_file" in data:
            status.current_file = data["current_file"]

        # Extract error info
        if "error_code" in data:
            status.error_code = data["error_code"]
        if "error_msg" in data:
            status.error_message = data["error_msg"]

        return status

    async def _pause_print(self) -> bool:
        """Pause print job.

        Returns:
            True if command successful
        """
        if not self.http_client:
            raise RuntimeError("Printer not connected")

        response = await self.http_client.post(
            f"{self.base_url}/api/control",
            json={"command": "pause"},
        )
        return response.status_code == 200

    async def _resume_print(self) -> bool:
        """Resume print job.

        Returns:
            True if command successful
        """
        if not self.http_client:
            raise RuntimeError("Printer not connected")

        response = await self.http_client.post(
            f"{self.base_url}/api/control",
            json={"command": "resume"},
        )
        return response.status_code == 200

    async def _stop_print(self) -> bool:
        """Stop print job.

        Returns:
            True if command successful
        """
        if not self.http_client:
            raise RuntimeError("Printer not connected")

        response = await self.http_client.post(
            f"{self.base_url}/api/control",
            json={"command": "stop"},
        )
        return response.status_code == 200

    async def _get_capabilities(self) -> PrinterCapabilities:
        """Get printer capabilities.

        Returns:
            Printer capabilities
        """
        return PrinterCapabilities(
            printer_id=self.printer_info.id,
            supports_pause=True,
            supports_resume=True,
            supports_stop=True,
            supports_print=True,
            supports_file_transfer=False,  # Requires physical testing
            max_temperature=300.0,
            min_temperature=20.0,
            bed_max_temperature=100.0,
        )

    def _normalize_state(self, native_state: Optional[str]) -> PrinterState:
        """Normalize FlashForge state to standard state.

        Args:
            native_state: FlashForge state string

        Returns:
            Normalized PrinterState
        """
        if not native_state:
            return PrinterState.UNKNOWN

        state_lower = native_state.lower()

        # Map FlashForge states to normalized states
        state_map = {
            "offline": PrinterState.OFFLINE,
            "online": PrinterState.ONLINE,
            "idle": PrinterState.IDLE,
            "preparing": PrinterState.PREPARING,
            "printing": PrinterState.PRINTING,
            "paused": PrinterState.PAUSED,
            "completed": PrinterState.COMPLETED,
            "error": PrinterState.ERROR,
        }

        for key, value in state_map.items():
            if key in state_lower:
                return value

        return PrinterState.UNKNOWN
