"""Study screens must show full buttons rather than clip them to fixed sizes."""
import tkinter as tk
import unittest
from unittest.mock import patch

import constants
from tk_gui import GUI
from tk_layout_maker import TkLayoutMaker


class StudyWindowGeometryTests(unittest.TestCase):
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
        self.layout = TkLayoutMaker()
        self.gui = GUI.__new__(GUI)
        self.gui._fullscreen = False
        self.text_constants = patch.multiple(
            constants, create=True, BUTTON_ANSWER_TEXT='Answer',
            BUTTON_NEXT_TEXT='Next', BUTTON_PRIORITY_TEXT='Priority',
            BUTTON_RETURN_TEXT='Return',
        )
        self.text_constants.start()

    def tearDown(self):
        self.text_constants.stop()
        if self.window.winfo_exists():
            self.window.destroy()

    def descendants(self, parent, kind):
        for child in parent.winfo_children():
            if isinstance(child, kind):
                yield child
            yield from self.descendants(child, kind)

    def assert_buttons_fit(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        buttons = list(self.descendants(self.window, tk.Button))
        self.assertGreater(len(buttons), 0)
        for button in buttons:
            with self.subTest(button=button.cget('text')):
                x = button.winfo_rootx() - self.window.winfo_rootx()
                y = button.winfo_rooty() - self.window.winfo_rooty()
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertGreater(button.winfo_height(), 20)
                self.assertLessEqual(x + button.winfo_width(), width)
                self.assertLessEqual(y + button.winfo_height(), height)

    def test_recent_and_standard_study_front_buttons_fit(self):
        self.layout.create_display_front_layout(
            self.window, 'Miss', lambda: None, lambda: None
        )
        self.gui.set_window_size(self.window, 520, 160)
        self.assert_buttons_fit()

    def test_standard_study_back_buttons_fit(self):
        self.layout.create_display_back_layout(
            self.window, 'Miss', 'cuò 错', False,
            lambda: None, lambda: None, lambda: None
        )
        self.gui.set_window_size(self.window, 640, 210)
        self.assert_buttons_fit()

    def test_priority_study_back_buttons_fit(self):
        self.layout.create_display_back_layout(
            self.window, 'Miss', 'cuò 错', True,
            lambda: None, lambda: None, lambda: None
        )
        self.gui.set_window_size(self.window, 640, 210)
        self.assert_buttons_fit()

    def test_input_study_controls_fit(self):
        self.layout.create_input_front_layout(
            self.window, 'Miss', lambda: None, lambda: None, lambda x: None
        )
        self.gui.set_window_size(self.window, 260, 150)
        self.assert_buttons_fit()
        fields = list(self.descendants(self.window, tk.Entry))
        self.assertEqual(len(fields), 1)
        self.assertGreater(fields[0].winfo_height(), 15)

    def test_fixed_size_still_used_when_layout_is_smaller(self):
        tk.Label(self.window, text='Small').pack()
        self.gui.set_window_size(self.window, 320, 200)
        self.window.update_idletasks()
        self.assertEqual(self.window.winfo_width(), 320)
        self.assertEqual(self.window.winfo_height(), 200)

    def test_fullscreen_does_not_set_window_geometry(self):
        self.gui._fullscreen = True
        with patch.object(self.window, 'attributes') as attributes:
            self.gui.set_window_size(self.window, 320, 200)
        attributes.assert_called_once_with('-fullscreen', True)


if __name__ == '__main__':
    unittest.main()
