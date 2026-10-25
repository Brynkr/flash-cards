"""Verify study controls are large and Auto speed controls remain usable."""
import tkinter as tk
import unittest
from tk_layout_maker import TkLayoutMaker


def find_buttons(widget):
    for child in widget.winfo_children():
        if isinstance(child, tk.Button):
            yield child
        yield from find_buttons(child)


class StudyButtonSizesTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'No graphical display: {exc}')
        self.root.withdraw()
        self.win = tk.Toplevel(self.root)
        self.layout = TkLayoutMaker()
        self.addCleanup(self.root.destroy)

    def assert_button_heights(self, minimum):
        buttons = list(find_buttons(self.win))
        self.assertTrue(buttons)
        for button in buttons:
            self.assertGreaterEqual(int(button.cget('height')), minimum)

    def test_visual_question_buttons_are_bigger(self):
        self.layout.create_display_front_layout(self.win, 'Question', lambda:None, lambda:None)
        self.assert_button_heights(3)

    def test_visual_answer_buttons_are_bigger(self):
        self.layout.create_display_back_layout(
            self.win, 'Q', 'A', False, lambda:None,lambda:None,lambda:None)
        self.assert_button_heights(3)

    def test_input_buttons_are_bigger(self):
        self.layout.create_input_front_layout(
            self.win,'Q',lambda:None,lambda:None,lambda v:None)
        self.assert_button_heights(4)

    def test_auto_speed_buttons_update_by_callbacks(self):
        log=[]
        controls = self.layout.create_auto_speed_controls(
            self.win, 5, on_faster=lambda:log.append('faster'),
            on_slower=lambda:log.append('slower'))
        self.assertEqual(controls['display'].cget('text'), 'Every 5 s')
        controls['faster'].invoke()
        controls['slower'].invoke()
        self.assertEqual(log, ['faster','slower'])
        self.assert_button_heights(2)

    def test_auto_speed_buttons_are_compact_and_reversed(self):
        controls = self.layout.create_auto_speed_controls(
            self.win, 5, on_faster=lambda:None, on_slower=lambda:None,
        )
        faster = controls['faster']
        slower = controls['slower']
        display = controls['display']
        self.assertEqual(faster.cget('text'), '−')
        self.assertEqual(slower.cget('text'), '+')
        self.assertEqual(int(faster.cget('width')), 3)
        self.assertEqual(int(slower.cget('width')), 3)
        self.assertEqual(int(faster.cget('height')), 2)
        self.assertEqual(int(slower.cget('height')), 2)
        # Verify physical order without requiring a mapped/macOS window.
        self.assertEqual(faster.master.pack_slaves(), [faster, display, slower])

    def test_auto_playback_buttons_are_bigger(self):
        self.layout.create_auto_layout(self.win,'Q','A',
            on_pause_resume=lambda:None,on_stop=lambda:None,on_return=lambda:None)
        self.assert_button_heights(2)
