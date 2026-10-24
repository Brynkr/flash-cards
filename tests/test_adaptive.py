"""v1.2 experimental scheduling: all tests use synthetic times/private SQLite."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

from study_core.adaptive import adaptive_schedule_from_events, adaptive_schedule_for_card
from study_core.history import ReviewEvent, ReviewHistory
from study_core.scheduler import schedule_for_card


T0 = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)


def event(identifier, days_ago, correct, *, at=None):
    return ReviewEvent(identifier, at or T0 - timedelta(days=days_ago), correct, "input")


class AdaptiveScheduleTests(unittest.TestCase):
    def test_ungraded_cards_not_review_due(self):
        status = adaptive_schedule_from_events([], now=T0)
        self.assertIsNone(status.due_at)
        self.assertFalse(status.is_due)
        self.assertEqual((status.review_count, status.interval_days), (0, 0))

    def test_first_correct_earns_one_day(self):
        result = adaptive_schedule_from_events([event(1, 0, True)], now=T0)
        self.assertEqual(result.interval_days, 1)
        self.assertEqual(result.due_at, T0 + timedelta(days=1))
        self.assertFalse(result.is_due)

    def test_uninterrupted_successes_grow_to_sixty_days(self):
        expected = [1, 3, 7, 14, 30, 45, 60, 60, 60]
        for n, interval in enumerate(expected, 1):
            reviews = [event(i, n - i, True) for i in range(1, n + 1)]
            status = adaptive_schedule_from_events(reviews, now=T0)
            self.assertEqual(status.interval_days, interval)
            self.assertEqual(status.correct_streak, n)

    def test_wrong_answer_resets_streak_and_due_immediately(self):
        reviews = [event(1, 4, True), event(2, 3, True), event(3, 0, False)]
        status = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual((status.correct_streak, status.interval_days), (0, 0))
        self.assertTrue(status.is_due)
        self.assertEqual(status.due_at, T0)

    def test_wrong_answer_not_due_before_occurrence(self):
        result = adaptive_schedule_from_events([event(1, 0, False)],
                                               now=T0 - timedelta(microseconds=1))
        self.assertFalse(result.is_due)

    def test_second_success_after_miss_remains_shorter(self):
        reviews = [event(1, 2, False), event(2, 1, True), event(3, 0, True)]
        status = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual(status.correct_streak, 2)
        self.assertEqual(status.recent_mistakes, 1)
        self.assertEqual(status.interval_days, 1)  # v1.1 would use three.

    def test_two_recent_mistakes_reduce_interval_by_two_levels(self):
        reviews = [event(1, 6, False), event(2, 5, False)]
        reviews += [event(i, 6 - i, True) for i in range(3, 7)]
        status = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual(status.correct_streak, 4)
        self.assertEqual(status.recent_mistakes, 2)
        self.assertEqual(status.interval_days, 3)  # Four-success baseline: 14.

    def test_penalty_is_limited_to_two_steps(self):
        reviews = [event(i, 8 - i, False) for i in range(1, 5)]
        reviews += [event(i, 8 - i, True) for i in range(5, 9)]
        status = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual(status.recent_mistakes, 4)
        self.assertEqual(status.interval_days, 3)

    def test_recovery_after_eight_correct_reviews(self):
        reviews = [event(1, 8, False)]
        reviews += [event(i, 9 - i, True) for i in range(2, 10)]
        status = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual(status.correct_streak, 8)
        self.assertEqual(status.recent_mistakes, 0)
        self.assertEqual(status.interval_days, 60)

    def test_due_time_boundary_is_inclusive(self):
        start = event(1, 0, True)
        due = T0 + timedelta(days=1)
        self.assertFalse(adaptive_schedule_from_events([start], now=due - timedelta(microseconds=1)).is_due)
        self.assertTrue(adaptive_schedule_from_events([start], now=due).is_due)

    def test_equal_timestamp_uses_highest_id_for_latest(self):
        reviews = [event(2, 0, False), event(1, 0, True)]
        result = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual((result.correct_streak, result.interval_days), (0, 0))

    def test_unsorted_events_use_chronological_order(self):
        reviews = [event(3, 0, True), event(1, 3, False), event(2, 1, True)]
        result = adaptive_schedule_from_events(reviews, now=T0)
        self.assertEqual(result.correct_streak, 2)
        self.assertEqual(result.interval_days, 1)

    def test_non_utc_timezone_is_normalized(self):
        nzdt = T0.astimezone(timezone(timedelta(hours=13)))
        result = adaptive_schedule_from_events(
            [event(1, 0, True, at=nzdt)],
            now=(T0 + timedelta(days=1)).astimezone(timezone(timedelta(hours=13))),
        )
        self.assertEqual(result.due_at, T0 + timedelta(days=1))
        self.assertEqual(result.due_at.tzinfo, timezone.utc)
        self.assertTrue(result.is_due)

    def test_naive_now_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "now"):
            adaptive_schedule_from_events([], now=datetime(2026, 10, 24))

    def test_naive_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "reviewed_at"):
            adaptive_schedule_from_events([
                ReviewEvent(1, datetime(2026, 10, 24), True, "input")
            ], now=T0)


class AdaptiveHistoryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db_path = Path(temp.name) / "flashcards.db"
        self.history = ReviewHistory(self.db_path)
        self.front, self.back = "Apple", "píng guǒ 苹果"

    def test_reads_existing_history_without_mutating_database(self):
        self.history.record_review(self.front, self.back, False, reviewed_at=T0 - timedelta(days=2))
        self.history.record_review(self.front, self.back, True, reviewed_at=T0)
        with sqlite3.connect(self.db_path) as connection:
            before = list(connection.execute("SELECT * FROM review_events ORDER BY id"))
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        result = adaptive_schedule_for_card(self.history, self.front, self.back, now=T0)
        self.assertEqual(result.interval_days, 1)
        with sqlite3.connect(self.db_path) as connection:
            after = list(connection.execute("SELECT * FROM review_events ORDER BY id"))
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], user_version)
        self.assertEqual(after, before)

    def test_existing_v11_scheduler_unchanged(self):
        for i in range(6):
            self.history.record_review(self.front, self.back, True,
                                       reviewed_at=T0 - timedelta(days=5 - i))
        old = schedule_for_card(self.history, self.front, self.back, now=T0)
        new = adaptive_schedule_for_card(self.history, self.front, self.back, now=T0)
        self.assertEqual(old.interval_days, 30)
        self.assertEqual(new.interval_days, 45)
        self.assertEqual(old.due_at, T0 + timedelta(days=30))
        self.assertEqual(new.due_at, T0 + timedelta(days=45))

    def test_card_identity_is_preserved(self):
        self.history.record_review(self.front, self.back, False, reviewed_at=T0)
        self.assertEqual(adaptive_schedule_for_card(self.history, self.front, self.back, now=T0).review_count, 1)
        self.assertEqual(adaptive_schedule_for_card(self.history, self.front, "other", now=T0).review_count, 0)
