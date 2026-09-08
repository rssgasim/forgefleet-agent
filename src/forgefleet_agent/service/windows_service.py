"""Windows service integration."""

import asyncio
import sys
import logging
from pathlib import Path

try:
    import servicemanager
    import win32serviceutil
    import win32service
    import win32event
except ImportError:
    # Mock for non-Windows environments
    class win32serviceutil:
        @staticmethod
        def HandleCommandLine(*args, **kwargs):
            pass

from ..main import Agent
from ..logging import get_logger

logger = get_logger(__name__)


class ForgeFleetAgentService(win32serviceutil.ServiceFramework):
    """Windows service wrapper for ForgeFleet Agent."""

    _svc_name_ = "ForgeFleetAgent"
    _svc_display_name_ = "ForgeFleet Agent"
    _svc_description_ = "Local network bridge for FlashForge printer management"

    def __init__(self, args):
        """Initialize service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.is_alive = True
        self.agent: Optional[Agent] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def SvcDoRun(self) -> None:
        """Service main loop."""
        logger.info("Starting ForgeFleet Agent service")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        try:
            # Run agent
            self.agent = Agent()
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.agent.start())
        except Exception as e:
            logger.error("Error in service", error=str(e))
            servicemanager.LogErrorMsg(f"ForgeFleet Agent error: {e}")
        finally:
            self.is_alive = False

    def SvcStop(self) -> None:
        """Stop service."""
        logger.info("Stopping ForgeFleet Agent service")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_alive = False

        if self.agent and self.loop:
            try:
                self.loop.run_until_complete(self.agent.stop())
            except Exception as e:
                logger.error("Error stopping service", error=str(e))


def run_service() -> None:
    """Run the service."""
    if len(sys.argv) > 1:
        win32serviceutil.HandleCommandLine(ForgeFleetAgentService)
    else:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingleService(ForgeFleetAgentService)
        servicemanager.StartServiceCtrlDispatcher()


if __name__ == "__main__":
    run_service()
