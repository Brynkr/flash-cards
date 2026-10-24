"""Iteration 3F: twelve readable palette colours and compact GUI layout."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import unittest
from unittest.mock import Mock

from study_core.appearance import (
    BACKGROUND_PRESETS, DEFAULT_BACKGROUND, contrast_ratio,
    is_readable_background, load_background, save_background,
)
from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


class PaletteExpansionTests(unittest.TestCase):
    def test_twelve_presets_have_unique_names_and_colours(self):
        self.assertEqual(len(BACKGROUND_PRESETS), 12)
        self.assertEqual(len({name for name, _ in BACKGROUND_PRESETS}), 12)
        self.assertEqual(len({colour for _, colour in BACKGROUND_PRESETS}), 12)
        self.assertEqual(BACKGROUND_PRESETS[0], ('Default', DEFAULT_BACKGROUND))

    def test_six_new_shades_preserve_high_contrast(self):
        expected = {
            'Warm sand': '#EFD9B4',
            'Eucalyptus': '#D0E5D6',
            'Sky blue': '#CDE3F5',
            'Mauve': '#E0D3F1',
            'Apricot': '#F5D8C6',
            'Butter yellow': '#F5E4A9',
        }
        self.assertEqual(dict(BACKGROUND_PRESETS[6:]), expected)
        for name, colour in BACKGROUND_PRESETS:
            with self.subTest(name=name):
                self.assertTrue(is_readable_background(colour))
                self.assertGreaterEqual(contrast_ratio('#17212B', colour), 7.0)

    def test_new_colour_persists_and_old_colour_remains_valid(self):
        with TemporaryDirectory() as directory:
            preference = Path(directory) / 'appearance.json'
            save_background(preference, '#E0D3F1')
            self.assertEqual(load_background(preference), '#E0D3F1')
            save_background(preference, '#EBF5EC')
            self.assertEqual(load_background(preference), '#EBF5EC')

    def test_popup_has_six_rows_two_columns_and_saves_new_colour(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        root.withdraw()
        self.addCleanup(lambda: root.destroy() if root.winfo_exists() else None)
        with TemporaryDirectory() as directory:
            gui = GUI.__new__(GUI)
            gui.root = root
            gui.current_window = tk.Toplevel(root)
            gui._layout_maker = TkLayoutMaker()
            gui._deck_handler = Mock(cards=[object()])
            gui._appearance_path = Path(directory) / 'appearance.json'
            gui._on_menu_selection = Mock()
            gui._pick_background()

            popup = next(child for child in gui.current_window.winfo_children()
                         if isinstance(child, tk.Toplevel))
            content = next(child for child in popup.winfo_children()
                           if isinstance(child, tk.Frame))
            rows = [child for child in content.winfo_children()
                    if isinstance(child, tk.Frame)]
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(len([c for c in row.winfo_children()
                                     if isinstance(c, tk.Frame)]) == 2
                                for row in rows))

            def buttons(parent):
                for child in parent.winfo_children():
                    if isinstance(child, tk.Button):
                        yield child
                    yield from buttons(child)

            preset_buttons = [button for button in buttons(popup)
                              if button.cget('text') in dict(BACKGROUND_PRESETS)]
            self.assertEqual(len(preset_buttons), 12)
            richer_choice = next(button for button in preset_buttons
                                 if button.cget('text') == 'Eucalyptus')
            richer_choice.invoke()
            self.assertFalse(popup.winfo_exists())
            self.assertEqual(gui._layout_maker.bg_color, '#D0E5D6')
            self.assertEqual(load_background(gui._appearance_path), '#D0E5D6')
            gui.current_window.destroy()


if __name__ == '__main__':
    unittest.main()
