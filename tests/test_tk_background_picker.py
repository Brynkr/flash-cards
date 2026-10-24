"""Iteration 3E: readable backgrounds and Tkinter popup smoke tests."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from study_core.appearance import (
    BACKGROUND_PRESETS, DEFAULT_BACKGROUND, is_readable_background,
    load_background, preference_path, save_background,
)
from tk_layout_maker import TkLayoutMaker
from tk_gui import GUI


class BackgroundPreferenceTests(unittest.TestCase):
    def test_all_predefined_colours_keep_text_readable(self):
        for name, colour in BACKGROUND_PRESETS:
            with self.subTest(name=name):
                self.assertTrue(is_readable_background(colour))

    def test_custom_dark_colours_are_rejected(self):
        for value in ('#111111', '#000000', '#12345', 'red', None):
            with self.subTest(value=value):
                self.assertFalse(is_readable_background(value))

    def test_nonexistent_or_corrupt_preference_loads_default(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'appearance.json'
            self.assertEqual(load_background(path), DEFAULT_BACKGROUND)
            path.write_text('{not valid json', encoding='utf-8')
            self.assertEqual(load_background(path), DEFAULT_BACKGROUND)
            path.write_text('{"background": "#000000"}', encoding='utf-8')
            self.assertEqual(load_background(path), DEFAULT_BACKGROUND)

    def test_preference_round_trip_survives_reopening(self):
        with TemporaryDirectory() as directory:
            path = preference_path(Path(directory) / 'cards.txt')
            self.assertEqual(path.parent, Path(directory))
            save_background(path, '#ebf5ec')
            self.assertEqual(load_background(path), '#EBF5EC')
            self.assertEqual(json.loads(path.read_text())['background'], '#EBF5EC')

    def test_invalid_save_does_not_overwrite_existing_choice(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'appearance.json'
            save_background(path, '#EAF4FC')
            with self.assertRaises(ValueError):
                save_background(path, '#101010')
            self.assertEqual(load_background(path), '#EAF4FC')

    def test_preference_path_never_points_at_cards_or_history(self):
        path = preference_path('/tmp/my_cards/cards.txt')
        self.assertEqual(path.name, '.flashcards-appearance.json')
        self.assertNotEqual(path.name, 'cards.txt')
        self.assertNotEqual(path.name, 'flashcards.db')


class BackgroundPopupTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.root.withdraw()
        self.addCleanup(lambda: self.root.destroy() if self.root.winfo_exists() else None)

    def test_small_top_right_button_opens_callback(self):
        window = tk.Toplevel(self.root)
        layout = TkLayoutMaker()
        opened = Mock()
        layout.create_start_layout(window, 2, lambda action: None, opened)
        window.update_idletasks()

        def find_buttons(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, tk.Button):
                    yield widget
                yield from find_buttons(widget)

        background = [button for button in find_buttons(window)
                      if 'Background' in button.cget('text')]
        regular = [button for button in find_buttons(window)
                   if button.cget('text') == 'Study']
        self.assertEqual(len(background), 1)
        self.assertEqual(len(regular), 1)
        self.assertLess(int(background[0].cget('height')), int(regular[0].cget('height')))
        self.assertLess(int(background[0].cget('width')), int(regular[0].cget('width')))
        self.assertEqual(background[0].pack_info()['side'], 'right')
        background[0].invoke()
        opened.assert_called_once_with()
        window.destroy()

    def test_colour_selection_updates_current_menu_and_future_screens(self):
        with TemporaryDirectory() as directory:
            path = preference_path(Path(directory) / 'cards.txt')
            gui = GUI.__new__(GUI)
            gui.root = self.root
            gui.current_window = tk.Toplevel(self.root)
            gui._deck_handler = Mock(cards=[object(), object()])
            gui._layout_maker = TkLayoutMaker()
            gui._appearance_path = path
            gui._on_menu_selection = Mock()
            selected = '#EBF5EC'
            gui._set_background_colour(selected)
            self.assertEqual(gui._layout_maker.bg_color, selected)
            self.assertEqual(load_background(path), selected)
            self.assertEqual(gui.current_window.cget('bg'), selected)
            self.assertEqual(self.root.cget('bg'), selected)
            other = tk.Toplevel(self.root)
            gui._layout_maker.create_input_back_layout(other, 'Water', '水')
            self.assertEqual(other.cget('bg'), selected)
            other.destroy()
            gui.current_window.destroy()

    def test_popup_selection_changes_background_and_closes_popup(self):
        with TemporaryDirectory() as directory:
            gui = GUI.__new__(GUI)
            gui.root = self.root
            gui.current_window = tk.Toplevel(self.root)
            gui._layout_maker = TkLayoutMaker()
            gui._appearance_path = Path(directory) / 'appearance.json'
            gui._deck_handler = Mock(cards=[object()])
            gui._on_menu_selection = Mock()
            gui._layout_maker.create_start_layout(
                gui.current_window, 1, gui._on_menu_selection, gui._pick_background
            )
            gui._pick_background()
            dialogs = [child for child in gui.current_window.winfo_children()
                       if isinstance(child, tk.Toplevel)]
            self.assertEqual(len(dialogs), 1)
            popup = dialogs[0]

            def walk(parent):
                for widget in parent.winfo_children():
                    if isinstance(widget, tk.Button):
                        yield widget
                    yield from walk(widget)

            buttons = [button for button in walk(popup)
                       if button.cget('text') == 'Soft sage']
            self.assertEqual(len(buttons), 1)
            buttons[0].invoke()
            self.assertFalse(popup.winfo_exists())
            self.assertEqual(gui._layout_maker.bg_color, '#EBF5EC')
            self.assertEqual(load_background(gui._appearance_path), '#EBF5EC')
            gui.current_window.destroy()

    def test_custom_too_dark_colour_does_not_change_theme(self):
        with TemporaryDirectory() as directory:
            gui = GUI.__new__(GUI)
            gui.root = self.root
            gui.current_window = tk.Toplevel(self.root)
            gui._layout_maker = TkLayoutMaker()
            gui._appearance_path = Path(directory) / 'appearance.json'
            gui._deck_handler = Mock(cards=[])
            gui._on_menu_selection = Mock()
            with patch('tk_gui.messagebox.showwarning') as warning:
                self.assertFalse(gui._set_background_colour('#111111'))
            warning.assert_called_once()
            self.assertEqual(gui._layout_maker.bg_color, DEFAULT_BACKGROUND)
            self.assertFalse(gui._appearance_path.exists())
            gui.current_window.destroy()


if __name__ == '__main__':
    unittest.main()
