"""Configuration management for ForgeFleet Agent."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Agent configuration settings."""

    # API Configuration
    forgefleet_api_url: str = Field(
        default="https://api.forgefleet.example.com",
        env="FORGEFLEET_API_URL",
        description="ForgeFleet Cloud API URL"
    )
    forgefleet_agent_token: Optional[str] = Field(
        default=None,
        env="FORGEFLEET_AGENT_TOKEN",
        description="Agent authentication token"
    )

    # Agent Configuration
    agent_name: str = Field(
        default="ForgeFleet Agent",
        env="AGENT_NAME",
        description="Agent display name"
    )
    agent_version: str = Field(
        default="1.0.0",
        env="AGENT_VERSION",
        description="Agent version"
    )
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    # Discovery Configuration
    discovery_timeout_seconds: int = Field(
        default=5,
        env="DISCOVERY_TIMEOUT_SECONDS",
        description="Timeout for single printer discovery attempt"
    )
    discovery_interval_seconds: int = Field(
        default=3600,
        env="DISCOVERY_INTERVAL_SECONDS",
        description="Interval between automatic discovery scans"
    )
    discovery_enabled: bool = Field(
        default=True,
        env="DISCOVERY_ENABLED",
        description="Enable automatic printer discovery"
    )

    # Telemetry Configuration
    telemetry_interval_seconds: int = Field(
        default=5,
        env="TELEMETRY_INTERVAL_SECONDS",
        description="Interval for telemetry collection"
    )
    telemetry_batch_size: int = Field(
        default=10,
        env="TELEMETRY_BATCH_SIZE",
        description="Number of telemetry samples to batch before sending"
    )
    telemetry_enabled: bool = Field(
        default=True,
        env="TELEMETRY_ENABLED",
        description="Enable telemetry collection"
    )

    # Cloud Connection
    cloud_heartbeat_interval_seconds: int = Field(
        default=30,
        env="CLOUD_HEARTBEAT_INTERVAL_SECONDS",
        description="Interval for cloud heartbeat"
    )
    cloud_reconnect_max_retries: int = Field(
        default=10,
        env="CLOUD_RECONNECT_MAX_RETRIES",
        description="Maximum reconnection attempts"
    )
    cloud_reconnect_backoff_initial_seconds: int = Field(
        default=2,
        env="CLOUD_RECONNECT_BACKOFF_INITIAL_SECONDS",
        description="Initial backoff time for reconnection"
    )
    cloud_reconnect_backoff_max_seconds: int = Field(
        default=300,
        env="CLOUD_RECONNECT_BACKOFF_MAX_SECONDS",
        description="Maximum backoff time for reconnection"
    )

    # Database
    database_path: Path = Field(
        default=Path("C:\\ProgramData\\ForgeFleet\\agent.db"),
        env="DATABASE_PATH",
        description="SQLite database path"
    )
    database_backup_enabled: bool = Field(
        default=True,
        env="DATABASE_BACKUP_ENABLED",
        description="Enable automatic database backups"
    )

    # Logging
    log_path: Path = Field(
        default=Path("C:\\ProgramData\\ForgeFleet\\logs"),
        env="LOG_PATH",
        description="Logging directory"
    )
    log_max_size_mb: int = Field(
        default=50,
        env="LOG_MAX_SIZE_MB",
        description="Maximum log file size in MB"
    )
    log_backup_count: int = Field(
        default=5,
        env="LOG_BACKUP_COUNT",
        description="Number of backup log files to keep"
    )
    log_format: str = Field(
        default="structured",
        env="LOG_FORMAT",
        description="Log format (structured or text)"
    )

    # Local UI
    local_ui_enabled: bool = Field(
        default=True,
        env="LOCAL_UI_ENABLED",
        description="Enable local status UI"
    )
    local_ui_host: str = Field(
        default="localhost",
        env="LOCAL_UI_HOST",
        description="Local UI host"
    )
    local_ui_port: int = Field(
        default=9090,
        env="LOCAL_UI_PORT",
        description="Local UI port"
    )
    local_ui_secure: bool = Field(
        default=False,
        env="LOCAL_UI_SECURE",
        description="Enable HTTPS for local UI"
    )

    # Workspace
    workspace_id: Optional[str] = Field(
        default="workspace_default",
        env="WORKSPACE_ID",
        description="Workspace ID for printer isolation"
    )

    # Advanced
    debug_mode: bool = Field(
        default=False,
        env="DEBUG_MODE",
        description="Enable debug mode"
    )
    verify_ssl: bool = Field(
        default=True,
        env="VERIFY_SSL",
        description="Verify SSL certificates"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **data):
        # Load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
        super().__init__(**data)

    def ensure_directories(self) -> None:
        """Create required directories."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
