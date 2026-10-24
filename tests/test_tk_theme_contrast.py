"""Contrast and widget-level tests for the macOS-compatible light theme."""
import tkinter as tk
import unittest
from unittest.mock import patch

import constants

from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


def contrast_ratio(a, b):
    def brightness(value):
        levels = [int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
        rgb = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
               for v in levels]
        return sum(left * right for left, right in zip(rgb, (0.2126, 0.7152, 0.0722)))
    high, low = sorted((brightness(a), brightness(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class ThemeContrastTests(unittest.TestCase):
    def setUp(self):
        self.layout = TkLayoutMaker()

    def test_main_text_contrasts_with_background(self):
        self.assertGreaterEqual(contrast_ratio(self.layout.fg_color, self.layout.bg_color), 7)

    def test_buttons_and_input_text_are_readable(self):
        self.assertGreaterEqual(contrast_ratio(self.layout.fg_color, self.layout.button_bg), 7)
        self.assertGreaterEqual(contrast_ratio(self.layout.fg_color, self.layout.entry_bg), 7)

    def test_feedback_colors_are_readable(self):
        for name in ('yellow_color', 'green_color', 'red_color'):
            with self.subTest(name=name):
                self.assertGreaterEqual(
                    contrast_ratio(getattr(self.layout, name), self.layout.bg_color), 4.5)

    def test_buttons_use_dark_text_and_light_active_background(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'No Tk display: {exc}')
        root.withdraw()
        self.addCleanup(root.destroy)
        button = self.layout._create_button(root, 'Review Due', lambda: None)
        self.assertEqual(button.cget('fg'), self.layout.fg_color)
        self.assertEqual(button.cget('bg'), self.layout.button_bg)
        self.assertEqual(button.cget('activeforeground'), self.layout.fg_color)
        self.assertEqual(button.cget('activebackground'), self.layout.button_active_bg)

    def test_answer_and_add_card_entries_are_light(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'No Tk display: {exc}')
        root.withdraw()
        self.addCleanup(root.destroy)
        study = tk.Toplevel(root)
        # Some older test fixtures omit legacy GUI button text constants.
        with patch.object(constants, 'BUTTON_ANSWER_TEXT', 'Answer', create=True):
            self.layout.create_input_front_layout(study, 'Water', lambda: None,
                                                  lambda: None, lambda value: None)
        entry = next(w for w in study.winfo_children()[0].winfo_children()
                     if isinstance(w, tk.Entry))
        self.assertEqual(entry.cget('bg'), self.layout.entry_bg)
        self.assertEqual(entry.cget('fg'), self.layout.fg_color)
        add = tk.Toplevel(root)
        self.layout.create_add_cards_layout(add, lambda: None,
                                            lambda: None, lambda value: None, 'start')
        add_entry = next(w for w in add.winfo_children()[0].winfo_children()
                         if isinstance(w, tk.Entry))
        self.assertEqual(add_entry.cget('bg'), self.layout.entry_bg)

    def test_gui_theme_uses_layout_palette(self):
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'No Tk display: {exc}')
        root.withdraw()
        self.addCleanup(root.destroy)
        gui = GUI.__new__(GUI)
        gui.root = root
        gui._layout_maker = self.layout
        gui._apply_theme()
        self.assertEqual(root.cget('bg'), self.layout.bg_color)
        from tkinter import ttk
        style = ttk.Style(root)
        self.assertEqual(style.lookup('TButton', 'foreground'), self.layout.fg_color)


if __name__ == '__main__':
    unittest.main()
