"""User-facing scheduler settings must affect Review Due, without mutating history."""
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from tk_gui import GUI


class ReviewSettingsIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.gui = GUI.__new__(GUI)
        self.gui.root = object()
        self.gui._categories = {'All': False}
        self.card = SimpleNamespace(english='Example', chinese='例子')
        self.gui._deck_handler = SimpleNamespace(
            cards=[self.card], filter_cards_by_category=Mock(return_value=[self.card])
        )
        self.gui._review_history = object()
        self.gui._input_answer_poll = Mock(return_value='Correct')
        self.gui._show_completion = Mock()

    def test_stored_standard_uses_original_selector(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch('tk_gui.load_review_mode', return_value='standard'), \
             patch('tk_gui.prioritized_due_cards', return_value=[self.card]) as old, \
             patch('tk_gui.adaptive_due_cards') as adaptive:
            self.gui.review_due()
        old.assert_called_once()
        adaptive.assert_not_called()

    def test_saved_adaptive_uses_adaptive_selector(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch('tk_gui.load_review_mode', return_value='adaptive'), \
             patch('tk_gui.prioritized_due_cards') as old, \
             patch('tk_gui.adaptive_due_cards', return_value=[self.card]) as adaptive:
            self.gui.review_due()
        adaptive.assert_called_once()
        old.assert_not_called()

    def test_environment_override_remains_enabled(self):
        with patch.dict(os.environ, {'FLASHCARDS_ADAPTIVE_REVIEWS': '1'}), \
             patch('tk_gui.load_review_mode') as load, \
             patch('tk_gui.adaptive_due_cards', return_value=[]), \
             patch('tk_gui.messagebox.showinfo'):
            self.gui.review_due()
        load.assert_not_called()

    def test_bad_settings_show_warning_instead_of_starting_review(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch('tk_gui.load_review_mode', side_effect=ValueError('invalid')), \
             patch('tk_gui.prioritized_due_cards') as old, \
             patch('tk_gui.messagebox.showwarning') as warn:
            self.gui.review_due()
        warn.assert_called_once()
        old.assert_not_called()

    def test_user_can_save_selected_adaptive_preference(self):
        with patch('tk_gui.load_review_mode', return_value='standard'), \
             patch('tk_gui.choose_review_mode', return_value='adaptive') as choose, \
             patch('tk_gui.save_review_mode') as save:
            self.gui.review_settings()
        choose.assert_called_once_with(self.gui.root, 'standard')
        save.assert_called_once_with('adaptive')

    def test_cancel_does_not_save(self):
        with patch('tk_gui.load_review_mode', return_value='adaptive'), \
             patch('tk_gui.choose_review_mode', return_value=None), \
             patch('tk_gui.save_review_mode') as save:
            self.gui.review_settings()
        save.assert_not_called()

    def test_settings_corrupt_does_not_open_editor(self):
        with patch('tk_gui.load_review_mode', side_effect=ValueError('corrupt')), \
             patch('tk_gui.messagebox.showwarning') as warn, \
             patch('tk_gui.choose_review_mode') as choose:
            self.gui.review_settings()
        warn.assert_called_once()
        choose.assert_not_called()

    def test_save_failure_warns_instead_of_hiding_error(self):
        with patch('tk_gui.load_review_mode', return_value='standard'), \
             patch('tk_gui.choose_review_mode', return_value='adaptive'), \
             patch('tk_gui.save_review_mode', side_effect=OSError('disk full')), \
             patch('tk_gui.messagebox.showwarning') as warn:
            self.gui.review_settings()
        warn.assert_called_once()


if __name__ == '__main__':
    unittest.main()
