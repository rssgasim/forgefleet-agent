"""ForgeFleet Cloud API models."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime


@dataclass
class AgentRegistration:
    """Agent registration request."""

    agent_id: str
    agent_name: str
    workspace_id: str
    os: str = "Windows"
    version: str = "1.0.0"
    hostname: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "workspace_id": self.workspace_id,
            "os": self.os,
            "version": self.version,
            "hostname": self.hostname,
        }


@dataclass
class Heartbeat:
    """Agent heartbeat."""

    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    printer_count: int = 0
    online_printers: int = 0
    status: str = "ONLINE"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "printer_count": self.printer_count,
            "online_printers": self.online_printers,
            "status": self.status,
        }


@dataclass
class PrinterEvent:
    """Printer lifecycle event."""

    event_type: str  # CREATE, UPDATE, ONLINE, OFFLINE, DELETE
    printer_id: str
    printer_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "printer_id": self.printer_id,
            "printer_data": self.printer_data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TelemetryData:
    """Telemetry data point."""

    printer_id: str
    state: str
    timestamp: datetime
    progress: Optional[float] = None
    nozzle_temperature: Optional[float] = None
    bed_temperature: Optional[float] = None
    current_file: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "printer_id": self.printer_id,
            "state": self.state,
            "timestamp": self.timestamp.isoformat(),
            "progress": self.progress,
            "nozzle_temperature": self.nozzle_temperature,
            "bed_temperature": self.bed_temperature,
            "current_file": self.current_file,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass
class CommandRequest:
    """Cloud command request."""

    command_id: str
    command_type: str
    printer_id: str
    parameters: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CommandResult:
    """Command execution result."""

    command_id: str
    printer_id: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "command_id": self.command_id,
            "printer_id": self.printer_id,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "result_data": self.result_data,
        }
