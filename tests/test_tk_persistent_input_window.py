"""v1.3 Stage 2: Input Study / Review Due Q and feedback reuse one window."""
import tkinter as tk
import unittest
from dataclasses import dataclass
from unittest.mock import Mock, patch

import constants
from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


@dataclass
class Card:
    english: str
    chinese: str


class PersistentInputStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as exc:
            raise unittest.SkipTest(f'Tk display unavailable: {exc}')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root') and cls.root.winfo_exists():
            cls.root.destroy()

    def setUp(self):
        self.gui = GUI.__new__(GUI)
        self.gui.root = self.root
        self.gui._fullscreen = False
        self.gui._categories = {'Any': True}
        self.cards = [Card('first', '一'), Card('second', '二')]
        self.gui._deck_handler = Mock()
        self.gui._deck_handler.cards = self.cards
        self.gui._deck_handler.filter_cards_by_category.side_effect = (
            lambda cards, categories: list(cards)
        )
        self.gui._deck_handler.correct_answer.side_effect = (
            lambda answer, entered: entered == answer
        )
        self.gui._record_input_review = Mock()
        self.gui._show_completion = Mock()
        self.gui._layout_maker = TkLayoutMaker()
        self.views = []
        self.scenarios = ['correct', 'incorrect']
        self.feedback_close = False
        self.front_return = False
        self.front_close = False
        self.double_submit = False
        self.positions = []
        self._patches = []
        self._settings = patch.object(constants, 'ANSWER_DISPLAY_DELAY_SEC', 0.06)
        self._settings.start()
        self._attach_callbacks()

    def tearDown(self):
        for patcher in self._patches:
            patcher.stop()
        self._settings.stop()
        self.gui._close_input_study_surface()

    def _record_geometry(self, window, view):
        window.update_idletasks()
        self.views.append((view, window))
        window.after(5, lambda: self.positions.append((
            window.winfo_x(), window.winfo_y(),
            window.winfo_width(), window.winfo_height()
        )))

    def _attach_callbacks(self):
        orig_front = self.gui._layout_maker.create_input_front_layout
        orig_correct = self.gui._layout_maker.create_input_back_layout
        orig_incorrect = self.gui._layout_maker.create_incorrect_layout

        def front(window, key, answer, ret, changed):
            orig_front(window, key, answer, ret, changed)
            self._record_geometry(window, 'Q')
            if self.front_return:
                window.after(15, ret)
            elif self.front_close:
                window.after(15, lambda: window.tk.call(
                    window.protocol('WM_DELETE_WINDOW')))
            else:
                which = self.scenarios[len([v for v, _ in self.views if v == 'Q']) - 1]
                value = '一' if which == 'correct' else 'WRONG'
                # Answer contents are ephemeral; no personal history DB is touched.
                def submit():
                    changed(value)
                    answer()
                    if self.double_submit:
                        answer()
                window.after(15, submit)

        def correct(window, key, value):
            orig_correct(window, key, value)
            self._record_geometry(window, 'A-correct')
            if self.feedback_close:
                window.after(15, lambda: window.tk.call(
                    window.protocol('WM_DELETE_WINDOW')))

        def incorrect(window, key, value):
            orig_incorrect(window, key, value)
            self._record_geometry(window, 'A-incorrect')
            if self.feedback_close:
                window.after(15, lambda: window.tk.call(
                    window.protocol('WM_DELETE_WINDOW')))

        for name, callback in (
            ('create_input_front_layout', front),
            ('create_input_back_layout', correct),
            ('create_incorrect_layout', incorrect),
        ):
            p = patch.object(self.gui._layout_maker, name, side_effect=callback)
            p.start()
            self._patches.append(p)

    def test_multiple_cards_one_window_and_two_recorded_attempts(self):
        outputs = [self.gui._input_answer_poll(c) for c in self.cards]
        self.assertEqual(outputs, ['Correct', 'Incorrect'])
        self.assertEqual([view for view, window in self.views],
                         ['Q', 'A-correct', 'Q', 'A-incorrect'])
        self.assertEqual(len({id(window) for view, window in self.views}), 1)
        self.gui._record_input_review.assert_any_call(self.cards[0], True)
        self.gui._record_input_review.assert_any_call(self.cards[1], False)
        self.assertEqual(self.gui._record_input_review.call_count, 2)

    def test_geometry_does_not_jump_for_short_cards(self):
        for card in self.cards:
            self.gui._input_answer_poll(card)
        self.assertTrue(all(g == self.positions[0] for g in self.positions),
                        self.positions)

    def test_double_submit_records_only_once(self):
        self.double_submit = True
        self.assertEqual(self.gui._input_answer_poll(self.cards[0]), 'Correct')
        self.gui._record_input_review.assert_called_once_with(self.cards[0], True)

    def test_return_without_submission_never_records(self):
        self.front_return = True
        output = self.gui._input_answer_poll(self.cards[0])
        self.assertEqual(output, constants.BUTTON_RETURN_TEXT)
        self.gui._record_input_review.assert_not_called()
        self.assertEqual([v for v, _ in self.views], ['Q'])

    def test_window_close_without_submission_never_records(self):
        self.front_close = True
        output = self.gui._input_answer_poll(self.cards[0])
        self.assertEqual(output, constants.BUTTON_RETURN_TEXT)
        self.gui._record_input_review.assert_not_called()

    def test_close_during_feedback_aborts_without_second_attempt(self):
        self.feedback_close = True
        output = self.gui._input_answer_poll(self.cards[0])
        self.assertEqual(output, constants.BUTTON_RETURN_TEXT)
        self.gui._record_input_review.assert_called_once_with(self.cards[0], True)

    def test_explicit_cleanup_destroys_shared_window(self):
        self.gui._input_answer_poll(self.cards[0])
        window = self.views[0][1]
        self.assertTrue(window.winfo_exists())
        self.gui._close_input_study_surface()
        self.assertFalse(window.winfo_exists())
        self.assertIsNone(self.gui._input_study_window)

    def test_input_study_closes_surface_before_completion(self):
        self.scenarios = ['correct', 'incorrect']
        self.gui._show_completion.side_effect = (
            lambda: self.assertIsNone(self.gui._input_study_window)
        )
        self.gui.input_study()
        self.assertEqual(len([v for v, _ in self.views if v == 'Q']), 2)
        self.gui._show_completion.assert_called_once()
        self.assertIsNone(self.gui._input_study_window)


if __name__ == '__main__':
    unittest.main()
