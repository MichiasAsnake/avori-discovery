from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR, TRACKING_GRADUATION_SOLD_COUNT, ensure_output_dir


STATE_DB_PATH = OUTPUT_DIR / "avori_state.sqlite3"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _connect() -> sqlite3.Connection:
    ensure_output_dir()
    connection = sqlite3.connect(STATE_DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(connection)
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            product_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            reason TEXT NOT NULL,
            added_at TEXT NOT NULL,
            tracked INTEGER NOT NULL DEFAULT 0,
            graduated INTEGER NOT NULL DEFAULT 0,
            last_score REAL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS watchlist_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            sold_count INTEGER,
            review_count INTEGER,
            price REAL,
            score REAL,
            FOREIGN KEY (product_id) REFERENCES watchlist(product_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS discovery_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            error TEXT,
            results_path TEXT,
            payload_json TEXT
        );
        """
    )
    connection.commit()


@contextmanager
def _cursor():
    connection = _connect()
    try:
        yield connection
    finally:
        connection.close()


def upsert_watchlist_entry(
    product_id: str,
    title: str,
    reason: str,
    *,
    tracked: bool = False,
    score: float | None = None,
    added_at: str | None = None,
) -> dict[str, Any]:
    now = _utcnow_iso()
    observed_at = added_at or date.today().isoformat()
    with _cursor() as connection:
        connection.execute(
            """
            INSERT INTO watchlist (product_id, title, reason, added_at, tracked, graduated, last_score, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                title=excluded.title,
                reason=excluded.reason,
                tracked=excluded.tracked,
                last_score=excluded.last_score,
                updated_at=excluded.updated_at
            """,
            (product_id, title, reason, observed_at, int(tracked), score, now),
        )
        connection.commit()
    return {
        "product_id": product_id,
        "title": title,
        "reason": reason,
        "added_at": observed_at,
        "track": tracked,
        "graduated": False,
        "score": score,
    }


def record_watchlist_snapshot(
    product_id: str,
    *,
    sold_count: int | None,
    review_count: int | None,
    price: float | None,
    score: float | None,
    observed_at: str | None = None,
) -> None:
    snapshot_time = observed_at or _utcnow_iso()
    with _cursor() as connection:
        connection.execute(
            """
            INSERT INTO watchlist_snapshots (product_id, observed_at, sold_count, review_count, price, score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (product_id, snapshot_time, sold_count, review_count, price, score),
        )
        connection.execute(
            """
            UPDATE watchlist
            SET last_score = COALESCE(?, last_score),
                graduated = CASE WHEN COALESCE(?, 0) >= ? THEN 1 ELSE graduated END,
                updated_at = ?
            WHERE product_id = ?
            """,
            (score, sold_count, TRACKING_GRADUATION_SOLD_COUNT, _utcnow_iso(), product_id),
        )
        connection.commit()


def remove_watchlist_entry(product_id: str) -> bool:
    with _cursor() as connection:
        cursor = connection.execute("DELETE FROM watchlist WHERE product_id = ?", (product_id,))
        connection.commit()
    return cursor.rowcount > 0


def _compute_velocity(snapshots: list[sqlite3.Row]) -> float | None:
    if len(snapshots) < 2:
        return None

    first = snapshots[0]
    last = snapshots[-1]
    if first["sold_count"] is None or last["sold_count"] is None:
        return None

    start = datetime.fromisoformat(str(first["observed_at"]).replace("Z", "+00:00"))
    end = datetime.fromisoformat(str(last["observed_at"]).replace("Z", "+00:00"))
    days = max((end - start).total_seconds() / 86400, 1)
    delta = int(last["sold_count"]) - int(first["sold_count"])
    return round(delta / days * 7, 2)


def list_watchlist_entries() -> list[dict[str, Any]]:
    with _cursor() as connection:
        rows = connection.execute(
            """
            SELECT product_id, title, reason, added_at, tracked, graduated, last_score
            FROM watchlist
            ORDER BY added_at DESC, product_id ASC
            """
        ).fetchall()
        entries: list[dict[str, Any]] = []
        for row in rows:
            snapshots = connection.execute(
                """
                SELECT observed_at, sold_count, review_count, price, score
                FROM watchlist_snapshots
                WHERE product_id = ?
                ORDER BY observed_at ASC
                """,
                (row["product_id"],),
            ).fetchall()
            latest = snapshots[-1] if snapshots else None
            entries.append(
                {
                    "product_id": row["product_id"],
                    "title": row["title"],
                    "reason": row["reason"],
                    "added_at": row["added_at"],
                    "track": bool(row["tracked"]),
                    "graduated": bool(row["graduated"]),
                    "score": row["last_score"],
                    "latest_sold_count": latest["sold_count"] if latest else None,
                    "latest_review_count": latest["review_count"] if latest else None,
                    "latest_price": latest["price"] if latest else None,
                    "velocity": _compute_velocity(snapshots),
                    "snapshots_count": len(snapshots),
                }
            )
    return entries


def create_discovery_job(job_id: str) -> dict[str, Any]:
    now = _utcnow_iso()
    with _cursor() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO discovery_jobs (job_id, status, created_at, updated_at, error, results_path, payload_json)
            VALUES (?, 'queued', ?, ?, NULL, NULL, NULL)
            """,
            (job_id, now, now),
        )
        connection.commit()
    return get_discovery_job(job_id)


def update_discovery_job(
    job_id: str,
    *,
    status: str,
    error: str | None = None,
    results_path: str | Path | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with _cursor() as connection:
        connection.execute(
            """
            UPDATE discovery_jobs
            SET status = ?, updated_at = ?, error = ?, results_path = ?, payload_json = ?
            WHERE job_id = ?
            """,
            (
                status,
                _utcnow_iso(),
                error,
                str(results_path) if results_path else None,
                json.dumps(payload) if payload is not None else None,
                job_id,
            ),
        )
        connection.commit()
    return get_discovery_job(job_id)


def get_discovery_job(job_id: str) -> dict[str, Any]:
    with _cursor() as connection:
        row = connection.execute(
            """
            SELECT job_id, status, created_at, updated_at, error, results_path, payload_json
            FROM discovery_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        ).fetchone()
    if row is None:
        return {}
    payload = json.loads(row["payload_json"]) if row["payload_json"] else None
    return {
        "job_id": row["job_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "error": row["error"],
        "results_path": row["results_path"],
        "payload": payload,
    }
