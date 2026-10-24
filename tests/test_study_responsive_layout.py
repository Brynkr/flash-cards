"""Layout regression checks for the two visual flashcard study screens."""
import tkinter as tk
import unittest
from unittest.mock import patch

import constants
from tk_layout_maker import TkLayoutMaker


class StudyResponsiveLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tk display unavailable: {error}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'root') and cls.root.winfo_exists():
            cls.root.destroy()

    def setUp(self):
        self.window = tk.Toplevel(self.root)
        self.layout = TkLayoutMaker()
        self.called = []
        self.constant_patch = patch.multiple(
            constants, create=True,
            BUTTON_ANSWER_TEXT='Answer', BUTTON_RETURN_TEXT='Return',
            BUTTON_NEXT_TEXT='Next', BUTTON_PRIORITY_TEXT='Priority',
        )
        self.constant_patch.start()

    def tearDown(self):
        self.constant_patch.stop()
        if self.window.winfo_exists():
            self.window.destroy()

    def widgets(self, kind):
        def visit(widget):
            for child in widget.winfo_children():
                if isinstance(child, kind):
                    yield child
                yield from visit(child)
        return list(visit(self.window))

    def front(self, word='example'):
        self.layout.create_display_front_layout(
            self.window, word,
            lambda: self.called.append('answer'),
            lambda: self.called.append('return'),
        )

    def back(self, priority=False, key='example', value='translation'):
        self.layout.create_display_back_layout(
            self.window, key, value, priority,
            lambda: self.called.append('next'),
            lambda: self.called.append('priority'),
            lambda: self.called.append('return'),
        )

    def assert_equal_buttons(self, expected_labels):
        self.window.update()
        buttons = self.widgets(tk.Button)
        self.assertEqual([b.cget('text') for b in buttons], expected_labels)
        widths = [b.winfo_width() for b in buttons]
        self.assertLessEqual(max(widths) - min(widths), 2, widths)
        self.assertTrue(all(b.winfo_height() >= 20 for b in buttons))
        self.assertTrue(all(b.winfo_rootx() + b.winfo_width() <=
                            self.window.winfo_rootx() + self.window.winfo_width() + 1
                            for b in buttons))
        self.assertTrue(all(b.winfo_rooty() + b.winfo_height() <=
                            self.window.winfo_rooty() + self.window.winfo_height() + 1
                            for b in buttons))
        return buttons

    def test_front_has_equal_width_controls(self):
        self.front()
        self.assert_equal_buttons(['Answer', 'Return'])

    def test_back_has_three_equal_width_controls(self):
        self.back()
        self.assert_equal_buttons(['Next', 'Priority', 'Return'])

    def test_priority_back_has_two_equal_width_controls(self):
        self.back(priority=True)
        self.assert_equal_buttons(['Next', 'Return'])

    def test_front_buttons_expand_with_window(self):
        self.front()
        self.window.geometry('460x290')
        self.window.update()
        narrow = self.widgets(tk.Button)[0].winfo_width()
        self.window.geometry('780x290')
        self.window.update()
        wide = self.widgets(tk.Button)[0].winfo_width()
        self.assertGreater(wide, narrow)
        self.assert_equal_buttons(['Answer', 'Return'])

    def test_back_buttons_expand_with_window(self):
        self.back()
        self.window.geometry('500x300')
        self.window.update()
        narrow = self.widgets(tk.Button)[0].winfo_width()
        self.window.geometry('790x300')
        self.window.update()
        self.assertGreater(self.widgets(tk.Button)[0].winfo_width(), narrow)
        self.assert_equal_buttons(['Next', 'Priority', 'Return'])

    def test_long_front_text_wraps_when_window_resizes(self):
        self.front('Long compound vocabulary prompt ' * 10)
        labels = [x for x in self.widgets(tk.Label) if 'Long compound' in x.cget('text')]
        self.assertEqual(len(labels), 1)
        self.window.geometry('480x350')
        self.window.update()
        narrow = int(labels[0].cget('wraplength'))
        self.window.geometry('800x350')
        self.window.update()
        self.assertGreater(int(labels[0].cget('wraplength')), narrow)
        self.assertEqual(str(labels[0].cget('justify')), 'center')

    def test_long_translation_wraps_when_window_resizes(self):
        self.back(value='A longer translation describing a word ' * 12)
        labels = [x for x in self.widgets(tk.Label) if 'A longer' in x.cget('text')]
        self.assertEqual(len(labels), 1)
        self.window.geometry('500x400')
        self.window.update()
        narrow = int(labels[0].cget('wraplength'))
        self.window.geometry('850x400')
        self.window.update()
        self.assertGreater(int(labels[0].cget('wraplength')), narrow)

    def test_front_button_callbacks_still_work(self):
        self.front()
        buttons = self.assert_equal_buttons(['Answer', 'Return'])
        buttons[0].invoke()
        buttons[1].invoke()
        self.assertEqual(self.called, ['answer', 'return'])

    def test_back_button_callbacks_still_work(self):
        self.back()
        buttons = self.assert_equal_buttons(['Next', 'Priority', 'Return'])
        for button in buttons:
            button.invoke()
        self.assertEqual(self.called, ['next', 'priority', 'return'])

    def test_input_study_layout_untouched(self):
        self.layout.create_input_front_layout(
            self.window, 'word', lambda: None, lambda: None, lambda x: None
        )
        self.assertEqual(len(self.widgets(tk.Entry)), 1)
        self.assertFalse(self.window.bind('<space>'))


if __name__ == '__main__':
    unittest.main()
