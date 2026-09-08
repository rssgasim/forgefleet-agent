"""FlashForge AD5X printer adapter."""

from ..models import PrinterCapabilities, PrinterState
from .base import FlashForgeAdapter


class FlashForgeAD5XAdapter(FlashForgeAdapter):
    """Adapter for FlashForge AD5X printer."""

    MODEL = "AD5X"
    SUPPORTED_FIRMWARE = ["5.1.8+"]

    async def _get_capabilities(self) -> PrinterCapabilities:
        """Get AD5X-specific capabilities.

        Returns:
            Printer capabilities
        """
        capabilities = await super()._get_capabilities()
        # AD5X specific settings can be adjusted here if needed
        return capabilities
