"""Unit tests for telemetry."""

import pytest
from forgefleet_agent.telemetry import TelemetryNormalizer
from forgefleet_agent.printers import PrinterStatus, PrinterState


class TestTelemetryNormalizer:
    """Test TelemetryNormalizer class."""

    def test_normalize_status(self):
        """Test status normalization."""
        status = PrinterStatus(
            printer_id="AD5M-001",
            state=PrinterState.PRINTING,
            progress=50.0,
            nozzle_temperature=220.5,
            bed_temperature=60.0,
        )
        normalizer = TelemetryNormalizer()
        telemetry = normalizer.normalize(status)

        assert telemetry["printer_id"] == "AD5M-001"
        assert telemetry["state"] == "PRINTING"
        assert telemetry["progress"] == 50.0
        assert telemetry["nozzle_temperature"] == 220.5
