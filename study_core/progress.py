"""Read-only study progress for the current flashcard deck.

Only graded attempts in the existing local review database count as reviews.
Passive card views and Auto Study exposure do not count as learning outcomes.
Opening this view never creates or modifies flashcards.db.
"""

from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Iterable

import constants
from study_core.history import ReviewEvent, card_key
from study_core.scheduler import schedule_from_events


@dataclass(frozen=True)
class ProgressSummary:
    total_cards: int
    reviewed_cards: int
    due_cards: int
    attempts: int
    correct: int
    last_review: datetime | None
    daily_reviews: tuple[tuple[date, int], ...]

    @property
    def accuracy_percent(self) -> int | None:
        """Percent of graded attempts answered correctly; None if no attempts."""
        return round(self.correct * 100 / self.attempts) if self.attempts else None


def load_progress(
    cards: Iterable,
    *,
    db_path: str | Path | None = None,
    now: datetime | None = None,
) -> ProgressSummary:
    """Summarise the unique cards in this deck, without altering any data.

    Counts are based only on cards whose current English/Chinese content matches
    an existing review identity. Edited or removed cards do not inherit an old
    identity. 'Due' includes cards not yet reviewed.
    """
    local_now = now if now is not None else datetime.now().astimezone()
    if not isinstance(local_now, datetime) or local_now.tzinfo is None or local_now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")

    keys = {card_key(card.english, card.chinese) for card in cards}
    events_by_key: dict[str, list[ReviewEvent]] = defaultdict(list)
    path = (Path(db_path) if db_path is not None else
            Path(constants.CARD_PATH).with_name("flashcards.db")).expanduser()

    if path.exists():
        # A read-only URI prevents accidentally creating a database or tables.
        uri = path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=5)) as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError(f"Unsupported review database version: {version}")
            has_table = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'review_events'"
            ).fetchone() is not None
            if not has_table and version == 1:
                raise RuntimeError("Review database has no review_events table")
            if has_table and keys:
                rows = db.execute(
                    "SELECT id, card_key, reviewed_at, correct, mode FROM review_events"
                )
                for row_id, key, reviewed_at, correct, mode in rows:
                    if key in keys:
                        when = datetime.fromisoformat(reviewed_at)
                        if when.tzinfo is None or when.utcoffset() is None:
                            raise ValueError("Review database has a timestamp without timezone")
                        events_by_key[key].append(
                            ReviewEvent(row_id, when, bool(correct), mode)
                        )

    start_day = local_now.date() - timedelta(days=6)
    daily = {start_day + timedelta(days=i): 0 for i in range(7)}
    reviewed_cards = 0
    due = 0
    attempts = 0
    correct = 0
    last = None
    for key in keys:
        events = events_by_key[key]
        if events:
            reviewed_cards += 1
        if schedule_from_events(events, now=local_now).is_due:
            due += 1
        for event in events:
            attempts += 1
            correct += event.correct
            if last is None or event.reviewed_at > last:
                last = event.reviewed_at
            day = event.reviewed_at.astimezone(local_now.tzinfo).date()
            if day in daily:
                daily[day] += 1

    return ProgressSummary(
        total_cards=len(keys), reviewed_cards=reviewed_cards, due_cards=due,
        attempts=attempts, correct=correct, last_review=last,
        daily_reviews=tuple(daily.items()),
    )
