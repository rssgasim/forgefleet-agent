"""FlashForge AD5M printer adapter."""

from ..models import PrinterCapabilities, PrinterState
from .base import FlashForgeAdapter


class FlashForgeAD5MAdapter(FlashForgeAdapter):
    """Adapter for FlashForge AD5M printer."""

    MODEL = "AD5M"
    SUPPORTED_FIRMWARE = ["5.1.8+"]

    async def _get_capabilities(self) -> PrinterCapabilities:
        """Get AD5M-specific capabilities.

        Returns:
            Printer capabilities
        """
        capabilities = await super()._get_capabilities()
        # AD5M specific settings can be adjusted here if needed
        return capabilities
