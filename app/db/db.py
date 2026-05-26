import logging
from typing import Any

import aiosqlite

from app.config import settings

logger = logging.getLogger(__name__)

_db: aiosqlite.Connection | None = None

VALID_STATUSES = ("queued", "claimed", "processing", "completed", "failed")


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(settings.db_path)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
    return _db


async def close_db() -> None:
    global _db
    if _db is not None:
        await _db.close()
        _db = None


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "phone_number": row["phone_number"],
        "message": row["message"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


async def _migrate_schema(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("PRAGMA table_info(jobs)")
    columns = {row[1] for row in await cursor.fetchall()}

    if not columns:
        return

    if "created_at" not in columns:
        await db.execute(
            "ALTER TABLE jobs ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        )
    if "updated_at" not in columns:
        await db.execute(
            "ALTER TABLE jobs ADD COLUMN updated_at TEXT NOT NULL DEFAULT (datetime('now'))"
        )


async def init_db() -> None:
    db = await get_db()
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT    NOT NULL,
            message      TEXT    NOT NULL,
            status       TEXT    NOT NULL DEFAULT 'queued'
                CHECK(status IN ('queued', 'claimed', 'processing', 'completed', 'failed')),
            created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    await _migrate_schema(db)
    await db.commit()


async def add_job(phone_number: str, message: str) -> int:
    db = await get_db()
    cursor = await db.execute(
        """
        INSERT INTO jobs (phone_number, message, status)
        VALUES (?, ?, 'queued')
        """,
        (phone_number, message),
    )
    await db.commit()
    return cursor.lastrowid


async def update_job_status(job_id: int, status: str) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")

    db = await get_db()
    await db.execute(
        """
        UPDATE jobs
        SET status = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (status, job_id),
    )
    await db.commit()


async def get_job_by_id(job_id: int) -> dict[str, Any] | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = await cursor.fetchone()
    return _row_to_dict(row) if row else None


async def claim_queued_jobs(limit: int = 10) -> list[int]:
    db = await get_db()
    cursor = await db.execute(
        """
        UPDATE jobs
        SET status = 'claimed', updated_at = datetime('now')
        WHERE id IN (
            SELECT id FROM jobs WHERE status = 'queued' LIMIT ?
        )
        RETURNING id
        """,
        (limit,),
    )
    rows = await cursor.fetchall()
    await db.commit()
    return [row[0] for row in rows]
