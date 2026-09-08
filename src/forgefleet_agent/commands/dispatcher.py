"""Command dispatcher and execution."""

from typing import Any, Callable, Dict, Optional

from ..logging import get_logger
from ..printers import PrinterRegistry
from ..cloud.models import CommandResult

logger = get_logger(__name__)


class CommandDispatcher:
    """Dispatches commands to printer adapters."""

    def __init__(self, printer_registry: PrinterRegistry) -> None:
        """Initialize command dispatcher.

        Args:
            printer_registry: Printer registry instance
        """
        self.printer_registry = printer_registry
        self.command_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default command handlers."""
        self.register_handler("PAUSE_PRINT", self._handle_pause_print)
        self.register_handler("RESUME_PRINT", self._handle_resume_print)
        self.register_handler("STOP_PRINT", self._handle_stop_print)
        self.register_handler("REFRESH_STATUS", self._handle_refresh_status)
        self.register_handler("REFRESH_TELEMETRY", self._handle_refresh_telemetry)
        self.register_handler("DISCOVER_PRINTERS", self._handle_discover_printers)

    def register_handler(
        self, command_type: str, handler: Callable
    ) -> None:
        """Register a command handler.

        Args:
            command_type: Type of command
            handler: Async handler function
        """
        self.command_handlers[command_type.upper()] = handler
        logger.debug("Registered command handler", command_type=command_type)

    async def dispatch(
        self,
        command_id: str,
        command_type: str,
        printer_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CommandResult:
        """Dispatch a command to a printer.

        Args:
            command_id: Unique command ID
            command_type: Type of command
            printer_id: Target printer ID
            parameters: Command parameters

        Returns:
            Command result
        """
        logger.info(
            "Dispatching command",
            command_id=command_id,
            command_type=command_type,
            printer_id=printer_id,
        )

        handler = self.command_handlers.get(command_type.upper())
        if not handler:
            logger.warning(
                "Unknown command type",
                command_type=command_type,
            )
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="UNKNOWN_COMMAND",
                error_message=f"Unknown command type: {command_type}",
            )

        try:
            result = await handler(command_id, printer_id, parameters or {})
            logger.info(
                "Command executed",
                command_id=command_id,
                success=result.success,
            )
            return result
        except Exception as e:
            logger.error(
                "Error executing command",
                command_id=command_id,
                error=str(e),
            )
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="EXECUTION_ERROR",
                error_message=str(e),
            )

    # Command handlers

    async def _handle_pause_print(
        self,
        command_id: str,
        printer_id: str,
        parameters: Dict[str, Any],
    ) -> CommandResult:
        """Handle pause print command."""
        adapter = self.printer_registry.get_printer(printer_id)
        if not adapter:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="PRINTER_NOT_FOUND",
                error_message="Printer not found",
            )

        capabilities = await adapter.get_capabilities()
        if not capabilities.supports_pause:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="NOT_SUPPORTED",
                error_message="Printer does not support pause",
            )

        success = await adapter.pause_print()
        return CommandResult(
            command_id=command_id,
            printer_id=printer_id,
            success=success,
        )

    async def _handle_resume_print(
        self,
        command_id: str,
        printer_id: str,
        parameters: Dict[str, Any],
    ) -> CommandResult:
        """Handle resume print command."""
        adapter = self.printer_registry.get_printer(printer_id)
        if not adapter:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="PRINTER_NOT_FOUND",
                error_message="Printer not found",
            )

        capabilities = await adapter.get_capabilities()
        if not capabilities.supports_resume:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="NOT_SUPPORTED",
                error_message="Printer does not support resume",
            )

        success = await adapter.resume_print()
        return CommandResult(
            command_id=command_id,
            printer_id=printer_id,
            success=success,
        )

    async def _handle_stop_print(
        self,
        command_id: str,
        printer_id: str,
        parameters: Dict[str, Any],
    ) -> CommandResult:
        """Handle stop print command."""
        adapter = self.printer_registry.get_printer(printer_id)
        if not adapter:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="PRINTER_NOT_FOUND",
                error_message="Printer not found",
            )

        capabilities = await adapter.get_capabilities()
        if not capabilities.supports_stop:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="NOT_SUPPORTED",
                error_message="Printer does not support stop",
            )

        success = await adapter.stop_print()
        return CommandResult(
            command_id=command_id,
            printer_id=printer_id,
            success=success,
        )

    async def _handle_refresh_status(
        self,
        command_id: str,
        printer_id: str,
        parameters: Dict[str, Any],
    ) -> CommandResult:
        """Handle refresh status command."""
        adapter = self.printer_registry.get_printer(printer_id)
        if not adapter:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="PRINTER_NOT_FOUND",
                error_message="Printer not found",
            )

        status = await adapter.get_status()
        return CommandResult(
            command_id=command_id,
            printer_id=printer_id,
            success=True,
            result_data=status.to_dict(),
        )

    async def _handle_refresh_telemetry(
        self,
        command_id: str,
        printer_id: str,
        parameters: Dict[str, Any],
    ) -> CommandResult:
        """Handle refresh telemetry command."""
        adapter = self.printer_registry.get_printer(printer_id)
        if not adapter:
            return CommandResult(
                command_id=command_id,
                printer_id=printer_id,
                success=False,
                error_code="PRINTER_NOT_FOUND",
                error_message="Printer not found",
            )

        status = await adapter.get_status()
        return CommandResult(
            command_id=command_id,
            printer_id=printer_id,
            success=True,
            result_data=status.to_dict(),
        )

    async def _handle_discover_printers(
        self,
        command_id: str,
        printer_id: str,
        parameters: Dict[str, Any],
    ) -> CommandResult:
        """Handle discover printers command."""
        # This would be handled by the main agent
        return CommandResult(
            command_id=command_id,
            printer_id=printer_id,
            success=True,
            result_data={"message": "Discovery initiated"},
        )
