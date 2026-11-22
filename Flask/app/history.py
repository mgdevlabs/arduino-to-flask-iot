import logging
import os
import sqlite3
import time
from contextlib import closing

log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "history.db")
DB_PATH_ENV = "HISTORY_DB_PATH"
RETENTION_SECONDS = 24 * 60 * 60

_initialized = set()


def get_db_path():
    return os.environ.get(DB_PATH_ENV, DEFAULT_DB_PATH)


def _ensure_db(path):
    if path in _initialized:
        return

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS readings ("
            "ts REAL PRIMARY KEY, temperature REAL, humidity REAL)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_ts ON readings(ts)")
        conn.commit()

    _initialized.add(path)


# Saves a single reading and removes samples older than 24 hours.
def record(temperature, humidity, ts=None):
    ts = time.time() if ts is None else ts
    path = get_db_path()

    try:
        _ensure_db(path)
        with closing(sqlite3.connect(path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO readings (ts, temperature, humidity) "
                "VALUES (?, ?, ?)",
                (ts, temperature, humidity),
            )
            conn.execute("DELETE FROM readings WHERE ts < ?", (ts - RETENTION_SECONDS,))
            conn.commit()
    except (OSError, sqlite3.Error) as e:
        log.warning("Could not save reading to history: %s", e)


# Returns at most one averaged point per minute from the last 24 hours.
def read_last_24h():
    path = get_db_path()

    try:
        _ensure_db(path)
        cutoff = time.time() - RETENTION_SECONDS
        with closing(sqlite3.connect(path)) as conn:
            rows = conn.execute(
                "SELECT CAST(ts / 60 AS INTEGER) * 60 AS ts, "
                "AVG(temperature) AS temperature, AVG(humidity) AS humidity "
                "FROM readings WHERE ts >= ? "
                "GROUP BY CAST(ts / 60 AS INTEGER) ORDER BY ts",
                (cutoff,),
            ).fetchall()
        return [
            {"ts": row[0], "temperature": row[1], "humidity": row[2]}
            for row in rows
        ]
    except (OSError, sqlite3.Error) as e:
        log.warning("Could not read history: %s", e)
        return []
