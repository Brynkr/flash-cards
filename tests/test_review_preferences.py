"""Persistent v1.2 review-mode preference is safe, explicit and cancellable."""
import json
from pathlib import Path
import stat
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from study_core.review_preferences import (
    DEFAULT_MODE, choose_review_mode, load_review_mode, save_review_mode, settings_file,
)


class ReviewPreferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "review_settings.json"

    def test_missing_file_defaults_to_standard_without_creating_file(self):
        self.assertEqual(load_review_mode(self.path), DEFAULT_MODE)
        self.assertFalse(self.path.exists())

    def test_saving_and_loading_adaptive(self):
        save_review_mode("adaptive", self.path)
        self.assertEqual(load_review_mode(self.path), "adaptive")

    def test_saving_and_loading_standard(self):
        save_review_mode("adaptive", self.path)
        save_review_mode("standard", self.path)
        self.assertEqual(load_review_mode(self.path), "standard")

    def test_valid_json_schema(self):
        save_review_mode("adaptive", self.path)
        self.assertEqual(json.loads(self.path.read_text()),
                         {"version": 1, "review_mode": "adaptive"})

    def test_invalid_mode_does_not_modify_existing_file(self):
        save_review_mode("standard", self.path)
        before = self.path.read_bytes()
        for wrong in (None, "", "unknown", "1", 1, True):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                save_review_mode(wrong, self.path)
            self.assertEqual(self.path.read_bytes(), before)

    def test_corrupt_file_is_not_silently_ignored(self):
        for bad in ('{broken', '[]', '{"version":2,"review_mode":"standard"}',
                    '{"version":1,"review_mode":"unknown"}'):
            with self.subTest(bad=bad):
                self.path.write_text(bad)
                with self.assertRaises(ValueError):
                    load_review_mode(self.path)

    def test_private_file_permissions(self):
        save_review_mode("standard", self.path)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)

    def test_symlink_is_rejected_for_read_and_write(self):
        target = Path(self.temp.name) / "target.json"
        target.write_text("secret")
        self.path.symlink_to(target)
        with self.assertRaises(ValueError):
            load_review_mode(self.path)
        with self.assertRaises(ValueError):
            save_review_mode("adaptive", self.path)
        self.assertEqual(target.read_text(), "secret")

    def test_default_location_follows_private_card_path(self):
        with patch('constants.CARD_PATH', str(Path(self.temp.name) / 'cards.txt')):
            self.assertEqual(settings_file(), self.path)


@unittest.skipUnless(bool(__import__('os').environ.get('DISPLAY')) or __import__('sys').platform == 'darwin',
                     'Display required for Tk dialog tests')
class ReviewPreferenceDialogTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(lambda: self.root.destroy() if self.root.winfo_exists() else None)

    @staticmethod
    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from ReviewPreferenceDialogTests.descendants(child)

    def _choose(self, initial, desired, click):
        def act():
            windows = [item for item in self.root.winfo_children() if isinstance(item, tk.Toplevel)]
            self.assertEqual(len(windows), 1)
            window = windows[0]
            buttons = [item for item in self.descendants(window) if isinstance(item, __import__('tkinter').ttk.Button)]
            if desired:
                radios = [item for item in self.descendants(window) if isinstance(item, __import__('tkinter').ttk.Radiobutton)]
                self.assertEqual(len(radios), 2)
                next(item for item in radios if item.cget('value') == desired).invoke()
            next(item for item in buttons if item.cget('text') == click).invoke()
        self.root.after(80, act)
        return choose_review_mode(self.root, initial)

    def test_save_adaptive_with_hidden_parent(self):
        self.assertEqual(self._choose('standard', 'adaptive', 'Save'), 'adaptive')

    def test_save_standard(self):
        self.assertEqual(self._choose('adaptive', 'standard', 'Save'), 'standard')

    def test_cancel_does_not_change_preference(self):
        self.assertIsNone(self._choose('adaptive', 'standard', 'Cancel'))
