"""Main ForgeFleet Agent implementation."""

import asyncio
import platform
import socket
import uuid
from datetime import datetime
from typing import Dict, Optional

from .cloud import CloudAPIClient, CloudWebSocketClient, AgentRegistration, Heartbeat
from .commands import CommandDispatcher
from .config import settings
from .database import Database
from .logging import get_logger, setup_logging
from .network import PrinterDiscoveryEngine
from .printers import (
    PrinterRegistry,
    FlashForgeAD5MAdapter,
    FlashForgeAD5XAdapter,
    PrinterInfo,
    PrinterState,
)
from .telemetry import TelemetryCollector

logger = get_logger(__name__)


class Agent:
    """ForgeFleet Agent - Main application class."""

    def __init__(self) -> None:
        """Initialize the Agent."""
        setup_logging()
        logger.info(
            "Initializing ForgeFleet Agent",
            version="1.0.0",
        )

        # Initialize components
        self.settings = settings
        self.database = Database(settings.database_path)
        self.printer_registry = PrinterRegistry()
        self.discovery_engine = PrinterDiscoveryEngine(
            timeout_seconds=settings.discovery_timeout_seconds
        )
        self.telemetry_collector = TelemetryCollector(
            self.printer_registry,
            self.database,
            interval_seconds=settings.telemetry_interval_seconds,
            batch_size=settings.telemetry_batch_size,
        )
        self.command_dispatcher = CommandDispatcher(self.printer_registry)
        self.cloud_client = CloudAPIClient(
            settings.forgefleet_api_url,
            agent_token=settings.forgefleet_agent_token,
        )

        # Agent state
        self.agent_id = self._get_or_create_agent_id()
        self.running = False

        # Register printer adapters
        self._register_printer_adapters()

    def _get_or_create_agent_id(self) -> str:
        """Get or create persistent agent ID.

        Returns:
            Agent ID
        """
        row = self.database.fetch_one(
            "SELECT value FROM configuration WHERE key = 'agent_id'"
        )
        if row:
            agent_id = row["value"]
            logger.info("Loaded existing agent ID", agent_id=agent_id)
        else:
            agent_id = str(uuid.uuid4())
            self.database.execute(
                "INSERT INTO configuration (key, value) VALUES (?, ?)",
                ("agent_id", agent_id),
            )
            logger.info("Created new agent ID", agent_id=agent_id)
        return agent_id

    def _register_printer_adapters(self) -> None:
        """Register printer model adapters."""
        self.printer_registry.register_adapter("AD5M", FlashForgeAD5MAdapter)
        self.printer_registry.register_adapter("AD5X", FlashForgeAD5XAdapter)
        logger.info(
            "Registered printer adapters",
            supported_models=self.printer_registry.list_supported_models(),
        )

    async def start(self) -> None:
        """Start the Agent."""
        logger.info("Starting ForgeFleet Agent")
        self.running = True

        try:
            # Connect to cloud
            if not await self.cloud_client.connect():
                logger.warning("Failed to connect to cloud initially")

            # Register agent
            registration = AgentRegistration(
                agent_id=self.agent_id,
                agent_name=self.settings.agent_name,
                workspace_id=self.settings.workspace_id or "default",
                hostname=socket.gethostname(),
            )
            if not await self.cloud_client.register_agent(registration):
                logger.warning("Failed to register agent with cloud")

            # Start background tasks
            tasks = [
                asyncio.create_task(self._discovery_loop()),
                asyncio.create_task(self._heartbeat_loop()),
                asyncio.create_task(self.telemetry_collector.start()),
            ]

            # Wait for tasks
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error("Error starting agent", error=str(e))
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the Agent."""
        logger.info("Stopping ForgeFleet Agent")
        self.running = False

        # Disconnect from printers
        for printer_id, adapter in self.printer_registry.get_all_printers().items():
            try:
                await adapter.disconnect()
            except Exception as e:
                logger.warning(
                    "Error disconnecting printer",
                    printer_id=printer_id,
                    error=str(e),
                )

        # Stop telemetry
        await self.telemetry_collector.stop()

        # Disconnect from cloud
        await self.cloud_client.disconnect()

        logger.info("Agent stopped")

    async def _discovery_loop(self) -> None:
        """Main printer discovery loop."""
        while self.running:
            try:
                logger.debug("Starting discovery scan")
                discovered = await self.discovery_engine.discover_printers()

                # Process discovered printers
                for printer_id, printer_data in discovered.items():
                    await self._process_discovered_printer(printer_id, printer_data)

                # Check for offline printers
                await self._check_offline_printers(discovered)

                # Wait for next discovery interval
                await asyncio.sleep(
                    self.settings.discovery_interval_seconds
                )
            except Exception as e:
                logger.error("Error in discovery loop", error=str(e))
                await asyncio.sleep(self.settings.discovery_interval_seconds)

    async def _process_discovered_printer(
        self, printer_id: str, printer_data: Dict
    ) -> None:
        """Process a newly discovered printer.

        Args:
            printer_id: Printer ID
            printer_data: Printer information
        """
        logger.info(
            "Processing discovered printer",
            printer_id=printer_id,
            model=printer_data.get("model"),
        )

        # Check if printer already registered
        existing = self.database.get_printer(printer_id)
        if existing:
            # Update existing printer
            printer_data["updated_at"] = datetime.utcnow().isoformat()
            self.database.save_printer(printer_data)
            logger.debug("Updated existing printer", printer_id=printer_id)
            return

        # Create new printer instance
        printer_info = PrinterInfo(
            id=printer_id,
            ip=printer_data["ip"],
            model=printer_data["model"],
            serial_number=printer_data.get("serial_number"),
            firmware_version=printer_data.get("firmware_version"),
            status=PrinterState.ONLINE,
            workspace_id=self.settings.workspace_id,
        )

        adapter = self.printer_registry.create_printer(printer_info)
        if not adapter:
            logger.warning(
                "Unsupported printer model",
                model=printer_data.get("model"),
            )
            return

        # Try to connect
        if await adapter.connect():
            self.database.save_printer(printer_info.to_dict())
            logger.info(
                "Printer added to registry",
                printer_id=printer_id,
            )
            # Notify cloud
            await self._notify_printer_online(printer_info)
        else:
            logger.warning(
                "Failed to connect to printer",
                printer_id=printer_id,
            )

    async def _check_offline_printers(
        self, discovered: Dict
    ) -> None:
        """Check for printers that went offline.

        Args:
            discovered: Dictionary of currently discovered printers
        """
        for printer_id, adapter in self.printer_registry.get_all_printers().items():
            if printer_id not in discovered:
                logger.info(
                    "Printer offline",
                    printer_id=printer_id,
                )
                # Update database
                self.database.execute(
                    "UPDATE printers SET status = ? WHERE id = ?",
                    (PrinterState.OFFLINE.value, printer_id),
                )
                # Notify cloud
                await self._notify_printer_offline(printer_id)

    async def _heartbeat_loop(self) -> None:
        """Main heartbeat loop."""
        while self.running:
            try:
                printers = self.printer_registry.get_all_printers()
                online_count = sum(
                    1 for adapter in printers.values()
                    if adapter.printer_info.status == PrinterState.ONLINE
                )

                heartbeat = Heartbeat(
                    agent_id=self.agent_id,
                    printer_count=len(printers),
                    online_printers=online_count,
                )
                await self.cloud_client.send_heartbeat(heartbeat)

                await asyncio.sleep(
                    self.settings.cloud_heartbeat_interval_seconds
                )
            except Exception as e:
                logger.debug("Error sending heartbeat", error=str(e))
                await asyncio.sleep(
                    self.settings.cloud_heartbeat_interval_seconds
                )

    async def _notify_printer_online(
        self, printer_info: PrinterInfo
    ) -> None:
        """Notify cloud that printer is online.

        Args:
            printer_info: Printer information
        """
        from .cloud import PrinterEvent
        event = PrinterEvent(
            event_type="ONLINE",
            printer_id=printer_info.id,
            printer_data=printer_info.to_dict(),
        )
        await self.cloud_client.send_printer_event(event)

    async def _notify_printer_offline(self, printer_id: str) -> None:
        """Notify cloud that printer is offline.

        Args:
            printer_id: Printer ID
        """
        from .cloud import PrinterEvent
        printer = self.database.get_printer(printer_id)
        if printer:
            event = PrinterEvent(
                event_type="OFFLINE",
                printer_id=printer_id,
                printer_data=printer,
            )
            await self.cloud_client.send_printer_event(event)


async def main() -> None:
    """Main entry point."""
    agent = Agent()
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await agent.stop()
    except Exception as e:
        logger.critical("Fatal error", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
