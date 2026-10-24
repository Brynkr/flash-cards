"""Deterministic, conservative review scheduling from existing SQLite events.

Iteration 3C is read-only: it does not alter review history, cards.txt, or GUI.
Input to scheduling is the existing append-only review event stream.
All due timestamps are timezone-aware UTC datetimes (not calendar dates).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, TypeVar

from study_core.history import ReviewEvent, ReviewHistory


# Days after successive correct attempts. After five successes, stay at 30 days.
# This is a simple initial schedule, not an SM-2 / FSRS implementation.
_SUCCESS_INTERVAL_DAYS = (1, 3, 7, 14, 30)


@dataclass(frozen=True)
class ReviewSchedule:
    due_at: datetime | None
    is_due: bool
    correct_streak: int
    interval_days: int


def _aware_utc(value: datetime, name: str) -> datetime:
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() is None):
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def schedule_from_events(
    events: Iterable[ReviewEvent], *, now: datetime | None = None
) -> ReviewSchedule:
    """Determine next review from the chronological outcome history.

    New cards are immediately due (due_at=None). After a wrong answer the
    card becomes due at the time of that answer. Correct answers earn intervals
    of 1, 3, 7, 14, and 30 days, capped at 30. An error resets the streak.
    Order is determined by timestamp, then database ID for ties.
    """
    current = _aware_utc(now if now is not None else datetime.now(timezone.utc), "now")
    ordered = list(events)
    for event in ordered:
        _aware_utc(event.reviewed_at, "reviewed_at")
    ordered.sort(key=lambda e: (e.reviewed_at, e.id), reverse=True)

    if not ordered:
        return ReviewSchedule(due_at=None, is_due=True, correct_streak=0, interval_days=0)

    correct_streak = 0
    for event in ordered:
        if not event.correct:
            break
        correct_streak += 1

    days = (_SUCCESS_INTERVAL_DAYS[min(correct_streak, len(_SUCCESS_INTERVAL_DAYS)) - 1]
            if correct_streak else 0)
    last_review = _aware_utc(ordered[0].reviewed_at, "reviewed_at")
    due_at = last_review + timedelta(days=days)
    return ReviewSchedule(due_at=due_at, is_due=current >= due_at,
                          correct_streak=correct_streak, interval_days=days)


def schedule_for_card(
    history: ReviewHistory, front: str, back: str, *, now: datetime | None = None
) -> ReviewSchedule:
    """Read one card's existing review history without adding review records."""
    return schedule_from_events(history.reviews_for(front, back), now=now)


_Card = TypeVar("_Card")


def due_cards(
    cards: Iterable[_Card], history: ReviewHistory, *, now: datetime | None = None
) -> list[_Card]:
    """Filter card objects (with .english/.chinese) in their original order.

    Category filtering, shuffling, and any single-session repeat policy belong
    to the calling study mode, not this read-only scheduler.
    """
    current = _aware_utc(now if now is not None else datetime.now(timezone.utc), "now")
    return [card for card in cards
            if schedule_for_card(history, card.english, card.chinese, now=current).is_due]
