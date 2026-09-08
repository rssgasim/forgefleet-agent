"""Cloud authentication handling."""

from typing import Optional

from ..logging import get_logger

logger = get_logger(__name__)


class CloudAuthenticator:
    """Handles authentication with ForgeFleet Cloud."""

    def __init__(self, agent_token: Optional[str] = None) -> None:
        """Initialize authenticator.

        Args:
            agent_token: Agent authentication token
        """
        self.agent_token = agent_token
        self.headers = {}
        self._update_headers()

    def _update_headers(self) -> None:
        """Update authentication headers."""
        self.headers = {"Content-Type": "application/json"}
        if self.agent_token:
            self.headers["Authorization"] = f"Bearer {self.agent_token}"

    def set_token(self, token: str) -> None:
        """Set authentication token.

        Args:
            token: New authentication token
        """
        logger.info("Updating authentication token")
        self.agent_token = token
        self._update_headers()

    def get_headers(self) -> dict:
        """Get authentication headers.

        Returns:
            Dictionary of HTTP headers
        """
        return self.headers.copy()

    def is_authenticated(self) -> bool:
        """Check if authenticated.

        Returns:
            True if authenticated
        """
        return bool(self.agent_token)
