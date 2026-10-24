"""v1.3: verify Q/A visual Study reuses a Toplevel; no personal data reads."""
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


class PersistentVisualStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as error:
            raise unittest.SkipTest(f'Tk display not available: {error}')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root') and cls.root.winfo_exists():
            cls.root.destroy()

    def setUp(self):
        self.gui = GUI.__new__(GUI)
        self.gui.root = self.root
        self.gui._fullscreen = False
        self.gui._categories = {'Any': True}
        self.cards = [Card('one', '一'), Card('two', '二')]
        self.gui._deck_handler = Mock()
        self.gui._deck_handler.cards = self.cards
        self.gui._deck_handler.recent_cards = self.cards[:1]
        self.gui._deck_handler.priority_cards = self.cards[:1]
        self.gui._deck_handler.filter_cards_by_category.side_effect = (
            lambda cards, categories: list(cards)
        )
        self.gui._layout_maker = TkLayoutMaker()
        self.gui._show_completion = Mock()
        self.views = []
        self._patch_buttons()

    def tearDown(self):
        for p in self.patchers:
            p.stop()
        window = getattr(self.gui, '_visual_study_window', None)
        if window is not None and window.winfo_exists():
            window.destroy()

    def _patch_buttons(self, front_action='answer', back_action='next'):
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
        self.patchers = []
        original_front = self.gui._layout_maker.create_display_front_layout
        original_back = self.gui._layout_maker.create_display_back_layout

        def front(window, key, on_answer, on_return):
            original_front(window, key, on_answer, on_return)
            self.views.append(('Q', window, key))
            callback = on_return if front_action == 'return' else on_answer
            window.after(15, callback)

        def back(window, key, value, priority, on_next, on_priority, on_return):
            original_back(window, key, value, priority, on_next, on_priority, on_return)
            self.views.append(('A', window, key))
            choices = {'return': on_return, 'priority': on_priority, 'next': on_next}
            window.after(15, choices[back_action])

        for name, value in [
            ('create_display_front_layout', front),
            ('create_display_back_layout', back),
        ]:
            patcher = patch.object(self.gui._layout_maker, name, side_effect=value)
            patcher.start()
            self.patchers.append(patcher)

    def test_two_cards_share_a_single_window(self):
        # Mocking the class-level Tk constructor counts real study windows.
        real_toplevel = tk.Toplevel
        with patch('tk_gui.tk.Toplevel', wraps=real_toplevel) as new_window, \
             patch('builtins.print'):
            self.gui.display_study()
        self.assertEqual(new_window.call_count, 1)
        self.assertEqual([view[0] for view in self.views], ['Q', 'A', 'Q', 'A'])
        self.assertEqual(len({id(view[1]) for view in self.views}), 1)
        self.assertFalse(self.views[0][1].winfo_exists())
        self.gui._show_completion.assert_called_once()

    def test_return_from_front_closes_session(self):
        self._patch_buttons(front_action='return')
        with patch('builtins.print'):
            self.gui.display_study()
        self.assertEqual([view[0] for view in self.views], ['Q'])
        self.gui._show_completion.assert_not_called()
        self.assertFalse(self.views[0][1].winfo_exists())

    def test_return_from_answer_closes_session(self):
        self._patch_buttons(back_action='return')
        with patch('builtins.print'):
            self.gui.display_study()
        self.assertEqual([view[0] for view in self.views], ['Q', 'A'])
        self.gui._show_completion.assert_not_called()

    def test_window_close_button_returns_without_completion(self):
        original_front = TkLayoutMaker.create_display_front_layout.__get__(
            self.gui._layout_maker, TkLayoutMaker
        )
        for patcher in self.patchers:
            patcher.stop()
        self.patchers = []

        def front(window, key, answer, ret):
            original_front(window, key, answer, ret)
            self.views.append(('Q', window, key))
            # Invoke Tk's real WM_DELETE_WINDOW handler, as the titlebar X does.
            window.after(15, lambda: window.tk.call(
                window.protocol('WM_DELETE_WINDOW')
            ))

        patcher = patch.object(
            self.gui._layout_maker, 'create_display_front_layout',
            side_effect=front,
        )
        patcher.start()
        self.patchers.append(patcher)
        with patch('builtins.print'):
            self.gui.display_study()
        self.assertEqual(len(self.views), 1)
        self.gui._show_completion.assert_not_called()
        self.assertFalse(self.views[0][1].winfo_exists())

    def test_priority_action_still_records_card(self):
        self.gui._deck_handler.priority_cards = self.cards[:1]
        self._patch_buttons(back_action='priority')
        with patch('builtins.print'):
            self.gui.display_study()
        self.assertEqual(self.gui._deck_handler.add_priority_card.call_count, 2)
        self.gui._deck_handler.add_priority_card.assert_any_call('one', '一')
        self.gui._show_completion.assert_called_once()

    def test_back_does_not_move_or_shrink_window(self):
        geometry = []
        original_front = TkLayoutMaker.create_display_front_layout.__get__(
            self.gui._layout_maker, TkLayoutMaker
        )
        original_back = TkLayoutMaker.create_display_back_layout.__get__(
            self.gui._layout_maker, TkLayoutMaker
        )
        for patcher in self.patchers:
            patcher.stop()
        self.patchers = []

        def front(window, key, answer, ret):
            original_front(window, key, answer, ret)
            window.after(25, lambda: (window.update_idletasks(), geometry.append(
                (window.winfo_x(), window.winfo_y(), window.winfo_width(), window.winfo_height())
            ), answer()))

        def back(window, key, val, pr, nxt, priority, ret):
            original_back(window, key, val, pr, nxt, priority, ret)
            window.after(25, lambda: (window.update_idletasks(), geometry.append(
                (window.winfo_x(), window.winfo_y(), window.winfo_width(), window.winfo_height())
            ), nxt()))

        for name, func in [
            ('create_display_front_layout', front),
            ('create_display_back_layout', back),
        ]:
            patcher = patch.object(self.gui._layout_maker, name, side_effect=func)
            patcher.start()
            self.patchers.append(patcher)
        with patch('builtins.print'):
            self.gui.display_study()
        self.assertEqual(len(geometry), 4)
        # Small cards should be displayed inside an entirely stable rectangle.
        self.assertTrue(all(g == geometry[0] for g in geometry), geometry)


if __name__ == '__main__':
    unittest.main()
