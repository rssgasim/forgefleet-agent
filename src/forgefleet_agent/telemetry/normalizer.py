"""Telemetry normalization utilities."""

from typing import Dict, Optional

from ..printers import PrinterStatus


class TelemetryNormalizer:
    """Normalizes printer telemetry to standard format."""

    @staticmethod
    def normalize(status: PrinterStatus) -> Dict:
        """Normalize printer status to telemetry format.

        Args:
            status: Printer status from adapter

        Returns:
            Normalized telemetry dictionary
        """
        return {
            "printer_id": status.printer_id,
            "timestamp": status.timestamp.isoformat(),
            "state": status.state.value,
            "progress": status.progress,
            "nozzle_temperature": status.nozzle_temperature,
            "bed_temperature": status.bed_temperature,
            "current_file": status.current_file,
            "print_start_time": status.print_start_time.isoformat()
            if status.print_start_time
            else None,
            "estimated_completion_time": status.estimated_completion_time.isoformat()
            if status.estimated_completion_time
            else None,
            "error_code": status.error_code,
            "error_message": status.error_message,
            "native_state": status.native_state,
        }
