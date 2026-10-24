"""Final GUI polish: sensible menu behaviour, Escape to Return, and safe Git ignores."""
from pathlib import Path
from unittest.mock import Mock, patch
import tkinter as tk
import unittest

from tk_gui import GUI
import constants
from tk_layout_maker import TkLayoutMaker


class ReleasePolishTests(unittest.TestCase):
    def test_local_preferences_and_review_history_ignored_by_git(self):
        lines = set((Path(__file__).resolve().parents[1] / '.gitignore')
                    .read_text(encoding='utf-8').splitlines())
        for name in ('.flashcards-appearance.json', 'flashcards.db', 'flashcards.db-*'):
            with self.subTest(name=name):
                self.assertIn(name, lines)

    def test_generate_audio_does_not_close_the_main_menu(self):
        gui = GUI.__new__(GUI)
        gui.current_window = Mock()
        with patch('tk_gui.messagebox.showinfo') as info:
            gui._on_menu_selection('Generate Audio')
        info.assert_called_once()
        gui.current_window.destroy.assert_not_called()
        self.assertFalse(hasattr(gui, '_next_action'))

    def test_escape_from_input_screen_calls_return_not_submit(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(lambda: root.destroy() if root.winfo_exists() else None)
        window = tk.Toplevel(root)
        self.addCleanup(lambda: window.destroy() if window.winfo_exists() else None)
        answer, back = Mock(), Mock()
        with patch.object(window, 'bind', wraps=window.bind) as bindings:
            with patch.object(constants, 'BUTTON_ANSWER_TEXT', 'Answer', create=True):
                TkLayoutMaker().create_input_front_layout(
                    window, 'Hello', answer, back, lambda value: None
                )
        escape = [call.args[1] for call in bindings.call_args_list
                  if call.args[0] == '<Escape>']
        self.assertEqual(len(escape), 1)
        escape[0](None)
        back.assert_called_once()
        answer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
