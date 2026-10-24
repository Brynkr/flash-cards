"""End-to-end Input Study callback regression tests using isolated SQLite.

On machines without a Tk display these are skipped. On a Mac the real Tk
window processes the simulated button callback through the Tk event loop.
"""
import sqlite3
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from deck_handler import DeckHandler
import constants
from study_core.history import ReviewHistory
from tk_gui import GUI


class _ImmediateAnswerLayout:
    def __init__(self, response, *, cancel=False, twice=False):
        self.response = response
        self.cancel = cancel
        self.twice = twice

    def create_input_front_layout(self, window, key, on_answer, on_return, on_input_change):
        def submit():
            on_input_change(self.response)
            if self.cancel:
                on_return()
            else:
                on_answer()
                if self.twice:
                    on_answer()
        window.after(0, submit)


class TkReviewHistoryTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError as error:
            self.skipTest(f"Tk display unavailable: {error}")
        self.addCleanup(lambda: self.root.destroy() if self.root.winfo_exists() else None)
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.db_path = Path(self.tempdir.name) / "flashcards.db"
        self.card = SimpleNamespace(english="Can", chinese=f"kě yǐ 可以 {constants.WORD_DELIMITER} néng 能")
        self.gui = GUI.__new__(GUI)
        self.gui.root = self.root
        self.gui._deck_handler = DeckHandler.__new__(DeckHandler)
        self.gui._review_history = ReviewHistory(self.db_path)
        self.gui.set_window_size = lambda *a: None
        self.feedback = []
        self.gui._show_correct_answer = lambda card: self.feedback.append("correct")
        self.gui._show_incorrect_answer = lambda card: self.feedback.append("incorrect")

    def attempt(self, response, *, cancel=False, twice=False):
        self.gui._layout_maker = _ImmediateAnswerLayout(response, cancel=cancel, twice=twice)
        return self.gui._input_answer_poll(self.card)

    def stored(self):
        # Reopen to confirm actual disk persistence, not merely in-memory data.
        return ReviewHistory(self.db_path).reviews_for(self.card.english, self.card.chinese)

    def test_correct_submitted_answer_persists(self):
        self.assertEqual(self.attempt("能"), "Correct")
        self.assertEqual(self.feedback, ["correct"])
        events = self.stored()
        self.assertEqual(len(events), 1)
        self.assertTrue(events[0].correct)
        self.assertEqual(events[0].mode, "input")

    def test_incorrect_submitted_answer_persists(self):
        self.assertEqual(self.attempt("不能"), "Incorrect")
        self.assertEqual(self.feedback, ["incorrect"])
        self.assertEqual(len(self.stored()), 1)
        self.assertFalse(self.stored()[0].correct)

    def test_return_without_submitting_does_not_record(self):
        self.assertEqual(self.attempt("能", cancel=True), constants.BUTTON_RETURN_TEXT)
        self.assertEqual(self.feedback, [])
        self.assertEqual(self.stored(), [])

    def test_repeated_submit_records_exactly_once(self):
        self.assertEqual(self.attempt("可以", twice=True), "Correct")
        self.assertEqual(len(self.stored()), 1)
        self.assertEqual(self.feedback, ["correct"])

    def test_database_error_reports_warning_but_does_not_prevent_study(self):
        class FailedHistory:
            def record_review(self, *args, **kwargs):
                raise sqlite3.OperationalError("database is read-only")

        self.gui._review_history = FailedHistory()
        with patch("tk_gui.messagebox.showwarning") as warning:
            self.assertEqual(self.attempt("可以"), "Correct")
        warning.assert_called_once()
        self.assertEqual(self.feedback, ["correct"])
        self.assertEqual(self.stored(), [])

    def test_history_is_lazy_when_first_recording(self):
        self.gui._review_history = None
        self.gui._layout_maker = _ImmediateAnswerLayout("能")
        with patch("tk_gui.ReviewHistory", side_effect=lambda: ReviewHistory(self.db_path)) as factory:
            self.assertEqual(self.gui._input_answer_poll(self.card), "Correct")
        factory.assert_called_once_with()
        self.assertEqual(len(self.stored()), 1)


if __name__ == "__main__":
    unittest.main()
