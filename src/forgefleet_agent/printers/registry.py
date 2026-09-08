"""Printer registry for managing printer instances."""

from typing import Dict, Optional, Type

from ..logging import get_logger
from .adapter import PrinterAdapter
from .models import PrinterInfo

logger = get_logger(__name__)


class PrinterRegistry:
    """Registry for printer adapters."""

    def __init__(self) -> None:
        """Initialize printer registry."""
        self.printers: Dict[str, PrinterAdapter] = {}
        self.adapter_classes: Dict[str, Type[PrinterAdapter]] = {}

    def register_adapter(
        self, model: str, adapter_class: Type[PrinterAdapter]
    ) -> None:
        """Register a printer adapter.

        Args:
            model: Printer model name
            adapter_class: Adapter class for the model
        """
        self.adapter_classes[model.upper()] = adapter_class
        logger.info("Registered printer adapter", model=model)

    def get_adapter_class(
        self, model: str
    ) -> Optional[Type[PrinterAdapter]]:
        """Get adapter class for printer model.

        Args:
            model: Printer model name

        Returns:
            Adapter class or None if not found
        """
        return self.adapter_classes.get(model.upper())

    def create_printer(
        self, printer_info: PrinterInfo
    ) -> Optional[PrinterAdapter]:
        """Create and register a printer instance.

        Args:
            printer_info: Printer information

        Returns:
            Printer adapter instance or None if model not supported
        """
        adapter_class = self.get_adapter_class(printer_info.model)
        if not adapter_class:
            logger.warning(
                "Unsupported printer model",
                model=printer_info.model,
            )
            return None

        adapter = adapter_class(printer_info)
        self.printers[printer_info.id] = adapter
        logger.info(
            "Created printer instance",
            printer_id=printer_info.id,
            model=printer_info.model,
        )
        return adapter

    def get_printer(self, printer_id: str) -> Optional[PrinterAdapter]:
        """Get printer by ID.

        Args:
            printer_id: Printer ID

        Returns:
            Printer adapter or None if not found
        """
        return self.printers.get(printer_id)

    def get_all_printers(self) -> Dict[str, PrinterAdapter]:
        """Get all registered printers.

        Returns:
            Dictionary of all printers
        """
        return self.printers.copy()

    def remove_printer(self, printer_id: str) -> bool:
        """Remove printer from registry.

        Args:
            printer_id: Printer ID

        Returns:
            True if removed, False if not found
        """
        if printer_id in self.printers:
            del self.printers[printer_id]
            logger.info("Removed printer from registry", printer_id=printer_id)
            return True
        return False

    def list_supported_models(self) -> list:
        """List all supported printer models.

        Returns:
            List of supported model names
        """
        return list(self.adapter_classes.keys())
