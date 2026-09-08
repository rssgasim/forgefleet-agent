"""Printer models and data structures."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class PrinterState(str, Enum):
    """Normalized printer states."""

    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    IDLE = "IDLE"
    PREPARING = "PREPARING"
    PRINTING = "PRINTING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class PrinterInfo:
    """Basic printer information."""

    id: str
    ip: str
    model: str
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    status: PrinterState = PrinterState.UNKNOWN
    workspace_id: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "ip": self.ip,
            "model": self.model,
            "serial_number": self.serial_number,
            "firmware_version": self.firmware_version,
            "status": self.status.value,
            "workspace_id": self.workspace_id,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PrinterStatus:
    """Real-time printer status."""

    printer_id: str
    state: PrinterState
    nozzle_temperature: Optional[float] = None
    bed_temperature: Optional[float] = None
    progress: Optional[float] = None  # 0-100
    current_file: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    print_start_time: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Original printer-specific state
    native_state: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "printer_id": self.printer_id,
            "state": self.state.value,
            "nozzle_temperature": self.nozzle_temperature,
            "bed_temperature": self.bed_temperature,
            "progress": self.progress,
            "current_file": self.current_file,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "print_start_time": self.print_start_time.isoformat()
            if self.print_start_time
            else None,
            "estimated_completion_time": self.estimated_completion_time.isoformat()
            if self.estimated_completion_time
            else None,
            "timestamp": self.timestamp.isoformat(),
            "native_state": self.native_state,
        }


@dataclass
class PrinterCapabilities:
    """Printer capabilities."""

    printer_id: str
    supports_pause: bool = False
    supports_resume: bool = False
    supports_stop: bool = False
    supports_print: bool = False
    supports_file_transfer: bool = False
    max_temperature: float = 300.0
    min_temperature: float = 20.0
    bed_max_temperature: float = 100.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "printer_id": self.printer_id,
            "supports_pause": self.supports_pause,
            "supports_resume": self.supports_resume,
            "supports_stop": self.supports_stop,
            "supports_print": self.supports_print,
            "supports_file_transfer": self.supports_file_transfer,
            "max_temperature": self.max_temperature,
            "min_temperature": self.min_temperature,
            "bed_max_temperature": self.bed_max_temperature,
        }
