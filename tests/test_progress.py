"""Progress tests use a temporary database, never a personal study profile."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

from study_core.history import ReviewHistory
from study_core.progress import load_progress


@dataclass
class Card:
    english: str
    chinese: str


NOW = datetime(2026, 10, 24, 12, tzinfo=timezone(timedelta(hours=13)))


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db = Path(self.tempdir.name) / "my cards" / "flashcards.db"
        self.cards = [Card("Hello", "nǐ hǎo 你好"), Card("Bye", "zài jiàn 再见")]

    def record(self, english, chinese, correct, when=NOW, mode="input"):
        ReviewHistory(self.db).record_review(
            english, chinese, correct, reviewed_at=when, mode=mode
        )

    def progress(self, cards=None, *, now=NOW):
        return load_progress(self.cards if cards is None else cards,
                             db_path=self.db, now=now)

    def test_missing_database_is_not_created(self):
        snapshot = self.progress()
        self.assertFalse(self.db.exists())
        self.assertEqual((snapshot.total_cards, snapshot.reviewed_cards,
                          snapshot.due_cards, snapshot.attempts), (2, 0, 2, 0))
        self.assertIsNone(snapshot.accuracy_percent)

    def test_correct_and_incorrect_attempts_and_accuracy(self):
        self.record("Hello", "nǐ hǎo 你好", True)
        self.record("Hello", "nǐ hǎo 你好", False)
        report = self.progress()
        self.assertEqual((report.reviewed_cards, report.attempts,
                          report.correct, report.accuracy_percent), (1, 2, 1, 50))
        self.assertEqual(report.due_cards, 2)

    def test_new_card_due_and_recent_success_not_due(self):
        self.record("Hello", "nǐ hǎo 你好", True)
        self.assertEqual(self.progress().due_cards, 1)

    def test_repeated_success_uses_same_scheduler_rules(self):
        self.record("Hello", "nǐ hǎo 你好", True, NOW - timedelta(days=4))
        self.record("Hello", "nǐ hǎo 你好", True, NOW - timedelta(days=2))
        self.assertEqual(self.progress().due_cards, 1)  # second success = 3-day interval

    def test_removed_card_history_is_excluded(self):
        self.record("Old", "jiù 旧", True)
        self.assertEqual(self.progress().attempts, 0)

    def test_duplicate_cards_share_one_unique_identity(self):
        repeated = [self.cards[0], self.cards[0]]
        self.record("Hello", "nǐ hǎo 你好", True)
        self.assertEqual(self.progress(repeated).total_cards, 1)
        self.assertEqual(self.progress(repeated).attempts, 1)

    def test_empty_deck(self):
        self.record("Hello", "nǐ hǎo 你好", True)
        result = self.progress([])
        self.assertEqual((result.total_cards, result.reviewed_cards,
                          result.attempts, result.due_cards), (0, 0, 0, 0))

    def test_seven_day_counts_and_local_timezone(self):
        self.record("Hello", "nǐ hǎo 你好", True,
                    NOW - timedelta(days=6, hours=1))
        self.record("Hello", "nǐ hǎo 你好", False,
                    NOW - timedelta(days=7))
        self.record("Hello", "nǐ hǎo 你好", True, NOW)
        totals = [count for _, count in self.progress().daily_reviews]
        self.assertEqual(totals, [1, 0, 0, 0, 0, 0, 1])

    def test_review_events_count_even_if_self_rated(self):
        self.record("Hello", "nǐ hǎo 你好", False, mode="self-rated")
        self.assertEqual(self.progress().attempts, 1)

    def test_invalid_naive_now_rejected(self):
        with self.assertRaises(ValueError):
            self.progress(now=datetime(2026, 10, 24))

    def test_database_contents_remain_unchanged(self):
        self.record("Hello", "nǐ hǎo 你好", True)
        before = self.db.read_bytes()
        self.progress()
        self.assertEqual(self.db.read_bytes(), before)

    def test_unsupported_database_version_is_not_misreported_as_zero(self):
        ReviewHistory(self.db)
        with sqlite3.connect(self.db) as db:
            db.execute("PRAGMA user_version = 99")
        with self.assertRaises(RuntimeError):
            self.progress()


if __name__ == "__main__":
    unittest.main()
