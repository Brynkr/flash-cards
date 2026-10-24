"""Auto Study playback/exit controls, without requiring a graphical display."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from tk_gui import GUI


class FakeButton:
    def __init__(self):
        self.props = {}
        self._coloured_face = SimpleNamespace(configure=Mock())

    def configure(self, **kwargs):
        self.props.update(kwargs)


class FakeStatus:
    def __init__(self):
        self.text = "Playing"

    def configure(self, **kwargs):
        self.text = kwargs.get("text", self.text)


class FakeWindow:
    def __init__(self, scenario):
        self.scenario = scenario
        self.callbacks = {}
        self.pending = {}
        self.canceled = []
        self.delays = []
        self.next_id = 0
        self.destroyed = False
        self.protocols = {}

    def title(self, _title):
        pass

    def after(self, delay, callback):
        self.next_id += 1
        self.pending[self.next_id] = callback
        self.delays.append(delay)
        return self.next_id

    def after_cancel(self, timer_id):
        self.canceled.append(timer_id)
        self.pending.pop(timer_id, None)

    def protocol(self, name, callback):
        self.protocols[name] = callback

    def destroy(self):
        self.destroyed = True

    def fire(self):
        timer_id = next(iter(self.pending))
        callback = self.pending.pop(timer_id)
        callback()

    def wait_window(self):
        self.scenario(self)
        if not self.destroyed:
            raise AssertionError("Scenario did not close its fake window")


class FakeLayout:
    def __init__(self):
        self.seen = []
        self.windows = []

    def create_auto_layout(self, window, key, value, *,
                           on_pause_resume, on_stop, on_return):
        self.seen.append((key, value))
        self.windows.append(window)
        window.callbacks.update(pause=on_pause_resume, stop=on_stop, back=on_return)
        window.controls = {'pause': FakeButton(), 'stop': FakeButton(),
                           'status': FakeStatus()}
        return window.controls


class FakeDeck:
    def __init__(self, cards, priority=None):
        self.cards = cards
        self.priority_cards = priority if priority is not None else cards
        self.shuffles = 0
        self.filtered_sources = []

    def shuffle_deck(self):
        self.shuffles += 1

    def filter_cards_by_category(self, cards, categories):
        self.filtered_sources.append(cards)
        return [c for c in cards if c.english not in categories.get('skip', ())]


class AutoStudyTests(unittest.TestCase):
    def setUp(self):
        self.a = SimpleNamespace(english='Hello', chinese='nǐ hǎo 你好')
        self.b = SimpleNamespace(english='Goodbye', chinese='zài jiàn 再见')
        self.deck = FakeDeck([self.a, self.b], [self.b])
        self.gui = GUI.__new__(GUI)
        self.gui.root = object()
        self.gui._deck_handler = self.deck
        self.gui._categories = {}
        self.gui._layout_maker = FakeLayout()
        self.gui.set_window_size = Mock()
        self.scenarios = []
        self.windows = []

    def run_study(self, priority=False):
        def make_window(_root):
            window = FakeWindow(self.scenarios[len(self.windows)])
            self.windows.append(window)
            return window
        with patch('tk_gui.tk.Toplevel', side_effect=make_window), \
             patch('tk_gui.constants.AUTO_DISPLAY_DELAY_SEC', 10, create=True):
            self.gui.auto_study(priority=priority)

    def test_return_to_menu_cancels_timer(self):
        self.scenarios = [lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(self.gui._layout_maker.seen, [('Hello', 'nǐ hǎo 你好')])
        self.assertEqual(self.windows[0].canceled, [1])

    def test_timer_advances_to_next_card(self):
        self.scenarios = [lambda w: w.fire(), lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual([c[0] for c in self.gui._layout_maker.seen],
                         ['Hello', 'Goodbye'])
        self.assertEqual(self.deck.shuffles, 1)
        self.assertEqual(self.windows[0].delays, [10000])

    def test_cycles_cards_until_return(self):
        self.scenarios = [lambda w: w.fire(), lambda w: w.fire(),
                          lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual([c[0] for c in self.gui._layout_maker.seen],
                         ['Hello', 'Goodbye', 'Hello'])
        self.assertEqual(self.deck.shuffles, 2)

    def test_pause_cancels_timer_then_resume_advances(self):
        def first(w):
            w.callbacks['pause']()
            self.assertFalse(w.pending)
            self.assertEqual(w.canceled, [1])
            self.assertEqual(w.controls['status'].text, 'Paused')
            self.assertEqual(w.controls['pause'].props['text'], 'Resume')
            w.callbacks['pause']()
            self.assertEqual(w.controls['status'].text, 'Playing')
            self.assertEqual(w.controls['pause'].props['text'], 'Pause')
            self.assertEqual(len(w.pending), 1)
            w.fire()
        self.scenarios = [first, lambda w: w.callbacks['back']()]
        with patch('tk_gui.time.monotonic', side_effect=[100.0, 103.0, 103.0, 104.0]):
            self.run_study()
        self.assertEqual(len(self.windows), 2)
        self.assertEqual(self.windows[0].delays, [10000, 7000])

    def test_stop_halts_progress_until_return(self):
        def stop_and_return(w):
            w.callbacks['stop']()
            self.assertFalse(w.pending)
            self.assertEqual(w.controls['status'].text, 'Stopped — select Return to Menu')
            self.assertEqual(w.controls['pause'].props['state'], 'disabled')
            self.assertEqual(w.controls['stop'].props['state'], 'disabled')
            w.callbacks['pause']()  # Cannot resume a stopped session.
            self.assertFalse(w.pending)
            w.callbacks['back']()
        self.scenarios = [stop_and_return]
        self.run_study()
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(self.windows[0].canceled, [1])

    def test_closing_window_returns_to_menu(self):
        self.scenarios = [lambda w: w.protocols['WM_DELETE_WINDOW']()]
        self.run_study()
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(self.windows[0].canceled, [1])

    def test_unexpected_window_destroy_does_not_restart(self):
        self.scenarios = [lambda w: w.destroy()]
        self.run_study()
        self.assertEqual(len(self.windows), 1)

    def test_priority_mode_uses_only_priority_cards(self):
        self.scenarios = [lambda w: w.callbacks['back']()]
        self.run_study(priority=True)
        self.assertEqual(self.gui._layout_maker.seen, [('Goodbye', 'zài jiàn 再见')])
        self.assertIs(self.deck.filtered_sources[0], self.deck.priority_cards)

    def test_empty_categories_do_not_spin(self):
        self.gui._categories = {'skip': ('Hello', 'Goodbye')}
        self.scenarios = []
        with patch('tk_gui.messagebox.showinfo') as info:
            self.run_study()
        info.assert_called_once()
        self.assertEqual(len(self.windows), 0)
        self.assertEqual(self.deck.shuffles, 1)


class AutoLayoutTests(unittest.TestCase):
    def test_real_tk_buttons_are_displayed_and_wired(self):
        import tkinter as tk
        from tk_layout_maker import TkLayoutMaker
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f'Graphical display unavailable: {error}')
        root.withdraw()
        self.addCleanup(root.destroy)
        win = tk.Toplevel(root)
        self.addCleanup(lambda: win.destroy() if win.winfo_exists() else None)
        actions = []
        controls = TkLayoutMaker().create_auto_layout(
            win, 'Hello', 'nǐ hǎo 你好',
            on_pause_resume=lambda: actions.append('pause'),
            on_stop=lambda: actions.append('stop'),
            on_return=lambda: actions.append('return'),
        )
        controls['pause'].invoke()
        controls['stop'].invoke()
        controls['return'].invoke()
        self.assertEqual(actions, ['pause', 'stop', 'return'])
        def all_buttons(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Button):
                    yield child
                yield from all_buttons(child)
        labels = [button['text'] for button in all_buttons(win)]
        self.assertEqual(labels, ['Pause', 'Stop', 'Return to Menu'])


if __name__ == '__main__':
    unittest.main()
