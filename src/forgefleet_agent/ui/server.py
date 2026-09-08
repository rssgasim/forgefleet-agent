"""Local status UI server."""

import asyncio
import json
from typing import Dict, Optional

try:
    from aiohttp import web
except ImportError:
    web = None

from ..logging import get_logger

logger = get_logger(__name__)


class LocalUIServer:
    """Lightweight local status UI server."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9090,
        agent=None,
    ) -> None:
        """Initialize UI server.

        Args:
            host: Server host
            port: Server port
            agent: Agent instance
        """
        self.host = host
        self.port = port
        self.agent = agent
        self.app: Optional[web.Application] = None
        self.runner: Optional[web.AppRunner] = None

    async def start(self) -> None:
        """Start the UI server."""
        if not web:
            logger.warning("aiohttp not available, UI disabled")
            return

        logger.info(
            "Starting local UI server",
            host=self.host,
            port=self.port,
        )

        self.app = web.Application()
        self._setup_routes()

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.host, self.port)
        await site.start()

        logger.info(
            "Local UI server started",
            url=f"http://{self.host}:{self.port}",
        )

    async def stop(self) -> None:
        """Stop the UI server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("Local UI server stopped")

    def _setup_routes(self) -> None:
        """Setup API routes."""
        self.app.router.add_get("/", self._handle_index)
        self.app.router.add_get("/api/status", self._handle_status)
        self.app.router.add_get("/api/printers", self._handle_get_printers)
        self.app.router.add_post("/api/printers/scan", self._handle_scan)
        self.app.router.add_post("/api/printers/pair", self._handle_pair)
        self.app.router.add_get("/api/logs", self._handle_logs)

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Serve index page."""
        html = self._get_index_html()
        return web.Response(text=html, content_type="text/html")

    async def _handle_status(self, request: web.Request) -> web.Response:
        """Get agent status."""
        if not self.agent:
            return web.json_response({"error": "Agent not available"})

        status = {
            "agent_id": self.agent.agent_id,
            "agent_name": self.agent.settings.agent_name,
            "running": self.agent.running,
            "printers": len(self.agent.printer_registry.get_all_printers()),
        }
        return web.json_response(status)

    async def _handle_get_printers(
        self, request: web.Request
    ) -> web.Response:
        """Get list of printers."""
        if not self.agent:
            return web.json_response({"error": "Agent not available"})

        printers = []
        for printer_id, adapter in self.agent.printer_registry.get_all_printers().items():
            status = await adapter.get_status()
            printers.append({
                "id": printer_id,
                "model": adapter.printer_info.model,
                "ip": adapter.printer_info.ip,
                "status": status.state.value,
                "temperature": {
                    "nozzle": status.nozzle_temperature,
                    "bed": status.bed_temperature,
                },
                "progress": status.progress,
            })
        return web.json_response({"printers": printers})

    async def _handle_scan(
        self, request: web.Request
    ) -> web.Response:
        """Initiate printer scan."""
        if not self.agent:
            return web.json_response({"error": "Agent not available"})

        asyncio.create_task(self.agent._discovery_loop())
        return web.json_response({"status": "Scan initiated"})

    async def _handle_pair(
        self, request: web.Request
    ) -> web.Response:
        """Pair printer with workspace."""
        try:
            data = await request.json()
            printer_ip = data.get("printer_ip")
            workspace_id = data.get("workspace_id")

            if not printer_ip or not workspace_id:
                return web.json_response(
                    {"error": "Missing printer_ip or workspace_id"},
                    status=400,
                )

            return web.json_response({"status": "Pairing initiated"})
        except Exception as e:
            logger.error("Error pairing printer", error=str(e))
            return web.json_response({"error": str(e)}, status=500)

    async def _handle_logs(
        self, request: web.Request
    ) -> web.Response:
        """Get recent logs."""
        if not self.agent:
            return web.json_response({"error": "Agent not available"})

        log_file = self.agent.settings.log_path / "forgefleet_agent.log"
        if log_file.exists():
            with open(log_file, "r") as f:
                lines = f.readlines()[-100:]  # Last 100 lines
                return web.json_response({"logs": lines})
        return web.json_response({"logs": []})

    def _get_index_html(self) -> str:
        """Get index HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>ForgeFleet Agent</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .online { background-color: #d4edda; }
        .offline { background-color: #f8d7da; }
        .printer { padding: 10px; border: 1px solid #ddd; margin: 10px 0; border-radius: 5px; }
        button { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ForgeFleet Agent</h1>
        <div id="status" class="status">Loading...</div>
        <div>
            <button onclick="scanPrinters()">Scan Printers</button>
            <button onclick="refreshStatus()">Refresh</button>
        </div>
        <h2>Printers</h2>
        <div id="printers"></div>
    </div>
    <script>
        async function refreshStatus() {
            const response = await fetch('/api/status');
            const data = await response.json();
            document.getElementById('status').innerHTML = 
                `<strong>${data.agent_name}</strong><br/>` +
                `Printers: ${data.printers}<br/>` +
                `Status: ${data.running ? 'Running' : 'Stopped'}`;
            loadPrinters();
        }
        async function loadPrinters() {
            const response = await fetch('/api/printers');
            const data = await response.json();
            const html = data.printers.map(p => `
                <div class="printer ${p.status === 'ONLINE' ? 'online' : 'offline'}">
                    <strong>${p.model}</strong> (${p.ip})<br/>
                    Status: ${p.status}<br/>
                    Nozzle: ${p.temperature.nozzle}°C | Bed: ${p.temperature.bed}°C<br/>
                    Progress: ${p.progress || 0}%
                </div>
            `).join('');
            document.getElementById('printers').innerHTML = html;
        }
        async function scanPrinters() {
            await fetch('/api/printers/scan', {method: 'POST'});
            alert('Scan initiated');
        }
        refreshStatus();
        setInterval(refreshStatus, 5000);
    </script>
</body>
</html>
        """
