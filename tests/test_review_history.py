"""Database tests isolated from real vocabulary and study progress."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from study_core.history import ReviewHistory, card_key


class ReviewHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.path = Path(self.tempdir.name) / "profile" / "flashcards.db"
        self.history = ReviewHistory(self.path)
        self.front = "Can"
        self.back = "kě yǐ 可以 / néng 能"

    def test_creates_local_database_and_directory(self):
        self.assertTrue(self.path.is_file())
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)

    def test_database_stays_empty_before_a_review(self):
        self.assertEqual(self.history.reviews_for(self.front, self.back), [])
        self.assertEqual(self.history.summary_for(self.front, self.back).total, 0)

    def test_records_correct_and_incorrect_reviews(self):
        self.history.record_review(self.front, self.back, True)
        self.history.record_review(self.front, self.back, False)
        summary = self.history.summary_for(self.front, self.back)
        self.assertEqual((summary.total, summary.correct, summary.incorrect), (2, 1, 1))

    def test_persists_across_instances(self):
        self.history.record_review(self.front, self.back, True)
        reopened = ReviewHistory(self.path)
        self.assertEqual(reopened.summary_for(self.front, self.back).total, 1)

    def test_different_cards_do_not_share_history(self):
        self.history.record_review(self.front, self.back, True)
        self.assertEqual(self.history.summary_for("No", "bù shì 不是").total, 0)

    def test_latest_first_even_if_inserted_out_of_order(self):
        old = datetime(2026, 10, 1, tzinfo=timezone.utc)
        new = datetime(2026, 10, 4, tzinfo=timezone.utc)
        self.history.record_review(self.front, self.back, True, reviewed_at=new)
        self.history.record_review(self.front, self.back, False, reviewed_at=old)
        results = self.history.reviews_for(self.front, self.back)
        self.assertEqual([event.correct for event in results], [True, False])
        self.assertEqual(self.history.summary_for(self.front, self.back).last_reviewed_at, new)

    def test_limit_and_equal_timestamp_tiebreak(self):
        when = datetime(2026, 10, 2, tzinfo=timezone.utc)
        self.history.record_review(self.front, self.back, False, reviewed_at=when)
        later_id = self.history.record_review(self.front, self.back, True, reviewed_at=when)
        self.assertEqual([r.id for r in self.history.reviews_for(self.front, self.back, limit=1)], [later_id])

    def test_rejects_invalid_limit(self):
        for value in (0, -1, True, "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.history.reviews_for(self.front, self.back, limit=value)

    def test_rejects_wrong_types_for_correct(self):
        for value in (1, 0, None, "yes"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                self.history.record_review(self.front, self.back, value)
        self.assertEqual(self.history.summary_for(self.front, self.back).total, 0)

    def test_rejects_unrecognised_mode(self):
        with self.assertRaises(ValueError):
            self.history.record_review(self.front, self.back, True, mode="unknown")

    def test_rejects_naive_datetime(self):
        with self.assertRaises(ValueError):
            self.history.record_review(self.front, self.back, True, reviewed_at=datetime(2026, 10, 1))

    def test_converts_offset_to_utc(self):
        nzdt = datetime(2026, 10, 1, 12, tzinfo=timezone(timedelta(hours=13)))
        self.history.record_review(self.front, self.back, True, reviewed_at=nzdt)
        when = self.history.reviews_for(self.front, self.back)[0].reviewed_at
        self.assertEqual(when, datetime(2026, 9, 30, 23, tzinfo=timezone.utc))

    def test_card_key_survives_restart_and_unicode_normalization(self):
        self.assertEqual(card_key("  Café ", self.back), card_key("Cafe\u0301", self.back))
        self.assertEqual(card_key(self.front, self.back), card_key(self.front, self.back))
        self.assertNotEqual(card_key("ab", "c"), card_key("a", "bc"))

    def test_rejects_blank_or_invalid_identity(self):
        with self.assertRaises(ValueError):
            card_key("", "中")
        with self.assertRaises(TypeError):
            card_key(None, "中")

    def test_supports_self_rated_mode(self):
        self.history.record_review(self.front, self.back, False, mode="self-rated")
        self.assertEqual(self.history.reviews_for(self.front, self.back)[0].mode, "self-rated")

    def test_rejects_newer_unknown_database_version(self):
        other = Path(self.tempdir.name) / "new_version.db"
        with sqlite3.connect(other) as db:
            db.execute("PRAGMA user_version = 99")
        with self.assertRaisesRegex(RuntimeError, "Unsupported"):
            ReviewHistory(other)

    def test_default_path_follows_configured_cards_path(self):
        import constants
        configured = str(Path(self.tempdir.name) / "another" / "cards.txt")
        with patch.object(constants, "CARD_PATH", configured):
            default_history = ReviewHistory()
        self.assertEqual(default_history.path, Path(configured).with_name("flashcards.db"))


if __name__ == "__main__":
    unittest.main()
