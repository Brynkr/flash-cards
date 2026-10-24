"""Daily goals and streaks; all data and settings are temporary."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from study_core.goals import (
    DEFAULT_DAILY_GOAL, load_daily_target, load_goals, save_daily_target
)
from study_core.history import ReviewHistory


@dataclass
class Card:
    english: str
    chinese: str


NOW = datetime(2026, 10, 24, 16, tzinfo=timezone(timedelta(hours=13)))


class GoalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.db = self.dir / 'flashcards.db'
        self.settings = self.dir / 'study_goals.json'
        self.cards = [Card('One', 'yī 一'), Card('Two', 'èr 二')]

    def record(self, days_ago, front='One', back='yī 一', correct=True):
        ReviewHistory(self.db).record_review(
            front, back, correct,
            reviewed_at=NOW - timedelta(days=days_ago),
        )

    def report(self, *, now=NOW, cards=None):
        return load_goals(self.cards if cards is None else cards,
                          db_path=self.db, settings_path=self.settings, now=now)

    def test_empty_history_is_read_only(self):
        summary = self.report()
        self.assertFalse(self.db.exists())
        self.assertFalse(self.settings.exists())
        self.assertEqual((summary.target, summary.completed_today,
                          summary.current_streak, summary.longest_streak),
                         (DEFAULT_DAILY_GOAL, 0, 0, 0))

    def test_single_review_today_starts_streak(self):
        self.record(0)
        summary = self.report()
        self.assertEqual((summary.completed_today, summary.current_streak,
                          summary.longest_streak), (1, 1, 1))
        self.assertFalse(summary.goal_reached)
        self.assertEqual(summary.remaining, DEFAULT_DAILY_GOAL - 1)

    def test_correct_and_incorrect_both_count(self):
        self.record(0, correct=False)
        self.record(0, correct=True)
        self.assertEqual(self.report().completed_today, 2)

    def test_consecutive_days_and_repeated_reviews(self):
        for day in [0, 0, 1, 2, 4, 5]:
            self.record(day)
        summary = self.report()
        self.assertEqual(summary.completed_today, 2)
        self.assertEqual(summary.current_streak, 3)
        self.assertEqual(summary.longest_streak, 3)

    def test_yesterday_keeps_streak_alive(self):
        for day in [1, 2]:
            self.record(day)
        self.assertEqual(self.report().current_streak, 2)
        self.assertEqual(self.report().completed_today, 0)

    def test_streak_breaks_after_missing_two_days(self):
        for day in [2, 3, 4]:
            self.record(day)
        summary = self.report()
        self.assertEqual((summary.current_streak, summary.longest_streak), (0, 3))

    def test_longest_streak_can_exceed_current(self):
        for day in [9, 10, 11, 12, 0, 1]:
            self.record(day)
        summary = self.report()
        self.assertEqual((summary.current_streak, summary.longest_streak), (2, 4))

    def test_removed_cards_are_not_included(self):
        self.record(0, 'Old', 'jiù 旧')
        self.assertEqual(self.report().completed_today, 0)

    def test_duplicate_deck_cards_count_review_once(self):
        self.record(0)
        self.assertEqual(self.report(cards=self.cards + [self.cards[0]]).completed_today, 1)

    def test_new_day_local_timezone_is_honoured(self):
        utc_stamp = datetime(2026, 10, 23, 23, 55, tzinfo=timezone.utc)
        ReviewHistory(self.db).record_review('One','yī 一',True, reviewed_at=utc_stamp)
        self.assertEqual(self.report().completed_today, 1)

    def test_future_reviews_do_not_count(self):
        self.record(-2)
        self.assertEqual(self.report().completed_today, 0)

    def test_target_is_saved_and_round_trips(self):
        save_daily_target(2, self.settings)
        self.record(0)
        self.record(0)
        summary = self.report()
        self.assertTrue(summary.goal_reached)
        self.assertEqual(summary.remaining, 0)
        self.assertEqual(load_daily_target(self.settings), 2)

    def test_invalid_targets_rejected_without_written_file(self):
        for value in (0, 501, -1, True, 3.5, '7', None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                save_daily_target(value, self.settings)
        self.assertFalse(self.settings.exists())

    def test_invalid_existing_settings_report_error_not_silent_reset(self):
        self.settings.write_text(json.dumps({'version': 1, 'daily_goal': '5'}))
        with self.assertRaises(ValueError):
            self.report()

    def test_unrecognised_sqlite_version_raises(self):
        ReviewHistory(self.db)
        with sqlite3.connect(self.db) as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaises(RuntimeError):
            self.report()

    def test_reading_does_not_mutate_db(self):
        self.record(0)
        before = self.db.read_bytes()
        self.report()
        self.assertEqual(before, self.db.read_bytes())

    def test_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            self.report(now=datetime(2026, 10, 24))


if __name__ == '__main__':
    unittest.main()
