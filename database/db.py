import os
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "database" / "ticketpilot.db"
DB_PATH = Path(os.getenv("TICKETPILOT_DB_PATH", str(DEFAULT_DB_PATH)))


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with dictionary-like rows and foreign keys enabled."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    """Create the TicketPilot helpdesk tables if they do not already exist."""
    schema_path = PROJECT_ROOT / "database" / "schema.sql"
    schema = schema_path.read_text(encoding="utf-8")

    with get_connection() as connection:
        connection.executescript(schema)
        connection.commit()


def row_to_dict(row):
    return dict(row) if row is not None else None
