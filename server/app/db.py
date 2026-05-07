from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .security import hash_password


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "server.sqlite3"


def get_db_path() -> Path:
    return Path(os.getenv("LICENSE_SERVER_DB", str(DEFAULT_DB_PATH)))


def connect() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def session() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS admin_sessions (
                token TEXT PRIMARY KEY,
                admin_id INTEGER NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active',
                owner TEXT,
                max_devices INTEGER NOT NULL DEFAULT 1,
                expires_at TEXT,
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
                machine_id TEXT NOT NULL,
                client_name TEXT,
                app_version TEXT,
                activation_token TEXT NOT NULL UNIQUE,
                last_ip TEXT,
                last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(license_id, machine_id)
            );

            CREATE TABLE IF NOT EXISTS releases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT 'windows',
                download_url TEXT NOT NULL,
                changelog TEXT,
                mandatory INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(version, platform)
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_id INTEGER REFERENCES licenses(id) ON DELETE SET NULL,
                client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
                machine_id TEXT,
                event_type TEXT NOT NULL,
                ip TEXT,
                payload TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_clients_license ON clients(license_id);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
            """
        )
        _ensure_column(conn, "clients", "last_ip", "TEXT")
        _ensure_column(conn, "events", "ip", "TEXT")
        _ensure_default_admin(conn)


def _ensure_default_admin(conn: sqlite3.Connection) -> None:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    exists = conn.execute(
        "SELECT id FROM admins WHERE username = ?",
        (username,),
    ).fetchone()
    if exists:
        return
    conn.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (username, hash_password(password)),
    )


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
