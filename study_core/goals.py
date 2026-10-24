"""Daily study goals and streaks, calculated from existing graded review events.

A graded review of a current deck card counts once, regardless of correctness.
Browsing flashcards, Auto Study and changing a daily target never count.
Loading goals is read-only; only explicit goal changes write a small JSON file.
"""
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Iterable

import constants
from study_core.history import card_key

DEFAULT_DAILY_GOAL = 10
MIN_DAILY_GOAL = 1
MAX_DAILY_GOAL = 500


@dataclass(frozen=True)
class GoalSummary:
    target: int
    completed_today: int
    current_streak: int
    longest_streak: int
    last_study_day: date | None

    @property
    def goal_reached(self) -> bool:
        return self.completed_today >= self.target

    @property
    def remaining(self) -> int:
        return max(0, self.target - self.completed_today)


def settings_file() -> Path:
    return Path(constants.CARD_PATH).expanduser().with_name('study_goals.json')


def _validate_target(value: int) -> int:
    if type(value) is not int or not MIN_DAILY_GOAL <= value <= MAX_DAILY_GOAL:
        raise ValueError(f'Daily goal must be an integer from {MIN_DAILY_GOAL} to {MAX_DAILY_GOAL}')
    return value


def load_daily_target(path: Path | str | None = None) -> int:
    path = Path(path) if path is not None else settings_file()
    if not path.exists():
        return DEFAULT_DAILY_GOAL
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or document.get('version') != 1:
        raise ValueError('Unsupported study goal settings format')
    return _validate_target(document.get('daily_goal'))


def save_daily_target(value: int, path: Path | str | None = None) -> None:
    """Atomically store the target only when the user explicitly saves it."""
    value = _validate_target(value)
    path = Path(path) if path is not None else settings_file()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = json.dumps({'version': 1, 'daily_goal': value}, sort_keys=True) + '\n'
    temp = None
    try:
        fd, name = tempfile.mkstemp(dir=path.parent, prefix='.study-goals-', suffix='.tmp')
        temp = Path(name)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(payload)
        os.chmod(temp, 0o600)
        os.replace(temp, path)
        temp = None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def load_goals(
    cards: Iterable,
    *,
    db_path: Path | str | None = None,
    settings_path: Path | str | None = None,
    now: datetime | None = None,
) -> GoalSummary:
    """Read existing graded reviews without ever creating or modifying SQLite.

    Count only events for cards still in this deck, consistent with Progress.
    Current streak remains alive until midnight after an unreviewed day.
    """
    local_now = now if now is not None else datetime.now().astimezone()
    if not isinstance(local_now, datetime) or local_now.tzinfo is None or local_now.utcoffset() is None:
        raise ValueError('now must be a timezone-aware datetime')
    target = load_daily_target(settings_path)
    keys = {card_key(card.english, card.chinese) for card in cards}
    db_path = (Path(db_path) if db_path is not None else
               Path(constants.CARD_PATH).with_name('flashcards.db')).expanduser()
    counts = Counter()
    if db_path.is_file():
        uri = db_path.resolve().as_uri() + '?mode=ro'
        with closing(sqlite3.connect(uri, uri=True, timeout=5)) as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError(f'Unsupported review database version: {version}')
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='review_events'"
            ).fetchone() is not None
            if not exists and version == 1:
                raise RuntimeError('Review database has no review_events table')
            if exists and keys:
                for key, stamp in db.execute('SELECT card_key, reviewed_at FROM review_events'):
                    if key not in keys:
                        continue
                    when = datetime.fromisoformat(stamp)
                    if when.tzinfo is None or when.utcoffset() is None:
                        raise ValueError('Review database has a timestamp without timezone')
                    day = when.astimezone(local_now.tzinfo).date()
                    if day <= local_now.date():
                        counts[day] += 1
    today = local_now.date()
    reviewed_days = sorted(counts)
    longest = 0
    run = 0
    previous = None
    for day in reviewed_days:
        run = run + 1 if previous == day - timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day
    cursor = today if counts[today] else today - timedelta(days=1)
    current = 0
    while counts[cursor]:
        current += 1
        cursor -= timedelta(days=1)
    return GoalSummary(
        target=target, completed_today=counts[today], current_streak=current,
        longest_streak=longest, last_study_day=reviewed_days[-1] if reviewed_days else None,
    )
