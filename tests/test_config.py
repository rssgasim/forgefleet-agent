"""Unit tests for configuration."""

import pytest
from pathlib import Path
from forgefleet_agent.config import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default configuration."""
        settings = Settings()
        assert settings.agent_name == "ForgeFleet Agent"
        assert settings.log_level == "INFO"
        assert settings.telemetry_interval_seconds == 5

    def test_custom_settings(self):
        """Test custom configuration."""
        settings = Settings(
            agent_name="Custom Agent",
            telemetry_interval_seconds=10,
        )
        assert settings.agent_name == "Custom Agent"
        assert settings.telemetry_interval_seconds == 10
