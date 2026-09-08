"""Printer adapter base class and interface."""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..logging import get_logger
from .models import PrinterCapabilities, PrinterInfo, PrinterState, PrinterStatus

logger = get_logger(__name__)


class PrinterAdapter(ABC):
    """Abstract base class for printer adapters."""

    MODEL: str = "Unknown"
    SUPPORTED_FIRMWARE: list = []

    def __init__(self, printer_info: PrinterInfo) -> None:
        """Initialize printer adapter.

        Args:
            printer_info: Basic printer information
        """
        self.printer_info = printer_info
        self._capabilities: Optional[PrinterCapabilities] = None

    async def connect(self) -> bool:
        """Connect to printer.

        Returns:
            True if connection successful
        """
        logger.info("Connecting to printer", printer_id=self.printer_info.id)
        try:
            result = await self._connect()
            if result:
                logger.info(
                    "Connected to printer",
                    printer_id=self.printer_info.id,
                    model=self.MODEL,
                )
            return result
        except Exception as e:
            logger.error(
                "Failed to connect to printer",
                printer_id=self.printer_info.id,
                error=str(e),
            )
            return False

    async def disconnect(self) -> None:
        """Disconnect from printer."""
        logger.info("Disconnecting from printer", printer_id=self.printer_info.id)
        try:
            await self._disconnect()
        except Exception as e:
            logger.warning(
                "Error disconnecting from printer",
                printer_id=self.printer_info.id,
                error=str(e),
            )

    async def get_status(self) -> PrinterStatus:
        """Get current printer status.

        Returns:
            Current printer status
        """
        try:
            status = await self._get_status()
            # Normalize state
            status.state = self._normalize_state(status.native_state)
            return status
        except Exception as e:
            logger.error(
                "Failed to get printer status",
                printer_id=self.printer_info.id,
                error=str(e),
            )
            return PrinterStatus(
                printer_id=self.printer_info.id,
                state=PrinterState.ERROR,
                error_message=str(e),
            )

    async def pause_print(self) -> bool:
        """Pause active print job.

        Returns:
            True if command successful
        """
        logger.info("Pausing print", printer_id=self.printer_info.id)
        try:
            return await self._pause_print()
        except Exception as e:
            logger.error(
                "Failed to pause print",
                printer_id=self.printer_info.id,
                error=str(e),
            )
            return False

    async def resume_print(self) -> bool:
        """Resume paused print job.

        Returns:
            True if command successful
        """
        logger.info("Resuming print", printer_id=self.printer_info.id)
        try:
            return await self._resume_print()
        except Exception as e:
            logger.error(
                "Failed to resume print",
                printer_id=self.printer_info.id,
                error=str(e),
            )
            return False

    async def stop_print(self) -> bool:
        """Stop active print job.

        Returns:
            True if command successful
        """
        logger.info("Stopping print", printer_id=self.printer_info.id)
        try:
            return await self._stop_print()
        except Exception as e:
            logger.error(
                "Failed to stop print",
                printer_id=self.printer_info.id,
                error=str(e),
            )
            return False

    async def get_capabilities(self) -> PrinterCapabilities:
        """Get printer capabilities.

        Returns:
            Printer capabilities
        """
        if self._capabilities is None:
            try:
                self._capabilities = await self._get_capabilities()
            except Exception as e:
                logger.error(
                    "Failed to get printer capabilities",
                    printer_id=self.printer_info.id,
                    error=str(e),
                )
                self._capabilities = PrinterCapabilities(
                    printer_id=self.printer_info.id
                )
        return self._capabilities

    # Abstract methods - must be implemented by subclasses

    @abstractmethod
    async def _connect(self) -> bool:
        """Internal connection logic."""
        pass

    @abstractmethod
    async def _disconnect(self) -> None:
        """Internal disconnection logic."""
        pass

    @abstractmethod
    async def _get_status(self) -> PrinterStatus:
        """Internal status retrieval logic."""
        pass

    @abstractmethod
    async def _pause_print(self) -> bool:
        """Internal pause logic."""
        pass

    @abstractmethod
    async def _resume_print(self) -> bool:
        """Internal resume logic."""
        pass

    @abstractmethod
    async def _stop_print(self) -> bool:
        """Internal stop logic."""
        pass

    @abstractmethod
    async def _get_capabilities(self) -> PrinterCapabilities:
        """Internal capabilities retrieval logic."""
        pass

    @abstractmethod
    def _normalize_state(self, native_state: Optional[str]) -> PrinterState:
        """Normalize printer-specific state to standard state.

        Args:
            native_state: Printer-specific state string

        Returns:
            Normalized PrinterState
        """
        pass
