"""FlashForge Network Protocol Diagnostic Tool

This tool performs safe, read-only discovery and diagnostics of FlashForge printers
without sending any control commands.

Usage:
    python -m forgefleet_agent.diagnostics
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .logging import get_logger

logger = get_logger(__name__)

# Diagnostic output directory
DIAGNOSTICS_DIR = Path.home() / "ForgeFleet" / "diagnostics"


class FlashForgeDiagnostics:
    """Safe diagnostic tool for FlashForge printer discovery and protocol investigation."""

    # Known FlashForge service ports (to be verified)
    KNOWN_PORTS = {
        8898: "HTTP API (assumed)",
        8899: "TCP (assumed)",
        5353: "mDNS (assumed)",
    }

    def __init__(self, printer_ip: str, timeout: int = 5) -> None:
        """Initialize diagnostics.

        Args:
            printer_ip: IP address of printer to diagnose
            timeout: Request timeout in seconds
        """
        self.printer_ip = printer_ip
        self.timeout = timeout
        self.results: Dict[str, Any] = {}
        self.raw_responses: Dict[str, Any] = {}

    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run complete diagnostic suite.

        Returns:
            Dictionary of diagnostic results
        """
        print("\n" + "=" * 60)
        print("ForgeFleet FlashForge Diagnostic Tool")
        print("=" * 60 + "\n")

        self.results["timestamp"] = datetime.utcnow().isoformat()
        self.results["target_ip"] = self.printer_ip

        # Step 1: Check network connectivity
        print("[1/6] Checking network connectivity...")
        await self._check_connectivity()

        # Step 2: Probe known ports
        print("[2/6] Probing known service ports...")
        await self._probe_ports()

        # Step 3: Attempt HTTP discovery
        print("[3/6] Attempting HTTP API discovery...")
        await self._http_discovery()

        # Step 4: Attempt known HTTP endpoints
        print("[4/6] Probing common HTTP endpoints...")
        await self._probe_http_endpoints()

        # Step 5: Attempt mDNS discovery
        print("[5/6] Attempting mDNS discovery...")
        await self._mdns_discovery()

        # Step 6: Summary and next steps
        print("[6/6] Generating summary...")
        await self._generate_summary()

        return self.results

    async def _check_connectivity(self) -> None:
        """Check if printer is reachable via ping."""
        import subprocess
        import platform

        try:
            # Use ping to check connectivity
            param = "-n" if platform.system().lower() == "windows" else "-c"
            result = subprocess.run(
                ["ping", param, "1", self.printer_ip],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                print(f"  ✓ Printer is reachable at {self.printer_ip}")
                self.results["connectivity"] = "SUCCESS"
            else:
                print(f"  ✗ Printer at {self.printer_ip} is not reachable")
                self.results["connectivity"] = "FAILED"
        except Exception as e:
            print(f"  ⚠ Connectivity check failed: {e}")
            self.results["connectivity"] = "ERROR"

    async def _probe_ports(self) -> None:
        """Probe known FlashForge service ports."""
        self.results["port_scan"] = {}

        for port, description in self.KNOWN_PORTS.items():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Try HTTP connection
                    url = f"http://{self.printer_ip}:{port}/"
                    try:
                        response = await client.get(url, follow_redirects=False)
                        print(
                            f"  ✓ Port {port} ({description}): "
                            f"HTTP {response.status_code}"
                        )
                        self.results["port_scan"][port] = {
                            "status": "OPEN",
                            "http_status": response.status_code,
                            "description": description,
                        }
                    except (httpx.ConnectError, httpx.TimeoutException):
                        print(f"  - Port {port} ({description}): Not responding to HTTP")
                        self.results["port_scan"][port] = {
                            "status": "CLOSED",
                            "description": description,
                        }
            except Exception as e:
                print(f"  ⚠ Port {port} probe error: {e}")
                self.results["port_scan"][port] = {
                    "status": "ERROR",
                    "error": str(e),
                }

    async def _http_discovery(self) -> None:
        """Attempt HTTP-based printer discovery.

        This is the PRIMARY discovery method for FlashForge printers.
        """
        self.results["http_discovery"] = {}

        # Common FlashForge HTTP endpoints to try
        endpoints_to_try = [
            "/api/version",
            "/api/",
            "/",
            "/json/printer",
            "/api/printer",
            "/api/info",
        ]

        print("  Attempting HTTP discovery endpoints...")
        for endpoint in endpoints_to_try:
            await self._probe_http_endpoint(endpoint)

    async def _probe_http_endpoints(self) -> None:
        """Probe common HTTP endpoints for status and metadata."""
        self.results["http_endpoints"] = {}

        # Try to get status if discovery succeeded
        if "http_discovery" in self.results:
            endpoints = [
                "/api/status",
                "/api/state",
                "/api/printer/status",
                "/json/status",
                "/printer/status",
            ]

            print("  Probing status endpoints...")
            for endpoint in endpoints:
                await self._probe_http_endpoint(endpoint, is_status=True)

    async def _probe_http_endpoint(
        self, endpoint: str, is_status: bool = False
    ) -> None:
        """Probe a single HTTP endpoint.

        Args:
            endpoint: HTTP endpoint path to probe
            is_status: Whether this is a status endpoint
        """
        url = f"http://{self.printer_ip}:8898{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"    ✓ {endpoint}: SUCCESS (JSON)")
                        print(f"      Keys: {', '.join(list(data.keys())[:5])}")
                        if len(data.keys()) > 5:
                            print(f"      ... and {len(data.keys()) - 5} more")

                        # Save raw response
                        endpoint_key = endpoint.replace("/", "_")
                        self.results["http_endpoints"][endpoint_key] = {
                            "status": "SUCCESS",
                            "http_status": response.status_code,
                            "keys": list(data.keys()),
                            "type": "json",
                        }
                        self.raw_responses[endpoint_key] = data

                        # Log important fields
                        if "model" in data:
                            print(f"      Model: {data['model']}")
                        if "serial" in data or "serial_number" in data:
                            serial_key = "serial" if "serial" in data else "serial_number"
                            print(f"      Serial: {data[serial_key]}")
                        if "version" in data or "firmware" in data:
                            fw_key = "version" if "version" in data else "firmware"
                            print(f"      Firmware: {data[fw_key]}")

                    except json.JSONDecodeError:
                        print(f"    ✓ {endpoint}: Response received but not JSON")
                        print(f"      Content-Type: {response.headers.get('content-type')}")
                        print(f"      Body (first 100 chars): {response.text[:100]}")
                        self.results["http_endpoints"][endpoint.replace("/", "_")] = {
                            "status": "SUCCESS",
                            "http_status": response.status_code,
                            "type": "text",
                            "content_type": response.headers.get("content-type"),
                        }
                elif response.status_code == 404:
                    pass  # Endpoint not found, try next
                elif response.status_code == 401:
                    print(f"    ⚠ {endpoint}: HTTP 401 (Authentication required)")
                    self.results["http_endpoints"][endpoint.replace("/", "_")] = {
                        "status": "REQUIRES_AUTH",
                        "http_status": 401,
                    }
                else:
                    print(f"    - {endpoint}: HTTP {response.status_code}")
        except asyncio.TimeoutError:
            pass  # Timeout, try next
        except httpx.ConnectError:
            pass  # Connection failed, try next
        except Exception as e:
            print(f"    ⚠ {endpoint}: Error: {e}")

    async def _mdns_discovery(self) -> None:
        """Attempt mDNS/Bonjour discovery.

        FlashForge printers may advertise via mDNS.
        """
        self.results["mdns"] = {"status": "NOT_IMPLEMENTED", "note": "Requires zeroconf library"}
        print("  mDNS discovery: Not yet implemented")

    async def _generate_summary(self) -> None:
        """Generate diagnostic summary and save results."""
        # Determine overall status
        overall_status = "NOT_REACHABLE"
        if self.results.get("connectivity") == "SUCCESS":
            if self.results.get("http_endpoints"):
                overall_status = "PARTIAL_SUCCESS"
            if self.results.get("http_endpoints") and self._has_critical_fields():
                overall_status = "READY_FOR_IMPLEMENTATION"

        self.results["overall_status"] = overall_status

        # Print summary
        print("\n" + "-" * 60)
        print("DIAGNOSTIC SUMMARY")
        print("-" * 60)
        print(f"Target IP: {self.printer_ip}")
        print(f"Connectivity: {self.results.get('connectivity', 'UNKNOWN')}")
        print(f"HTTP Port 8898: {self._get_port_status(8898)}")
        print(f"Overall Status: {overall_status}")

        if overall_status == "READY_FOR_IMPLEMENTATION":
            print("\n✓ Printer successfully discovered and responding to API calls")
            print("  Ready to implement production adapter")
        elif overall_status == "PARTIAL_SUCCESS":
            print("\n⚠ Printer is reachable but some endpoints need verification")
            print("  May require authentication or further protocol investigation")
        else:
            print("\n✗ Printer not responding to standard discovery methods")
            print("  Check printer IP, network connectivity, or firewall settings")

        print("-" * 60 + "\n")

        # Save results to file
        await self._save_results()

    def _get_port_status(self, port: int) -> str:
        """Get human-readable port status."""
        port_info = self.results.get("port_scan", {}).get(port, {})
        if port_info.get("status") == "OPEN":
            return f"OPEN (HTTP {port_info.get('http_status')})"
        elif port_info.get("status") == "CLOSED":
            return "CLOSED"
        else:
            return "UNKNOWN"

    def _has_critical_fields(self) -> bool:
        """Check if discovered endpoints contain critical fields."""
        for endpoint_data in self.raw_responses.values():
            if isinstance(endpoint_data, dict):
                # Look for model, serial, firmware, or status fields
                critical_fields = ["model", "serial", "version", "firmware", "status"]
                if any(field in endpoint_data for field in critical_fields):
                    return True
        return False

    async def _save_results(self) -> None:
        """Save diagnostic results to file."""
        # Create diagnostics directory
        DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)

        # Create printer-specific directory
        printer_dir = DIAGNOSTICS_DIR / f"printer_{self.printer_ip.replace('.', '_')}"
        printer_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        results_file = printer_dir / "diagnostic_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Diagnostic results saved to: {results_file}")

        # Save raw responses
        if self.raw_responses:
            raw_dir = printer_dir / "raw_responses"
            raw_dir.mkdir(parents=True, exist_ok=True)
            for endpoint_name, response_data in self.raw_responses.items():
                response_file = raw_dir / f"{endpoint_name}.json"
                with open(response_file, "w") as f:
                    json.dump(response_data, f, indent=2)
            print(f"✓ Raw responses saved to: {raw_dir}")

        print(f"\nNext steps:")
        print(f"1. Review the diagnostic output above")
        print(f"2. Check saved files in: {printer_dir}")
        print(f"3. Share results if needed for protocol implementation")


async def main() -> None:
    """Main entry point for diagnostics."""
    print("\nForgeFleet FlashForge Diagnostic Tool")
    print("" + "-" * 40)
    print("This tool performs read-only diagnostic tests")
    print("against FlashForge printers.")
    print("\nNo control commands will be sent.\n")

    # Get printer IP from user
    printer_ip = input("Enter printer IP address (e.g., 192.168.1.50): ").strip()

    if not printer_ip:
        print("Error: No IP address provided")
        sys.exit(1)

    # Validate IP format
    parts = printer_ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        print(f"Error: Invalid IP address format: {printer_ip}")
        sys.exit(1)

    # Run diagnostics
    diagnostics = FlashForgeDiagnostics(printer_ip)
    try:
        results = await diagnostics.run_full_diagnostics()
        # Exit success if printer was found
        sys.exit(0 if results.get("overall_status") != "NOT_REACHABLE" else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnostics cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Diagnostic error", error=str(e))
        print(f"\nError during diagnostics: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
