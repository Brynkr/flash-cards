"""Read-only regression tests for intelligent Review Due ordering."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from study_core.history import ReviewHistory
from study_core.scheduler import due_cards, prioritized_due_cards, schedule_for_card

NOW = datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc)


def card(name):
    return SimpleNamespace(english=name, chinese='translation: ' + name)


class PrioritizedReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.history = ReviewHistory(Path(temporary.name) / 'history.db')

    def record(self, c, correct, when):
        self.history.record_review(c.english, c.chinese, correct, reviewed_at=when)

    def test_failed_card_before_older_overdue_without_new_card(self):
        new, old, failed, future = map(card, ('New', 'Old', 'Failed', 'Future'))
        self.record(old, True, NOW - timedelta(days=10))
        self.record(failed, False, NOW - timedelta(minutes=15))
        self.record(future, True, NOW)
        self.assertEqual(prioritized_due_cards([new, old, failed, future],
                                               self.history, now=NOW),
                         [failed, old])

    def test_more_overdue_review_first(self):
        recent, older = map(card, ('Recent', 'Older'))
        self.record(recent, True, NOW - timedelta(days=2))
        self.record(older, True, NOW - timedelta(days=8))
        self.assertEqual(prioritized_due_cards([recent, older], self.history,
                                               now=NOW), [older, recent])

    def test_previous_mistakes_break_equal_overdue_ties(self):
        easy, hard = map(card, ('Easy', 'Hard'))
        self.record(easy, True, NOW - timedelta(days=2))
        self.record(hard, False, NOW - timedelta(days=3))
        self.record(hard, True, NOW - timedelta(days=2))
        self.assertEqual(prioritized_due_cards([easy, hard], self.history,
                                               now=NOW), [hard, easy])

    def test_new_cards_are_not_interleaved_with_due_reviews(self):
        reviewed = [card(f'Reviewed{i}') for i in range(6)]
        unseen = [card('New1'), card('New2')]
        for item in reviewed:
            self.record(item, False, NOW - timedelta(days=1))
        got = prioritized_due_cards(unseen + reviewed, self.history, now=NOW)
        self.assertEqual(got, reviewed)

    def test_unseen_cards_are_excluded_even_if_all_cards_are_new(self):
        cards = [card('One'), card('Two'), card('Three')]
        self.assertEqual(prioritized_due_cards(cards, self.history, now=NOW), [])

    def test_equal_priority_preserves_input_order(self):
        cards = [card('First'), card('Second')]
        for item in cards:
            self.record(item, False, NOW - timedelta(hours=1))
        self.assertEqual(prioritized_due_cards(cards, self.history, now=NOW), cards)

    def test_original_due_cards_order_is_unchanged(self):
        new, wrong = card('New'), card('Wrong')
        self.record(wrong, False, NOW)
        self.assertEqual(due_cards([new, wrong], self.history, now=NOW), [new, wrong])
        self.assertEqual(prioritized_due_cards([new, wrong], self.history, now=NOW), [wrong])

    def test_selection_does_not_write_reviews_or_change_interval(self):
        seen = card('Seen')
        self.record(seen, True, NOW - timedelta(days=2))
        expected = schedule_for_card(self.history, seen.english, seen.chinese, now=NOW)
        initial = self.history.summary_for(seen.english, seen.chinese).total
        for _ in range(2):
            self.assertEqual(prioritized_due_cards([seen], self.history, now=NOW), [seen])
        self.assertEqual(self.history.summary_for(seen.english, seen.chinese).total, initial)
        self.assertEqual(schedule_for_card(self.history, seen.english, seen.chinese,
                                           now=NOW), expected)


    def test_all_reviewed_cards_not_yet_due_produces_empty_list(self):
        unseen, future = card('Unseen'), card('Future')
        self.record(future, True, NOW)
        self.assertEqual(prioritized_due_cards([unseen, future], self.history,
                                               now=NOW), [])

    def test_card_with_only_viewing_and_no_grading_is_not_review_due(self):
        # Merely viewing a card does not generate a graded history event.
        unseen = card('Viewed but not graded')
        self.assertEqual(prioritized_due_cards([unseen], self.history,
                                               now=NOW), [])
        self.assertEqual(self.history.summary_for(unseen.english,
                                                  unseen.chinese).total, 0)

    def test_invalid_time_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'now'):
            prioritized_due_cards([card('One')], self.history,
                                  now=datetime(2026, 10, 24))


if __name__ == '__main__':
    unittest.main()
