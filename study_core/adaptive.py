"""Experimental, read-only adaptive review dates for Flashcards v1.2.

Not used by the v1.1 Review Due interface yet. These suggestions are derived
from existing graded ReviewEvent records; no data is written or migrated.

Policy (intentionally simple and deterministic, not SM-2 or FSRS):
- ungraded cards have no review date and are *not* eligible for Review Due;
- a miss resets the correct streak and is eligible again immediately;
- successive correct reviews increase the interval (up to 60 days);
- each mistake in the last eight attempts reduces the interval one step,
  capped at two steps; after eight consecutive successes old mistakes no
  longer affect the schedule.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from study_core.history import ReviewEvent, ReviewHistory


_INTERVALS_DAYS = (1, 3, 7, 14, 30, 45, 60)
_RECENT_WINDOW = 8
_MAX_PENALTY = 2


@dataclass(frozen=True)
class AdaptiveSchedule:
    due_at: datetime | None
    is_due: bool
    correct_streak: int
    interval_days: int
    recent_mistakes: int
    review_count: int


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def adaptive_schedule_from_events(
    events: Iterable[ReviewEvent], *, now: datetime | None = None
) -> AdaptiveSchedule:
    """Compute a potential v1.2 review date without changing any records.

    Sort by UTC timestamp and DB ID so source query ordering is irrelevant.
    An ungraded card is not a due review; it belongs in the learning modes.
    """
    current = _utc(now if now is not None else datetime.now(timezone.utc), "now")
    ordered = list(events)
    # Validate and normalize before sorting (including non-UTC timezones).
    chronological = [(_utc(event.reviewed_at, "reviewed_at"), event.id, event)
                     for event in ordered]
    chronological.sort(key=lambda row: (row[0], row[1]), reverse=True)
    count = len(chronological)
    if not count:
        return AdaptiveSchedule(None, False, 0, 0, 0, 0)

    recent = chronological[:_RECENT_WINDOW]
    recent_mistakes = sum(not row[2].correct for row in recent)
    latest_at = chronological[0][0]

    streak = 0
    for _, _, event in chronological:
        if not event.correct:
            break
        streak += 1

    if not streak:
        # A miss is due again as soon as it has occurred.
        interval_days = 0
    else:
        base_index = min(streak - 1, len(_INTERVALS_DAYS) - 1)
        penalty = min(_MAX_PENALTY, recent_mistakes)
        interval_days = _INTERVALS_DAYS[max(0, base_index - penalty)]

    due = latest_at + timedelta(days=interval_days)
    return AdaptiveSchedule(
        due_at=due,
        is_due=current >= due,
        correct_streak=streak,
        interval_days=interval_days,
        recent_mistakes=recent_mistakes,
        review_count=count,
    )


def adaptive_schedule_for_card(
    history: ReviewHistory, front: str, back: str, *, now: datetime | None = None
) -> AdaptiveSchedule:
    """Read only: consult the existing append-only SQLite review records."""
    return adaptive_schedule_from_events(history.reviews_for(front, back), now=now)
