"""Verify study and library/settings controls are visually grouped."""
import tkinter as tk
import unittest
from tk_layout_maker import TkLayoutMaker


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def find_text_widget(window, text):
    for widget in descendants(window):
        try:
            if widget.cget('text') == text:
                return widget
        except tk.TclError:
            pass
    raise AssertionError(f'Widget with text {text!r} was not found')


def direct_child_of(widget, parent):
    while widget.master is not parent:
        if widget.master is None:
            raise AssertionError('Widget is not a descendant of main menu')
        widget = widget.master
    return widget


class MainMenuSectionsTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'No graphical display: {exc}')
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.menu = tk.Toplevel(self.root)
        self.layout = TkLayoutMaker()
        self.layout.create_start_layout(
            self.menu, 12, lambda value: None,
            lambda: None, lambda: None,
        )
        self.menu.update_idletasks()

    def test_divider_separates_study_from_library_tools(self):
        heading = find_text_widget(self.menu, 'Library & Settings')
        parent = heading.master
        group = parent.pack_slaves()
        divider_index = group.index(heading) - 1
        self.assertGreaterEqual(divider_index, 0)
        divider = group[divider_index]
        self.assertIsInstance(divider, tk.Frame)
        self.assertEqual(int(divider.cget('height')), 2)
        self.assertEqual(divider.pack_info()['fill'], 'x')

        study = direct_child_of(find_text_widget(self.menu, 'Study'), parent)
        review = direct_child_of(find_text_widget(self.menu, 'Review Due'), parent)
        cards = direct_child_of(find_text_widget(self.menu, 'Add Cards'), parent)
        settings = direct_child_of(find_text_widget(self.menu, 'Review Settings'), parent)
        self.assertLess(group.index(study), divider_index)
        self.assertLess(group.index(review), divider_index)
        self.assertGreater(group.index(cards), group.index(heading))
        self.assertGreater(group.index(settings), group.index(heading))

    def test_all_menu_buttons_are_preserved(self):
        for text in (
            'Study', 'Study Recent', 'Priority Study', 'Input Study',
            'Auto', 'Auto Priority', 'Review Due', 'Progress',
            'Add Cards', 'Categories', 'Review Settings', 'Exit',
        ):
            with self.subTest(button=text):
                self.assertIsNotNone(find_text_widget(self.menu, text))


if __name__ == '__main__':
    unittest.main()
