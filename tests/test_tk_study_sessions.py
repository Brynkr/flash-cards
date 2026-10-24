"""GUI wiring tests; no Tk windows and no personal data are opened."""
import unittest
from dataclasses import dataclass
from unittest.mock import Mock, patch

from tk_gui import GUI


@dataclass
class Card:
    english: str
    chinese: str


class StudySessionGuiTests(unittest.TestCase):
    def setUp(self):
        self.cards = [Card(str(i), str(i)) for i in range(55)]
        self.gui = GUI.__new__(GUI)
        self.gui._categories = {"Any": True}
        self.gui._deck_handler = Mock()
        self.gui._deck_handler.cards = self.cards
        self.gui._deck_handler.recent_cards = self.cards[:5]
        self.gui._deck_handler.priority_cards = self.cards[:3]
        self.gui._deck_handler.filter_cards_by_category.side_effect = lambda cards, cats: list(cards)
        self.gui._show_card_front = Mock(return_value="SHOW_BACK")
        self.gui._show_card_back = Mock(return_value="NEXT")
        self.gui._show_completion = Mock()

    def test_regular_study_limited_to_twenty(self):
        with patch("builtins.print"):
            self.gui.display_study(session_size="20")
        self.assertEqual(self.gui._show_card_front.call_count, 20)
        self.gui._show_completion.assert_called_once()

    def test_regular_study_all_remains_available(self):
        with patch("builtins.print"):
            self.gui.display_study(session_size="all")
        self.assertEqual(self.gui._show_card_front.call_count, 55)

    def test_study_recent_does_not_limit(self):
        with patch("builtins.print"):
            self.gui.display_study(recent=True, session_size="10")
        self.assertEqual(self.gui._show_card_front.call_count, 5)

    def test_priority_study_does_not_limit(self):
        with patch("builtins.print"):
            self.gui.display_study(priority=True, session_size="10")
        self.assertEqual(self.gui._show_card_front.call_count, 3)

    def test_early_return_still_stops_session(self):
        self.gui._show_card_front.return_value = "RETURN"
        with patch("builtins.print"):
            self.gui.display_study(session_size="20")
        self.gui._show_card_front.assert_called_once()
        self.gui._show_completion.assert_not_called()

    def test_duplicate_cards_not_repeated(self):
        self.gui._deck_handler.cards = [self.cards[0]] * 3 + self.cards[1:]
        with patch("builtins.print"):
            self.gui.display_study(session_size="10")
        self.assertEqual(self.gui._show_card_front.call_count, 10)
        cards = [c.args[0] for c in self.gui._show_card_front.call_args_list]
        self.assertEqual(cards, self.cards[:10])


if __name__ == "__main__":
    unittest.main()
