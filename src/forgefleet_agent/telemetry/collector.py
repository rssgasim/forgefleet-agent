"""Telemetry collection from printers."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from ..database import Database
from ..logging import get_logger
from ..printers import PrinterRegistry
from .normalizer import TelemetryNormalizer

logger = get_logger(__name__)


class TelemetryCollector:
    """Collects telemetry from connected printers."""

    def __init__(
        self,
        printer_registry: PrinterRegistry,
        database: Database,
        interval_seconds: int = 5,
        batch_size: int = 10,
    ) -> None:
        """Initialize telemetry collector.

        Args:
            printer_registry: Printer registry instance
            database: Database instance
            interval_seconds: Collection interval
            batch_size: Batch size for sending telemetry
        """
        self.printer_registry = printer_registry
        self.database = database
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.normalizer = TelemetryNormalizer()
        self.running = False
        self.telemetry_buffer: List[Dict] = []

    async def start(self) -> None:
        """Start telemetry collection."""
        logger.info("Starting telemetry collection")
        self.running = True
        await self._collect_loop()

    async def stop(self) -> None:
        """Stop telemetry collection."""
        logger.info("Stopping telemetry collection")
        self.running = False
        # Flush any remaining telemetry
        await self._flush_telemetry()

    async def _collect_loop(self) -> None:
        """Main telemetry collection loop."""
        while self.running:
            try:
                await self._collect_once()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error("Error in telemetry collection loop", error=str(e))
                await asyncio.sleep(self.interval_seconds)

    async def _collect_once(self) -> None:
        """Collect telemetry once from all printers."""
        printers = self.printer_registry.get_all_printers()
        if not printers:
            return

        tasks = [
            self._collect_from_printer(printer_id, adapter)
            for printer_id, adapter in printers.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Check if buffer should be flushed
        if len(self.telemetry_buffer) >= self.batch_size:
            await self._flush_telemetry()

    async def _collect_from_printer(
        self, printer_id: str, adapter
    ) -> None:
        """Collect telemetry from a single printer.

        Args:
            printer_id: Printer ID
            adapter: Printer adapter instance
        """
        try:
            status = await adapter.get_status()
            telemetry = self.normalizer.normalize(status)
            self.telemetry_buffer.append(telemetry)

            # Store in database
            self.database.execute(
                """
                INSERT INTO telemetry
                (printer_id, state, progress, nozzle_temperature, bed_temperature,
                 current_file, error_code, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    telemetry.get("state"),
                    telemetry.get("progress"),
                    telemetry.get("nozzle_temperature"),
                    telemetry.get("bed_temperature"),
                    telemetry.get("current_file"),
                    telemetry.get("error_code"),
                    telemetry.get("error_message"),
                    datetime.utcnow().isoformat(),
                ),
            )

            logger.debug(
                "Telemetry collected",
                printer_id=printer_id,
                state=telemetry.get("state"),
            )
        except Exception as e:
            logger.debug(
                "Error collecting telemetry from printer",
                printer_id=printer_id,
                error=str(e),
            )

    async def _flush_telemetry(self) -> None:
        """Flush telemetry buffer."""
        if not self.telemetry_buffer:
            return

        logger.debug(
            "Flushing telemetry buffer",
            item_count=len(self.telemetry_buffer),
        )
        # In real implementation, this would send to cloud
        # For now, just clear the buffer
        self.telemetry_buffer.clear()

    def get_buffered_telemetry(self) -> List[Dict]:
        """Get current telemetry buffer.

        Returns:
            List of telemetry items
        """
        return self.telemetry_buffer.copy()
