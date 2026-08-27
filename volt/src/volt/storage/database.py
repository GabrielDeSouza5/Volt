from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Optional

from volt.models.tool import ExecutionRecord


def _get_config_dir() -> Path:
    config_dir = Path.home() / ".config" / "volt"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def _get_db_path() -> Path:
    return _get_config_dir() / "volt.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_get_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS favorites (
            tool_name TEXT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS execution_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            command TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_code INTEGER DEFAULT -1,
            duration REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# Favorites


def add_favorite(tool_name: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR IGNORE INTO favorites (tool_name) VALUES (?)",
        (tool_name,),
    )
    conn.commit()
    conn.close()


def remove_favorite(tool_name: str) -> None:
    conn = _connect()
    conn.execute("DELETE FROM favorites WHERE tool_name = ?", (tool_name,))
    conn.commit()
    conn.close()


def get_favorites() -> list[str]:
    conn = _connect()
    rows = conn.execute(
        "SELECT tool_name FROM favorites ORDER BY added_at"
    ).fetchall()
    conn.close()
    return [row["tool_name"] for row in rows]


def is_favorite(tool_name: str) -> bool:
    conn = _connect()
    row = conn.execute(
        "SELECT 1 FROM favorites WHERE tool_name = ?", (tool_name,)
    ).fetchone()
    conn.close()
    return row is not None


def toggle_favorite(tool_name: str) -> bool:
    if is_favorite(tool_name):
        remove_favorite(tool_name)
        return False
    else:
        add_favorite(tool_name)
        return True


# History


def add_history(record: ExecutionRecord) -> None:
    conn = _connect()
    conn.execute(
        """INSERT INTO execution_history
           (tool_name, command, timestamp, exit_code, duration)
           VALUES (?, ?, ?, ?, ?)""",
        (record.tool_name, record.command, record.timestamp,
         record.exit_code, record.duration),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 100) -> list[ExecutionRecord]:
    conn = _connect()
    rows = conn.execute(
        """SELECT tool_name, command, timestamp, exit_code, duration
           FROM execution_history
           ORDER BY timestamp DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        ExecutionRecord(
            tool_name=row["tool_name"],
            command=row["command"],
            timestamp=row["timestamp"],
            exit_code=row["exit_code"],
            duration=row["duration"],
        )
        for row in rows
    ]


def clear_history() -> None:
    conn = _connect()
    conn.execute("DELETE FROM execution_history")
    conn.commit()
    conn.close()


# Settings


def set_setting(key: str, value: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    conn = _connect()
    row = conn.execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else default


def get_all_settings() -> dict[str, str]:
    conn = _connect()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


# Stats


def get_stats() -> dict:
    fav_count = len(get_favorites())
    conn = _connect()
    hist_count = conn.execute(
        "SELECT COUNT(*) as c FROM execution_history"
    ).fetchone()["c"]
    conn.close()
    return {"favorites": fav_count, "history_count": hist_count}
