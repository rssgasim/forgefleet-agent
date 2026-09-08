"""Unit tests for printer adapters."""

import pytest
from forgefleet_agent.printers import (
    PrinterInfo,
    PrinterRegistry,
    PrinterState,
    FlashForgeAD5MAdapter,
    FlashForgeAD5XAdapter,
)


class TestPrinterRegistry:
    """Test PrinterRegistry class."""

    def test_register_adapter(self):
        """Test adapter registration."""
        registry = PrinterRegistry()
        registry.register_adapter("AD5M", FlashForgeAD5MAdapter)
        assert registry.get_adapter_class("AD5M") == FlashForgeAD5MAdapter

    def test_create_printer(self):
        """Test printer creation."""
        registry = PrinterRegistry()
        registry.register_adapter("AD5M", FlashForgeAD5MAdapter)

        printer_info = PrinterInfo(
            id="AD5M-001",
            ip="192.168.1.50",
            model="AD5M",
        )
        adapter = registry.create_printer(printer_info)
        assert adapter is not None
        assert adapter.printer_info.id == "AD5M-001"

    def test_unsupported_model(self):
        """Test unsupported printer model."""
        registry = PrinterRegistry()
        printer_info = PrinterInfo(
            id="UNSUPPORTED-001",
            ip="192.168.1.50",
            model="UNSUPPORTED",
        )
        adapter = registry.create_printer(printer_info)
        assert adapter is None

    def test_list_supported_models(self):
        """Test listing supported models."""
        registry = PrinterRegistry()
        registry.register_adapter("AD5M", FlashForgeAD5MAdapter)
        registry.register_adapter("AD5X", FlashForgeAD5XAdapter)
        models = registry.list_supported_models()
        assert "AD5M" in models
        assert "AD5X" in models
