"""Dashboard UI plumbing tests; do not touch actual flashcard databases."""

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch
import sqlite3
import tkinter as tk

from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


class ProgressScreenTests(TestCase):
    def make_gui(self):
        gui = GUI.__new__(GUI)
        gui.root = MagicMock()
        gui._deck_handler = SimpleNamespace(cards=[])
        gui._review_history = None
        gui._layout_maker = MagicMock()
        gui.set_window_size = MagicMock()
        return gui

    def test_progress_view_is_read_only_and_returns_to_menu(self):
        gui = self.make_gui()
        sample = object()
        with patch('tk_gui.load_progress', return_value=sample) as load, \
                patch('tk_gui.tk.Toplevel') as window:
            gui.show_progress()
        load.assert_called_once_with([], db_path=None)
        gui._layout_maker.create_progress_layout.assert_called_once()
        self.assertIs(gui._layout_maker.create_progress_layout.call_args.args[1], sample)
        window.return_value.wait_window.assert_called_once()
        window.return_value.protocol.assert_called_once()

    def test_pass_existing_history_path_to_reader(self):
        gui = self.make_gui()
        gui._review_history = SimpleNamespace(path=Path('/tmp/flashcards-test-not-real.db'))
        with patch('tk_gui.load_progress') as load, patch('tk_gui.tk.Toplevel'):
            gui.show_progress()
        self.assertEqual(load.call_args.kwargs['db_path'], gui._review_history.path)

    def test_database_errors_show_warning_instead_of_blank_progress(self):
        gui = self.make_gui()
        with patch('tk_gui.load_progress', side_effect=sqlite3.OperationalError('locked')), \
                patch('tk_gui.messagebox.showwarning') as warn, \
                patch('tk_gui.tk.Toplevel') as window:
            gui.show_progress()
        warn.assert_called_once()
        window.assert_not_called()

    def test_progress_button_is_available_from_main_menu(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        root.withdraw()
        self.addCleanup(root.destroy)
        win = tk.Toplevel(root)
        self.addCleanup(win.destroy)
        actions = []
        TkLayoutMaker().create_start_layout(win, 5, actions.append)

        def walk(parent):
            for child in parent.winfo_children():
                yield child
                yield from walk(child)

        buttons = [w for w in walk(win)
                   if isinstance(w, tk.Button) and w['text'] == 'Progress']
        self.assertEqual(len(buttons), 1)
        buttons[0].invoke()
        self.assertEqual(actions, ['Progress'])
