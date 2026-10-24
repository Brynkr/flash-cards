"""Keyboard controls for visual flashcard study (not typed answer modes)."""
import tkinter as tk
import unittest
from unittest.mock import patch

import constants
from tk_layout_maker import TkLayoutMaker


class StudyKeyboardShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.geometry("100x100+0+0")
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display unavailable: {error}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root') and cls.root.winfo_exists():
            cls.root.destroy()

    def setUp(self):
        self.window = tk.Toplevel(self.root)
        self.layout = TkLayoutMaker()
        self.called = []
        self.constants_patch = patch.multiple(
            constants, create=True, BUTTON_ANSWER_TEXT='Answer',
            BUTTON_NEXT_TEXT='Next', BUTTON_PRIORITY_TEXT='Priority',
            BUTTON_RETURN_TEXT='Return',
        )
        self.constants_patch.start()

    def tearDown(self):
        self.constants_patch.stop()
        if self.window.winfo_exists():
            self.window.destroy()

    def press(self, sequence, widget=None):
        target = widget or self.window
        self.window.update()
        target.focus_force()
        self.window.update()
        target.event_generate(sequence, when='tail')
        self.window.update()

    def front(self):
        self.layout.create_display_front_layout(
            self.window, 'example',
            lambda: self.called.append('reveal'),
            lambda: self.called.append('return'),
        )

    def back(self, priority=False):
        self.layout.create_display_back_layout(
            self.window, 'example', 'translation', priority,
            lambda: self.called.append('next'),
            lambda: self.called.append('priority'),
            lambda: self.called.append('return'),
        )

    def test_front_space_reveals(self):
        self.front()
        self.press('<space>')
        self.assertEqual(self.called, ['reveal'])

    def test_front_escape_returns(self):
        self.front()
        self.press('<Escape>')
        self.assertEqual(self.called, ['return'])

    def test_front_enter_remains_reveal(self):
        self.front()
        self.press('<Return>')
        self.assertEqual(self.called, ['reveal'])

    def test_back_space_advances(self):
        self.back()
        self.press('<space>')
        self.assertEqual(self.called, ['next'])

    def test_priority_back_space_advances(self):
        self.back(priority=True)
        self.press('<space>')
        self.assertEqual(self.called, ['next'])

    def test_back_escape_returns(self):
        self.back()
        self.press('<Escape>')
        self.assertEqual(self.called, ['return'])

    def test_focused_button_does_not_also_trigger_window_space(self):
        self.front()
        button = next(w for w in self.all_widgets(self.window)
                      if isinstance(w, tk.Button)
                      and w.cget('text') == 'Return')
        self.press('<space>', button)
        # The button's own keyboard action may differ by Tk platform, but
        # Space must never trigger the window's default Reveal action too.
        self.assertNotIn('reveal', self.called)

    def test_input_study_has_no_new_space_binding(self):
        self.layout.create_input_front_layout(
            self.window, 'example',
            lambda: self.called.append('answer'),
            lambda: self.called.append('return'),
            lambda text: None,
        )
        self.assertFalse(self.window.bind('<space>'))

    @classmethod
    def all_widgets(cls, parent):
        for widget in parent.winfo_children():
            yield widget
            yield from cls.all_widgets(widget)


if __name__ == '__main__':
    unittest.main()
