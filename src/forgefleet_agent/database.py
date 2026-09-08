"""SQLite database management for ForgeFleet Agent."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logging import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database management."""

    def __init__(self, db_path: Path) -> None:
        """Initialize database connection."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> None:
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Agent table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS agent (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                workspace_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Printers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS printers (
                id TEXT PRIMARY KEY,
                printer_ip TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT,
                firmware_version TEXT,
                status TEXT DEFAULT 'UNKNOWN',
                workspace_id TEXT,
                last_seen TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Telemetry table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_id TEXT NOT NULL,
                state TEXT,
                progress REAL,
                nozzle_temperature REAL,
                bed_temperature REAL,
                current_file TEXT,
                error_code TEXT,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0,
                FOREIGN KEY (printer_id) REFERENCES printers(id)
            )
            """
        )

        # Events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                printer_id TEXT,
                event_type TEXT NOT NULL,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN DEFAULT 0,
                FOREIGN KEY (printer_id) REFERENCES printers(id)
            )
            """
        )

        # Commands table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS commands (
                id TEXT PRIMARY KEY,
                printer_id TEXT NOT NULL,
                command_type TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                result TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (printer_id) REFERENCES printers(id)
            )
            """
        )

        # Configuration table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS configuration (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()
        conn.close()
        logger.info("Database schema initialized", db_path=str(self.db_path))

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a database query."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return cursor

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result

    def fetch_all(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def save_printer(self, printer_data: Dict[str, Any]) -> None:
        """Save printer information."""
        self.execute(
            """
            INSERT OR REPLACE INTO printers
            (id, printer_ip, model, serial_number, firmware_version, status, workspace_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                printer_data["id"],
                printer_data["ip"],
                printer_data["model"],
                printer_data.get("serial_number"),
                printer_data.get("firmware_version"),
                printer_data.get("status", "UNKNOWN"),
                printer_data.get("workspace_id"),
                datetime.utcnow().isoformat(),
            ),
        )
        logger.info("Printer saved", printer_id=printer_data["id"])

    def get_printer(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """Get printer by ID."""
        row = self.fetch_one("SELECT * FROM printers WHERE id = ?", (printer_id,))
        return dict(row) if row else None

    def get_all_printers(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all printers, optionally filtered by workspace."""
        if workspace_id:
            rows = self.fetch_all(
                "SELECT * FROM printers WHERE workspace_id = ?",
                (workspace_id,),
            )
        else:
            rows = self.fetch_all("SELECT * FROM printers")
        return [dict(row) for row in rows]
