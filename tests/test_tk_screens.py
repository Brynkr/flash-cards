"""Integration tests for the previously incomplete Tkinter screens.

When Tk is unavailable (headless CI), tests skip rather than failing.
On a Mac desktop they exercise actual Tk widgets.
"""
import tkinter as tk
import unittest

from tk_layout_maker import TkLayoutMaker
import constants


class TkScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as error:
            raise unittest.SkipTest(f'Tk display unavailable: {error}')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root') and cls.root.winfo_exists():
            cls.root.destroy()

    def setUp(self):
        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.layout = TkLayoutMaker()

    def tearDown(self):
        if self.window.winfo_exists():
            self.window.destroy()

    def descendants(self, parent, widget_type):
        found = []
        for child in parent.winfo_children():
            if isinstance(child, widget_type):
                found.append(child)
            found.extend(self.descendants(child, widget_type))
        return found

    def test_add_card_screen_submits_pasted_input_and_return(self):
        entries = []
        callbacks = {'add': 0, 'return': 0}

        def update(value):
            entries.append(value)

        def add():
            callbacks['add'] += 1

        def go_back():
            callbacks['return'] += 1

        self.layout.create_add_cards_layout(
            self.window, add, go_back, update, 'start')
        entry = self.descendants(self.window, tk.Entry)[0]
        entry.insert(0, 'Hello : nǐ hǎo 你好')
        buttons = {b['text']: b for b in self.descendants(self.window, tk.Button)}
        buttons['Add'].invoke()
        self.assertEqual(entries[-1], 'Hello : nǐ hǎo 你好')
        self.assertEqual(callbacks['add'], 1)
        buttons['Return'].invoke()
        self.assertEqual(callbacks['return'], 1)

    def test_add_card_screen_shows_success_or_error_feedback(self):
        self.layout.create_add_cards_layout(
            self.window, lambda: None, lambda: None, lambda value: None, 'invalid')
        labels = [label['text'] for label in self.descendants(self.window, tk.Label)]
        self.assertTrue(any('Invalid card' in label for label in labels))

    def test_category_screen_builds_checkboxes_and_saves(self):
        categories = {constants.CATEGORY_ALL: True, 'Number': False,
                      'Food': False, constants.CATEGORY_NO_TAGS: False}
        variables = {}
        saved = []
        self.layout.create_category_select_layout(
            self.window, categories, variables,
            lambda: saved.append({k: v.get() for k, v in variables.items()}))
        self.assertEqual(set(variables), set(categories))
        checks = {c['text']: c for c in self.descendants(self.window, tk.Checkbutton)}
        checks['Number'].invoke()
        self.assertTrue(variables['Number'].get())
        self.assertFalse(variables[constants.CATEGORY_ALL].get())
        checks['Food'].invoke()
        self.assertTrue(variables['Food'].get())
        checks[constants.CATEGORY_ALL].invoke()
        self.assertTrue(variables[constants.CATEGORY_ALL].get())
        self.assertFalse(variables['Food'].get())
        self.assertFalse(variables['Number'].get())
        buttons = {b['text']: b for b in self.descendants(self.window, tk.Button)}
        buttons['Save categories'].invoke()
        self.assertEqual(len(saved), 1)
        self.assertTrue(saved[0][constants.CATEGORY_ALL])


if __name__ == '__main__':
    unittest.main()
