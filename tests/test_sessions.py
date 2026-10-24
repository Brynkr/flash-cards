"""No personal data, GUI or database is needed for session selection tests."""
import unittest
from dataclasses import dataclass
from study_core.sessions import (
    DEFAULT_SESSION_SIZE, SESSION_SIZES, select_session_cards,
)


@dataclass
class Card:
    english: str
    chinese: str


class SessionSelectionTests(unittest.TestCase):
    def setUp(self):
        self.cards = [Card(f"English {i}", f"Chinese {i}") for i in range(65)]

    def test_default_is_twenty(self):
        self.assertEqual(DEFAULT_SESSION_SIZE, "20")
        self.assertEqual(len(select_session_cards(self.cards)), 20)

    def test_preset_options(self):
        self.assertEqual(SESSION_SIZES, ("10", "20", "50", "all"))
        for n in (10, 20, 50):
            with self.subTest(n=n):
                self.assertEqual(len(select_session_cards(self.cards, str(n))), n)

    def test_all_available(self):
        self.assertEqual(select_session_cards(self.cards, "all"), self.cards)

    def test_small_deck_remains_small(self):
        self.assertEqual(select_session_cards(self.cards[:3], "20"), self.cards[:3])

    def test_empty_deck(self):
        self.assertEqual(select_session_cards([], "all"), [])
        self.assertEqual(select_session_cards([], "20"), [])

    def test_preserves_input_order(self):
        reversed_cards = list(reversed(self.cards))
        self.assertEqual(select_session_cards(reversed_cards), reversed_cards[:20])

    def test_duplicate_same_pair_only_once(self):
        selected = select_session_cards(
            [self.cards[0], self.cards[0], Card("English 0", "Chinese 0"),
             self.cards[1]], "all"
        )
        self.assertEqual(selected, [self.cards[0], self.cards[1]])

    def test_same_front_different_back_remains_distinct(self):
        choices = [Card("Same", "A"), Card("Same", "B")]
        self.assertEqual(select_session_cards(choices, "all"), choices)

    def test_skips_duplicate_to_fill_size(self):
        cards = [self.cards[0]] * 6 + self.cards[1:]
        self.assertEqual(select_session_cards(cards, "10"), self.cards[:10])

    def test_does_not_change_source(self):
        cards = self.cards[:]
        select_session_cards(cards, "10")
        self.assertEqual(cards, self.cards)

    def test_rejects_invalid_sizes(self):
        for value in (None, 0, 20, "0", "999", "ALL", "", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                select_session_cards(self.cards, value)


if __name__ == "__main__":
    unittest.main()
