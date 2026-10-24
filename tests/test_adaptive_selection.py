"""Adaptive Review Due selection: synthetic events only, no personal data."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from study_core.adaptive import adaptive_due_cards
from study_core.history import ReviewHistory
from study_core.scheduler import prioritized_due_cards

T0 = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


def card(name):
    return SimpleNamespace(english=name, chinese=f"meaning of {name}")


class AdaptiveSelectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.history = ReviewHistory(Path(temp.name) / "reviews.db")

    def grade(self, item, correct, days_ago):
        self.history.record_review(item.english, item.chinese, correct,
                                   reviewed_at=T0 - timedelta(days=days_ago))

    def test_unstudied_cards_are_never_in_adaptive_review_due(self):
        self.assertEqual(adaptive_due_cards([card("new")], self.history, now=T0), [])

    def test_recent_miss_is_immediately_due(self):
        missed = card("missed")
        self.grade(missed, False, 0)
        self.assertEqual(adaptive_due_cards([missed], self.history, now=T0), [missed])

    def test_first_success_waits_one_day(self):
        correct = card("correct")
        self.grade(correct, True, 0)
        self.assertEqual(adaptive_due_cards([correct], self.history, now=T0), [])
        self.assertEqual(adaptive_due_cards([correct], self.history,
                                            now=T0 + timedelta(days=1)), [correct])

    def test_twice_correct_after_miss_due_adaptive_but_not_legacy(self):
        difficult = card("difficult")
        self.grade(difficult, False, 5)
        self.grade(difficult, True, 4)
        self.grade(difficult, True, 2)
        self.assertEqual(prioritized_due_cards([difficult], self.history, now=T0), [])
        self.assertEqual(adaptive_due_cards([difficult], self.history, now=T0), [difficult])

    def test_six_successes_get_longer_interval_than_legacy(self):
        strong = card("strong")
        for days_ago in (50, 45, 40, 35, 33, 32):
            self.grade(strong, True, days_ago)
        # The v1.1 30-day interval has passed, but v1.2's 45-day hasn't.
        self.assertEqual(prioritized_due_cards([strong], self.history, now=T0), [strong])
        self.assertEqual(adaptive_due_cards([strong], self.history, now=T0), [])

    def test_incorrect_latest_before_older_correct(self):
        wrong, correct = card("wrong"), card("correct")
        self.grade(wrong, False, 0)
        self.grade(correct, True, 5)
        self.assertEqual(adaptive_due_cards([correct, wrong], self.history,
                                            now=T0), [wrong, correct])

    def test_overdue_before_less_overdue(self):
        older, newer = card("older"), card("newer")
        self.grade(older, True, 10)
        self.grade(newer, True, 3)
        self.assertEqual(adaptive_due_cards([newer, older], self.history,
                                            now=T0), [older, newer])

    def test_equal_priorities_stay_in_deck_order(self):
        a, b = card("a"), card("b")
        self.grade(a, False, 0)
        self.grade(b, False, 0)
        self.assertEqual(adaptive_due_cards([b, a], self.history, now=T0), [b, a])

    def test_selecting_does_not_change_existing_history(self):
        first = card("first")
        self.grade(first, False, 0)
        before = self.history.reviews_for(first.english, first.chinese)
        self.assertEqual(adaptive_due_cards([first], self.history, now=T0), [first])
        self.assertEqual(self.history.reviews_for(first.english, first.chinese), before)

    def test_timezone_aware_now_is_required(self):
        with self.assertRaisesRegex(ValueError, "now"):
            adaptive_due_cards([], self.history, now=datetime(2026, 10, 24))


if __name__ == "__main__":
    unittest.main()
