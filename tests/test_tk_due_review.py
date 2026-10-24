"""Iteration 3D: GUI Review Due integration using isolated SQLite data."""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import sqlite3
import tempfile
import tkinter as tk
import unittest

import constants
from study_core.history import ReviewHistory
from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


class _Deck:
    def __init__(self, cards):
        self.cards = cards
        self.filtered = []

    def filter_cards_by_category(self, cards, categories):
        self.filtered.append((cards, categories))
        return [c for c in cards if c.english not in categories.get('exclude', ())]


class ReviewDueTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.history = ReviewHistory(Path(tmp.name) / 'flashcards.db')
        self.new = SimpleNamespace(english='New', chinese='xīn 新')
        self.future = SimpleNamespace(english='Future', chinese='hǎo 好')
        self.missed = SimpleNamespace(english='Missed', chinese='cuò 错')
        self.exclude = SimpleNamespace(english='Exclude', chinese='bù 不')
        self.deck = _Deck([self.new, self.future, self.missed, self.exclude])
        self.categories = {'All': False, 'exclude': ('Exclude',)}
        self.gui = GUI.__new__(GUI)
        self.gui._deck_handler = self.deck
        self.gui._categories = self.categories
        self.gui._review_history = self.history
        self.gui.root = object()
        self.seen = []
        self.gui._input_answer_poll = lambda card: self.seen.append(card.english) or 'Correct'
        self.gui._show_completion = Mock()
        now = datetime.now(timezone.utc)
        self.history.record_review('Future', 'hǎo 好', True, reviewed_at=now)
        self.history.record_review('Missed', 'cuò 错', False, reviewed_at=now)

    def test_reviews_only_due_cards_in_filtered_order(self):
        self.gui.review_due()
        self.assertEqual(self.seen, ['New', 'Missed'])
        self.gui._show_completion.assert_called_once()
        self.assertEqual(self.deck.filtered, [(self.deck.cards, self.categories)])

    def test_selection_does_not_create_new_review_events(self):
        self.gui.review_due()
        self.assertEqual(self.history.reviews_for('New', 'xīn 新'), [])
        self.assertEqual(len(self.history.reviews_for('Missed', 'cuò 错')), 1)

    def test_return_exits_without_showing_completion(self):
        self.gui._input_answer_poll = lambda card: self.seen.append(card.english) or constants.BUTTON_RETURN_TEXT
        self.gui.review_due()
        self.assertEqual(self.seen, ['New'])
        self.gui._show_completion.assert_not_called()

    def test_closed_answer_window_exits_session(self):
        self.gui._input_answer_poll = lambda card: None
        self.gui.review_due()
        self.gui._show_completion.assert_not_called()

    def test_successful_review_is_not_due_in_next_session(self):
        def answer(card):
            self.gui._record_input_review(card, True)
            return 'Correct'
        self.gui._input_answer_poll = answer
        self.gui.review_due()
        self.assertEqual(len(self.history.reviews_for('New', 'xīn 新')), 1)
        self.assertEqual(len(self.history.reviews_for('Missed', 'cuò 错')), 2)
        # Only due again if its future interval elapses.
        self.seen.clear()
        self.gui._input_answer_poll = lambda card: self.seen.append(card.english) or 'Correct'
        with patch('tk_gui.messagebox.showinfo') as info:
            self.gui.review_due()
        self.assertEqual(self.seen, [])
        info.assert_called_once()

    def test_no_due_cards_shows_caught_up(self):
        self.deck.cards = [self.future]
        with patch('tk_gui.messagebox.showinfo') as info:
            self.gui.review_due()
        info.assert_called_once()
        self.assertEqual(self.seen, [])
        self.gui._show_completion.assert_not_called()

    def test_database_read_error_does_not_crash(self):
        class ReadError:
            def reviews_for(self, *_args, **_kwargs):
                raise sqlite3.OperationalError('database busy')
        self.gui._review_history = ReadError()
        with patch('tk_gui.messagebox.showwarning') as warn:
            self.gui.review_due()
        warn.assert_called_once()
        self.gui._show_completion.assert_not_called()
        self.assertEqual(self.seen, [])

    def test_history_is_lazily_created_for_review_due(self):
        self.gui._review_history = None
        with patch('tk_gui.ReviewHistory', return_value=self.history) as factory:
            self.gui.review_due()
        factory.assert_called_once_with()
        self.assertIs(self.gui._review_history, self.history)


class ReviewDueMenuTests(unittest.TestCase):
    def test_menu_button_is_visible_and_invokes_correct_action(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        root.withdraw()
        self.addCleanup(lambda: root.destroy() if root.winfo_exists() else None)
        win = tk.Toplevel(root)
        self.addCleanup(lambda: win.destroy() if win.winfo_exists() else None)
        actions = []
        layout = TkLayoutMaker()
        layout.create_start_layout(win, 5, actions.append)
        def buttons(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Button):
                    yield child
                yield from buttons(child)
        candidates = [b for b in buttons(win) if b['text'] == 'Review Due']
        self.assertEqual(len(candidates), 1)
        candidates[0].invoke()
        self.assertEqual(actions, ['Review Due'])


if __name__ == '__main__':
    unittest.main()
