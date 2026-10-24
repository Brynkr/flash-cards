"""Safe opt-in selection; ordinary Review Due behaviour remains the default."""
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from tk_gui import GUI


class OptInReviewDueTests(unittest.TestCase):
    def setUp(self):
        # Avoid dependence on the current user's saved scheduler setting.
        mode_patcher = patch("tk_gui.load_review_mode", return_value="standard")
        mode_patcher.start()
        self.addCleanup(mode_patcher.stop)
        self.gui = GUI.__new__(GUI)
        self.gui._categories = {"All": False}
        self.card = SimpleNamespace(english="Card", chinese="卡")
        self.gui._deck_handler = SimpleNamespace(
            cards=[self.card],
            filter_cards_by_category=Mock(return_value=[self.card]),
        )
        self.gui._review_history = object()
        self.gui.root = object()
        self.gui._input_answer_poll = Mock(return_value="Correct")
        self.gui._show_completion = Mock()

    def test_legacy_review_due_is_the_default(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch("tk_gui.prioritized_due_cards", return_value=[self.card]) as old, \
             patch("tk_gui.adaptive_due_cards") as new:
            self.gui.review_due()
        old.assert_called_once_with([self.card], self.gui._review_history)
        new.assert_not_called()
        self.gui._input_answer_poll.assert_called_once_with(self.card)

    def test_adaptive_opt_in_selects_adaptive_cards(self):
        with patch.dict(os.environ, {"FLASHCARDS_ADAPTIVE_REVIEWS": "1"}), \
             patch("tk_gui.prioritized_due_cards") as old, \
             patch("tk_gui.adaptive_due_cards", return_value=[self.card]) as new:
            self.gui.review_due()
        new.assert_called_once_with([self.card], self.gui._review_history)
        old.assert_not_called()
        self.gui._input_answer_poll.assert_called_once_with(self.card)

    def test_unrecognized_setting_uses_legacy(self):
        with patch.dict(os.environ, {"FLASHCARDS_ADAPTIVE_REVIEWS": "yes"}), \
             patch("tk_gui.prioritized_due_cards", return_value=[self.card]) as old, \
             patch("tk_gui.adaptive_due_cards") as new:
            self.gui.review_due()
        old.assert_called_once()
        new.assert_not_called()

    def test_no_adaptive_due_cards_shows_existing_empty_state(self):
        with patch.dict(os.environ, {"FLASHCARDS_ADAPTIVE_REVIEWS": "1"}), \
             patch("tk_gui.adaptive_due_cards", return_value=[]), \
             patch("tk_gui.messagebox.showinfo") as info:
            self.gui.review_due()
        info.assert_called_once()
        self.gui._input_answer_poll.assert_not_called()
        self.gui._show_completion.assert_not_called()


if __name__ == "__main__":
    unittest.main()
