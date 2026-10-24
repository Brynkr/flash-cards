"""Goals dashboard integration tests without writing personal data."""
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import MagicMock, patch
import tkinter as tk

from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker
from study_core.goals import GoalSummary


class GoalScreenTests(TestCase):
    def make_gui(self):
        gui = GUI.__new__(GUI)
        gui.root = MagicMock()
        gui._review_history = None
        gui._deck_handler = SimpleNamespace(cards=[])
        gui._layout_maker = MagicMock()
        gui.set_window_size = MagicMock()
        return gui

    def test_opening_progress_does_not_save_goal(self):
        gui = self.make_gui()
        summary = GoalSummary(10, 1, 1, 1, None)
        with patch('tk_gui.load_progress', return_value=object()), \
             patch('tk_gui.load_goals', return_value=summary), \
             patch('tk_gui.save_daily_target') as save, \
             patch('tk_gui.tk.Toplevel'):
            gui.show_progress()
        save.assert_not_called()
        kwargs = gui._layout_maker.create_progress_layout.call_args.kwargs
        self.assertEqual(kwargs['goals'], summary)
        self.assertTrue(callable(kwargs['on_save_goal']))

    def test_only_save_action_changes_settings(self):
        gui = self.make_gui()
        summary = GoalSummary(10, 1, 1, 1, None)
        updated = GoalSummary(7, 1, 1, 1, None)
        with patch('tk_gui.load_progress'), \
             patch('tk_gui.load_goals', side_effect=[summary, updated]), \
             patch('tk_gui.save_daily_target') as save, \
             patch('tk_gui.tk.Toplevel'):
            gui.show_progress()
            callback = gui._layout_maker.create_progress_layout.call_args.kwargs['on_save_goal']
            result = callback(7)
        save.assert_called_once_with(7)
        self.assertEqual(result.target, 7)

    def test_failed_goal_save_warns_and_preserves_ui(self):
        gui = self.make_gui()
        with patch('tk_gui.load_progress'), \
             patch('tk_gui.load_goals', return_value=GoalSummary(10, 0, 0, 0, None)), \
             patch('tk_gui.save_daily_target', side_effect=OSError('readonly')), \
             patch('tk_gui.messagebox.showwarning') as warning, \
             patch('tk_gui.tk.Toplevel'):
            gui.show_progress()
            callback = gui._layout_maker.create_progress_layout.call_args.kwargs['on_save_goal']
            self.assertIsNone(callback(12))
        warning.assert_called_once()

    def test_dashboard_displays_goal_and_streak_when_gui_available(self):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        root.withdraw()
        self.addCleanup(root.destroy)
        window = tk.Toplevel(root)
        self.addCleanup(window.destroy)
        report = SimpleNamespace(
            total_cards=1, reviewed_cards=1, due_cards=0,
            attempts=1, correct=1, accuracy_percent=100,
            daily_reviews=(),
        )
        saved = []
        def save(goal):
            saved.append(goal)
            return GoalSummary(goal, 1, 1, 1, None)
        TkLayoutMaker().create_progress_layout(
            window, report, window.destroy,
            goals=GoalSummary(10, 1, 1, 1, None), on_save_goal=save
        )
        window.update_idletasks()
        def walk(parent):
            for child in parent.winfo_children():
                yield child
                yield from walk(child)
        widgets = list(walk(window))
        labels = [w.cget('text') for w in widgets if isinstance(w, tk.Label)]
        self.assertTrue(any('Today: 1/10' in label for label in labels))
        self.assertTrue(any('Current streak: 1' in label for label in labels))
        spin = next(w for w in widgets if isinstance(w, tk.Spinbox))
        spin.delete(0, tk.END)
        spin.insert(0, '7')
        button = next(w for w in widgets if isinstance(w, tk.Button)
                      and w.cget('text') == 'Save Goal')
        button.invoke()
        self.assertEqual(saved, [7])
        self.assertTrue(any('Today: 1/7' in w.cget('text') for w in widgets
                            if isinstance(w, tk.Label)))


if __name__ == '__main__':
    import unittest
    unittest.main()
