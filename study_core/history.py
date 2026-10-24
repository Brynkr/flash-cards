"""Local SQLite record of flash-card review outcomes.

Iteration 3A deliberately does not change the deck or GUI. Later integrations
can call ReviewHistory.record_review() after grading a typed answer.
"""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import unicodedata

import constants


@dataclass(frozen=True)
class ReviewEvent:
    id: int
    reviewed_at: datetime
    correct: bool
    mode: str


@dataclass(frozen=True)
class ReviewSummary:
    total: int
    correct: int
    incorrect: int
    last_reviewed_at: datetime | None


def card_key(front: str, back: str) -> str:
    """Deterministic key; unlike Card.id, it survives application restarts.

    The key intentionally changes if the card content changes. Assigning
    permanent card IDs and migrating history across edits is a later feature.
    """
    if not isinstance(front, str) or not isinstance(back, str):
        raise TypeError("front and back must both be strings")
    front = unicodedata.normalize("NFC", front.strip())
    back = unicodedata.normalize("NFC", back.strip())
    if not front or not back:
        raise ValueError("front and back must both be nonempty")
    payload = json.dumps([front, back], ensure_ascii=False, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


class ReviewHistory:
    """Append-only review history, stored locally with the Python stdlib.

    By default, the database is beside the configured cards.txt. Supplying
    ``path`` makes tests or alternate profiles independent of the real deck.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else Path(constants.CARD_PATH).with_name("flashcards.db")
        self.path = self.path.expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            with db:
                version = db.execute("PRAGMA user_version").fetchone()[0]
                if version not in (0, 1):
                    raise RuntimeError(f"Unsupported review database version: {version}")
                db.execute("""
                    CREATE TABLE IF NOT EXISTS review_events (
                        id INTEGER PRIMARY KEY,
                        card_key TEXT NOT NULL,
                        reviewed_at TEXT NOT NULL,
                        correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
                        mode TEXT NOT NULL CHECK (mode IN ('input', 'self-rated'))
                    )
                """)
                db.execute("""
                    CREATE INDEX IF NOT EXISTS ix_review_events_card_time
                    ON review_events (card_key, reviewed_at DESC, id DESC)
                """)
                if version == 0:
                    db.execute("PRAGMA user_version = 1")

    def record_review(
        self,
        front: str,
        back: str,
        correct: bool,
        *,
        mode: str = "input",
        reviewed_at: datetime | None = None,
    ) -> int:
        """Add one graded review and return its row ID.

        ``reviewed_at`` must be timezone-aware; times are stored in UTC.
        The user's typed response is deliberately not stored.
        """
        key = card_key(front, back)
        if type(correct) is not bool:
            raise TypeError("correct must be a boolean")
        if mode not in ("input", "self-rated"):
            raise ValueError("mode must be 'input' or 'self-rated'")
        if reviewed_at is None:
            reviewed_at = datetime.now(timezone.utc)
        if not isinstance(reviewed_at, datetime) or reviewed_at.tzinfo is None or reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be a timezone-aware datetime")
        timestamp = reviewed_at.astimezone(timezone.utc).isoformat(timespec="microseconds")
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            with db:
                cur = db.execute(
                    "INSERT INTO review_events (card_key, reviewed_at, correct, mode) VALUES (?, ?, ?, ?)",
                    (key, timestamp, int(correct), mode),
                )
                return cur.lastrowid

    def reviews_for(self, front: str, back: str, *, limit: int | None = None) -> list[ReviewEvent]:
        """Return the latest events first. Each entry represents one attempt."""
        key = card_key(front, back)
        if limit is not None and (type(limit) is not int or limit <= 0):
            raise ValueError("limit must be a positive integer")
        sql = """SELECT id, reviewed_at, correct, mode
                 FROM review_events WHERE card_key = ?
                 ORDER BY reviewed_at DESC, id DESC"""
        parameters: tuple = (key,)
        if limit is not None:
            sql += " LIMIT ?"
            parameters = (key, limit)
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            rows = db.execute(sql, parameters).fetchall()
        return [ReviewEvent(row_id, datetime.fromisoformat(when), bool(correct), mode)
                for row_id, when, correct, mode in rows]

    def summary_for(self, front: str, back: str) -> ReviewSummary:
        """Summarize attempts on one card without loading all the events."""
        key = card_key(front, back)
        with closing(sqlite3.connect(self.path, timeout=10)) as db:
            total, correct, last = db.execute(
                """SELECT COUNT(*), COALESCE(SUM(correct), 0), MAX(reviewed_at)
                   FROM review_events WHERE card_key = ?""",
                (key,),
            ).fetchone()
        return ReviewSummary(total, correct, total - correct,
                             datetime.fromisoformat(last) if last is not None else None)
