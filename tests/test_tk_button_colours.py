"""Iteration 3G: independently saved, readable button colours and the small popup."""
import json
import tkinter as tk
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from study_core.appearance import (
    BACKGROUND_PRESETS, BUTTON_PRESETS, DEFAULT_BUTTON, active_button_color,
    contrast_ratio, is_readable_button, load_background, load_buttons,
    save_background, save_buttons,
)
from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


def descendants(widget, klass):
    for child in widget.winfo_children():
        if isinstance(child, klass):
            yield child
        yield from descendants(child, klass)


class ButtonPreferencesTests(unittest.TestCase):
    def test_twelve_unique_options_and_default(self):
        self.assertEqual(len(BUTTON_PRESETS), len(BACKGROUND_PRESETS))
        self.assertEqual(len(BUTTON_PRESETS), 12)
        self.assertEqual(len(set(n for n, _ in BUTTON_PRESETS)), 12)
        self.assertEqual(len(set(c for _, c in BUTTON_PRESETS)), 12)
        self.assertEqual(BUTTON_PRESETS[0], ('Default', DEFAULT_BUTTON))

    def test_every_option_and_active_colour_is_readable(self):
        for name, colour in BUTTON_PRESETS:
            with self.subTest(name=name):
                self.assertTrue(is_readable_button(colour))
                self.assertGreaterEqual(contrast_ratio('#17212B', colour), 7)
                self.assertGreaterEqual(
                    contrast_ratio('#17212B', active_button_color(colour)), 7)

    def test_bad_custom_colours_are_rejected(self):
        for colour in ('#111111', 'navy', '#12345', None, ''):
            with self.subTest(colour=colour):
                self.assertFalse(is_readable_button(colour))

    def test_default_invalid_and_corrupt_preferences(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / '.flashcards-appearance.json'
            self.assertEqual(load_buttons(path), DEFAULT_BUTTON)
            path.write_text('{invalid json', encoding='utf-8')
            self.assertEqual(load_buttons(path), DEFAULT_BUTTON)
            path.write_text('{"buttons":"#000000"}', encoding='utf-8')
            self.assertEqual(load_buttons(path), DEFAULT_BUTTON)

    def test_background_and_buttons_survive_each_others_saves(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / '.flashcards-appearance.json'
            save_background(path, '#EBF5EC')
            save_buttons(path, '#E0D3F1')
            self.assertEqual(load_background(path), '#EBF5EC')
            self.assertEqual(load_buttons(path), '#E0D3F1')
            save_background(path, '#F5D8C6')
            self.assertEqual(load_buttons(path), '#E0D3F1')
            save_buttons(path, '#D0E5D6')
            self.assertEqual(load_background(path), '#F5D8C6')
            self.assertEqual(json.loads(path.read_text())['buttons'], '#D0E5D6')

    def test_invalid_button_save_preserves_previous_settings(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'appearance.json'
            save_background(path, '#EAF4FC')
            save_buttons(path, '#E0D3F1')
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                save_buttons(path, '#202020')
            self.assertEqual(path.read_bytes(), original)


class ButtonPopupTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as e:
            self.skipTest(f'Tk display unavailable: {e}')
        self.root.withdraw()
        self.addCleanup(lambda: self.root.destroy() if self.root.winfo_exists() else None)

    def make_gui(self, preference):
        gui = GUI.__new__(GUI)
        gui.root = self.root
        gui.current_window = tk.Toplevel(self.root)
        gui._layout_maker = TkLayoutMaker()
        gui._appearance_path = preference
        gui._deck_handler = Mock(cards=[object(), object()])
        gui._on_menu_selection = Mock()
        return gui

    def test_buttons_control_is_small_and_below_background(self):
        window = tk.Toplevel(self.root)
        layout = TkLayoutMaker()
        bg_callback, button_callback = Mock(), Mock()
        layout.create_start_layout(window, 2, Mock(), bg_callback, button_callback)
        window.update_idletasks()
        by_text = {b.cget('text'): b for b in descendants(window, tk.Button)}
        for label in ('Background', 'Buttons'):
            self.assertLess(int(by_text[label].cget('height')),
                            int(by_text['Study'].cget('height')))
            self.assertLess(int(by_text[label].cget('width')),
                            int(by_text['Study'].cget('width')))
        self.assertEqual(by_text['Buttons'].pack_info()['side'], 'right')
        # Distinct rows, below the Background row.
        self.assertNotEqual(by_text['Buttons'].master, by_text['Background'].master)
        self.assertGreater(by_text['Buttons'].winfo_rooty(),
                           by_text['Background'].winfo_rooty())
        by_text['Buttons'].invoke()
        button_callback.assert_called_once_with()
        bg_callback.assert_not_called()
        window.destroy()

    def test_popup_has_twelve_options_and_selects_one(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / '.flashcards-appearance.json'
            gui = self.make_gui(path)
            gui._pick_buttons()
            popup = next(child for child in gui.current_window.winfo_children()
                         if isinstance(child, tk.Toplevel))
            frame = next(child for child in popup.winfo_children()
                         if isinstance(child, tk.Frame))
            rows = [child for child in frame.winfo_children()
                    if isinstance(child, tk.Frame)]
            self.assertEqual(len(rows), 6)
            choices = [b for b in descendants(popup, tk.Button)
                       if b.cget('text') in dict(BUTTON_PRESETS)]
            self.assertEqual(len(choices), 12)
            next(b for b in choices if b.cget('text') == 'Lavender').invoke()
            self.assertFalse(popup.winfo_exists())
            self.assertEqual(gui._layout_maker.button_bg, '#E0D3F1')
            self.assertEqual(load_buttons(path), '#E0D3F1')
            gui.current_window.destroy()

    def test_background_and_button_changes_keep_each_other(self):
        with TemporaryDirectory() as folder:
            gui = self.make_gui(Path(folder) / 'settings.json')
            self.assertTrue(gui._set_button_colour('#D0E5D6'))
            self.assertTrue(gui._set_background_colour('#EBF5EC'))
            self.assertEqual(gui._layout_maker.button_bg, '#D0E5D6')
            self.assertEqual(gui._layout_maker.bg_color, '#EBF5EC')
            self.assertEqual(load_buttons(gui._appearance_path), '#D0E5D6')
            self.assertEqual(load_background(gui._appearance_path), '#EBF5EC')
            gui.current_window.destroy()

    def test_reject_dark_button_without_writing(self):
        with TemporaryDirectory() as folder:
            gui = self.make_gui(Path(folder) / 'settings.json')
            with patch('tk_gui.messagebox.showwarning') as warning:
                self.assertFalse(gui._set_button_colour('#000000'))
            warning.assert_called_once()
            self.assertFalse(gui._appearance_path.exists())
            gui.current_window.destroy()

    def test_mac_fallback_face_uses_selected_colour_and_calls_button(self):
        layout = TkLayoutMaker()
        layout.button_bg = '#E0D3F1'
        layout.button_active_bg = active_button_color(layout.button_bg)
        pressed = Mock()
        with patch('tk_layout_maker._mac_buttons_need_overlay', return_value=True):
            button = layout._create_button(self.root, 'Press me', pressed)
        button.pack()
        self.root.update_idletasks()
        face = button._coloured_face
        self.assertEqual(face.cget('bg'), '#E0D3F1')
        self.assertEqual(face.cget('text'), 'Press me')
        button.invoke()
        pressed.assert_called_once_with()
        button.destroy()


if __name__ == '__main__':
    unittest.main()
