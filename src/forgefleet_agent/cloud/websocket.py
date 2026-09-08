"""WebSocket connection to ForgeFleet Cloud."""

import asyncio
import json
from typing import Callable, Optional

import websockets

from ..logging import get_logger
from .authentication import CloudAuthenticator

logger = get_logger(__name__)


class CloudWebSocketClient:
    """WebSocket client for real-time cloud communication."""

    def __init__(
        self,
        ws_url: str,
        agent_token: Optional[str] = None,
        reconnect_max_retries: int = 10,
        reconnect_backoff_initial: int = 2,
        reconnect_backoff_max: int = 300,
    ) -> None:
        """Initialize WebSocket client.

        Args:
            ws_url: WebSocket URL
            agent_token: Agent authentication token
            reconnect_max_retries: Maximum reconnection attempts
            reconnect_backoff_initial: Initial backoff time in seconds
            reconnect_backoff_max: Maximum backoff time in seconds
        """
        self.ws_url = ws_url
        self.authenticator = CloudAuthenticator(agent_token)
        self.reconnect_max_retries = reconnect_max_retries
        self.reconnect_backoff_initial = reconnect_backoff_initial
        self.reconnect_backoff_max = reconnect_backoff_max
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.message_handlers: dict = {}

    def register_handler(
        self, message_type: str, handler: Callable
    ) -> None:
        """Register a message handler.

        Args:
            message_type: Type of message to handle
            handler: Async handler function
        """
        self.message_handlers[message_type] = handler
        logger.debug("Registered message handler", message_type=message_type)

    async def connect(self) -> bool:
        """Connect to WebSocket.

        Returns:
            True if connection successful
        """
        retry_count = 0
        backoff = self.reconnect_backoff_initial

        while retry_count < self.reconnect_max_retries:
            try:
                logger.info(
                    "Connecting to cloud WebSocket",
                    url=self.ws_url,
                    attempt=retry_count + 1,
                )
                self.websocket = await websockets.connect(self.ws_url)
                self.connected = True
                logger.info("Connected to cloud WebSocket")

                # Start message receive loop
                asyncio.create_task(self._receive_loop())
                return True
            except Exception as e:
                retry_count += 1
                logger.warning(
                    "WebSocket connection failed",
                    attempt=retry_count,
                    error=str(e),
                    backoff=backoff,
                )
                if retry_count < self.reconnect_max_retries:
                    await asyncio.sleep(backoff)
                    backoff = min(
                        backoff * 2, self.reconnect_backoff_max
                    )

        logger.error("Failed to connect to cloud WebSocket after retries")
        return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self.connected = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.debug("Error closing WebSocket", error=str(e))
            self.websocket = None

    async def send_message(self, message_type: str, data: dict) -> bool:
        """Send message to cloud.

        Args:
            message_type: Type of message
            data: Message data

        Returns:
            True if message sent successfully
        """
        if not self.connected or not self.websocket:
            logger.warning("WebSocket not connected")
            return False

        try:
            message = {
                "type": message_type,
                "data": data,
            }
            await self.websocket.send(json.dumps(message))
            logger.debug("Message sent", message_type=message_type)
            return True
        except Exception as e:
            logger.error(
                "Error sending WebSocket message",
                error=str(e),
            )
            return False

    async def _receive_loop(self) -> None:
        """Main message receive loop."""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except Exception as e:
            logger.error("Error in WebSocket receive loop", error=str(e))
            self.connected = False

    async def _handle_message(self, message: str) -> None:
        """Handle received message.

        Args:
            message: Raw message text
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            message_data = data.get("data", {})

            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(message_data)
            else:
                logger.debug(
                    "No handler for message type",
                    message_type=message_type,
                )
        except Exception as e:
            logger.error("Error handling WebSocket message", error=str(e))
