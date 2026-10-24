"""Iteration 3C deterministic scheduling, using only temporary SQLite files."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from study_core.history import ReviewEvent, ReviewHistory
from study_core.scheduler import due_cards, schedule_for_card, schedule_from_events


T0 = datetime(2026, 10, 24, 4, 0, tzinfo=timezone.utc)


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "flashcards.db"
        self.history = ReviewHistory(self.path)
        self.front = "Can"
        self.back = "kě yǐ 可以 / néng 能"

    def record(self, correct, time):
        self.history.record_review(self.front, self.back, correct, reviewed_at=time)

    def status(self, now=T0):
        return schedule_for_card(self.history, self.front, self.back, now=now)

    def test_new_card_is_due_now_without_writing_records(self):
        status = self.status()
        self.assertTrue(status.is_due)
        self.assertIsNone(status.due_at)
        self.assertEqual((status.correct_streak, status.interval_days), (0, 0))
        self.assertEqual(self.history.reviews_for(self.front, self.back), [])

    def test_first_correct_earns_one_day(self):
        self.record(True, T0)
        self.assertEqual(self.status().due_at, T0 + timedelta(days=1))
        self.assertFalse(self.status().is_due)
        self.assertEqual(self.status().correct_streak, 1)

    def test_second_correct_earns_three_days_from_latest_review(self):
        self.record(True, T0 - timedelta(days=4))
        self.record(True, T0)
        status = self.status()
        self.assertEqual((status.correct_streak, status.interval_days), (2, 3))
        self.assertEqual(status.due_at, T0 + timedelta(days=3))

    def test_third_correct_earns_seven_days(self):
        for n in (3, 2, 0):
            self.record(True, T0 - timedelta(days=n))
        self.assertEqual(self.status().interval_days, 7)
        self.assertEqual(self.status().due_at, T0 + timedelta(days=7))

    def test_fourth_and_fifth_earn_fourteen_and_thirty_days(self):
        for i in range(4):
            self.record(True, T0 + timedelta(days=i))
        self.assertEqual(self.status(now=T0 + timedelta(days=3)).interval_days, 14)
        self.record(True, T0 + timedelta(days=4))
        self.assertEqual(self.status(now=T0 + timedelta(days=4)).interval_days, 30)

    def test_interval_caps_at_thirty_days_after_many_successes(self):
        for i in range(8):
            self.record(True, T0 + timedelta(days=i))
        self.assertEqual(self.status(now=T0 + timedelta(days=7)).interval_days, 30)
        self.assertEqual(self.status(now=T0 + timedelta(days=7)).correct_streak, 8)

    def test_wrong_answer_is_immediately_due_and_resets_streak(self):
        self.record(True, T0 - timedelta(days=2))
        self.record(True, T0 - timedelta(days=1))
        self.record(False, T0)
        status = self.status()
        self.assertTrue(status.is_due)
        self.assertEqual((status.correct_streak, status.interval_days), (0, 0))
        self.assertEqual(status.due_at, T0)

    def test_success_after_wrong_restarts_at_one_day(self):
        self.record(True, T0 - timedelta(days=3))
        self.record(True, T0 - timedelta(days=2))
        self.record(False, T0 - timedelta(days=1))
        self.record(True, T0)
        self.assertEqual((self.status().correct_streak, self.status().interval_days), (1, 1))

    def test_due_boundary_is_inclusive(self):
        self.record(True, T0)
        due = T0 + timedelta(days=1)
        self.assertFalse(self.status(due - timedelta(microseconds=1)).is_due)
        self.assertTrue(self.status(due).is_due)
        self.assertTrue(self.status(due + timedelta(seconds=1)).is_due)

    def test_wrong_answer_cannot_be_due_before_it_happened(self):
        self.record(False, T0)
        self.assertFalse(self.status(T0 - timedelta(seconds=1)).is_due)
        self.assertTrue(self.status(T0).is_due)

    def test_new_card_due_with_no_timezone_dependence(self):
        local = timezone(timedelta(hours=13))
        self.record(True, T0.astimezone(local))
        status = self.status(now=(T0 + timedelta(days=1)).astimezone(local))
        self.assertTrue(status.is_due)
        self.assertEqual(status.due_at.tzinfo, timezone.utc)

    def test_out_of_order_and_equal_timestamp_use_db_id_tiebreak(self):
        events = [
            ReviewEvent(1, T0, True, "input"),
            ReviewEvent(3, T0, False, "input"),
            ReviewEvent(2, T0 - timedelta(days=1), True, "input"),
        ]
        status = schedule_from_events(events, now=T0)
        self.assertTrue(status.is_due)
        self.assertEqual(status.correct_streak, 0)

    def test_rejects_naive_now_without_modifying_db(self):
        with self.assertRaisesRegex(ValueError, "now"):
            self.status(datetime(2026, 10, 24))
        self.assertEqual(self.history.reviews_for(self.front, self.back), [])

    def test_rejects_naive_event_time(self):
        event = ReviewEvent(1, datetime(2026, 10, 24), True, "input")
        with self.assertRaisesRegex(ValueError, "reviewed_at"):
            schedule_from_events([event], now=T0)

    def test_due_cards_preserves_order_and_does_not_modify_history(self):
        cards = [
            SimpleNamespace(english="New", chinese="xīn 新"),
            SimpleNamespace(english=self.front, chinese=self.back),
            SimpleNamespace(english="Wrong", chinese="cuò 错"),
        ]
        self.record(True, T0)
        self.history.record_review("Wrong", "cuò 错", False, reviewed_at=T0)
        result = due_cards(cards, self.history, now=T0)
        self.assertEqual(result, [cards[0], cards[2]])
        self.assertEqual(self.history.summary_for(self.front, self.back).total, 1)
        self.assertEqual(self.history.summary_for("Wrong", "cuò 错").total, 1)

    def test_due_cards_respects_review_and_exact_identity(self):
        cards = [
            SimpleNamespace(english=self.front, chinese=self.back),
            SimpleNamespace(english=self.front, chinese="néng 能"),
        ]
        self.record(True, T0)
        self.assertEqual(due_cards(cards, self.history, now=T0), [cards[1]])

    def test_persistent_database_yields_identical_schedule_after_reopen(self):
        self.record(True, T0)
        expected = self.status(now=T0 + timedelta(hours=4))
        reopened = ReviewHistory(self.path)
        self.assertEqual(schedule_for_card(reopened, self.front, self.back,
                                           now=T0 + timedelta(hours=4)), expected)

    def test_latest_incorrect_and_self_rated_are_supported(self):
        self.history.record_review(self.front, self.back, False,
                                   mode="self-rated", reviewed_at=T0)
        self.assertTrue(self.status().is_due)
