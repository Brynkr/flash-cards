"""Auto Study playback controls and persistent window regression tests."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from tk_gui import GUI


class FakeVar:
    def __init__(self, master=None, value='WAIT'):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeButton:
    def __init__(self):
        self.props = {}
        self._coloured_face = SimpleNamespace(configure=Mock())

    def configure(self, **kwargs):
        self.props.update(kwargs)


class FakeStatus:
    def __init__(self):
        self.text = 'Playing'

    def configure(self, **kwargs):
        self.text = kwargs.get('text', self.text)


class FakeChild:
    def __init__(self, window):
        self.window = window
        self.destroyed = False

    def destroy(self):
        self.destroyed = True
        self.window.children.remove(self)


class FakeWindow:
    def __init__(self, scenario):
        self.scenario = scenario
        self.callbacks = {}
        self.pending = {}
        self.canceled = []
        self.delays = []
        self.next_id = 0
        self.destroyed = False
        self.destroy_count = 0
        self.protocols = {}
        self.bindings = {}
        self.children = []
        self.layouts_removed = 0
        self.geometry_changes = []

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

    def bind(self, name, callback):
        self.bindings[name] = callback

    def unbind(self, name):
        self.bindings.pop(name, None)

    def winfo_exists(self):
        return not self.destroyed

    def winfo_children(self):
        return self.children[:]

    def update_idletasks(self):
        pass

    def winfo_width(self):
        return 700

    def winfo_height(self):
        return 350

    def winfo_reqwidth(self):
        return 650

    def winfo_reqheight(self):
        return 260

    def geometry(self, value):
        self.geometry_changes.append(value)

    def destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        self.destroy_count += 1
        callback = self.bindings.get('<Destroy>')
        if callback is not None:
            callback(SimpleNamespace(widget=self))

    def fire(self):
        timer_id = next(iter(self.pending))
        callback = self.pending.pop(timer_id)
        callback()

    def wait_variable(self, variable):
        self.scenario(self)
        if variable.get() == 'WAIT':
            raise AssertionError('Scenario did not complete its fake card')


class FakeLayout:
    def __init__(self):
        self.seen = []
        self.windows = []

    def create_auto_speed_controls(self, window, seconds, *,
                                   on_faster, on_slower):
        window.callbacks["faster"] = on_faster
        window.callbacks["slower"] = on_slower
        window.speed_display = FakeStatus()
        window.speed_display.text = f"Every {seconds:g} s"
        window.speed_controls = {"faster": FakeButton(), "slower": FakeButton(),
                                 "display": window.speed_display}
        return window.speed_controls

    def create_auto_layout(self, window, key, value, *,
                           on_pause_resume, on_stop, on_return):
        self.seen.append((key, value))
        self.windows.append(window)
        if window.children:
            raise AssertionError('Previous card was not cleared')
        window.children.append(FakeChild(window))
        window.callbacks = {'pause': on_pause_resume, 'stop': on_stop,
                            'back': on_return}
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
        self.gui._fullscreen = False
        self.gui._deck_handler = self.deck
        self.gui._categories = {}
        self.gui._layout_maker = FakeLayout()
        self.gui.set_window_size = Mock()
        self.scenarios = []
        self.windows = []
        self.waits = 0

    def run_study(self, priority=False):
        def make_window(_root):
            window = FakeWindow(self.next_scenario)
            self.windows.append(window)
            return window

        with patch('tk_gui.tk.Toplevel', side_effect=make_window), \
             patch('tk_gui.tk.StringVar', side_effect=FakeVar), \
             patch('tk_gui.constants.AUTO_DISPLAY_DELAY_SEC', 10, create=True):
            self.gui.auto_study(priority=priority)

    def next_scenario(self, window):
        scenario = self.scenarios[self.waits]
        self.waits += 1
        scenario(window)

    def test_return_to_menu_cancels_timer(self):
        self.scenarios = [lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(self.gui._layout_maker.seen, [('Hello', 'nǐ hǎo 你好')])
        self.assertEqual(self.windows[0].canceled, [1])
        self.assertEqual(self.windows[0].destroy_count, 1)

    def test_timer_advances_to_next_card(self):
        self.scenarios = [lambda w: w.fire(), lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual([c[0] for c in self.gui._layout_maker.seen],
                         ['Hello', 'Goodbye'])
        self.assertEqual(self.deck.shuffles, 1)
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(self.windows[0].delays, [10000, 10000])

    def test_cycles_cards_until_return(self):
        self.scenarios = [lambda w: w.fire(), lambda w: w.fire(),
                          lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual([c[0] for c in self.gui._layout_maker.seen],
                         ['Hello', 'Goodbye', 'Hello'])
        self.assertEqual(self.deck.shuffles, 2)
        self.assertEqual(len(self.windows), 1)

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
        self.assertEqual(len(self.windows), 1)
        self.assertEqual(self.windows[0].delays, [10000, 7000, 10000])

    def test_stop_halts_progress_until_return(self):
        def stop_and_return(w):
            w.callbacks['stop']()
            self.assertFalse(w.pending)
            self.assertEqual(w.controls['status'].text, 'Stopped — select Return to Menu')
            self.assertEqual(w.controls['pause'].props['state'], 'disabled')
            self.assertEqual(w.controls['stop'].props['state'], 'disabled')
            w.callbacks['pause']()
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
        self.assertEqual(self.deck.shuffles, 1)

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

    def test_one_window_maintained_for_multiple_cards(self):
        self.scenarios = [lambda w: w.fire(), lambda w: w.fire(),
                          lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual(len(self.windows), 1)
        self.assertTrue(all(w is self.windows[0]
                            for w in self.gui._layout_maker.windows))
        self.assertEqual(self.windows[0].destroy_count, 1)
        self.assertEqual(self.windows[0].geometry_changes, [])

    def test_no_stale_timer_after_advancing(self):
        def first(w):
            previous = next(iter(w.pending.values()))
            w.fire()
            self.old_callback = previous
        def second(w):
            w.callbacks['pause']()
            self.old_callback()  # Should be harmless even if invoked late.
            self.assertFalse(w.pending)
            self.assertEqual(w.controls['status'].text, 'Paused')
            w.callbacks['back']()
        self.scenarios = [first, second]
        self.run_study()
        self.assertEqual(self.waits, 2)

    def test_stop_cannot_advance_or_resume(self):
        def first(w):
            stale = next(iter(w.pending.values()))
            w.callbacks['stop']()
            stale()
            w.callbacks['pause']()
            self.assertFalse(w.pending)
            w.callbacks['back']()
        self.scenarios = [first]
        self.run_study()
        self.assertEqual(self.waits, 1)

    def test_return_does_not_render_following_cards(self):
        self.scenarios = [lambda w: w.callbacks['back']()]
        self.run_study()
        self.assertEqual(len(self.gui._layout_maker.seen), 1)
        self.assertEqual(self.deck.shuffles, 1)

    def test_speed_change_resets_current_timer_and_updates_label(self):
        def first(w):
            self.assertEqual(w.speed_display.text, "Every 10 s")
            old_callback = next(iter(w.pending.values()))
            w.callbacks["faster"]()
            self.assertEqual(w.speed_display.text, "Every 9 s")
            self.assertEqual(w.delays, [10000, 9000])
            self.assertEqual(len(w.pending), 1)
            old_callback()  # Canceled timer must not advance.
            self.assertEqual(len(w.pending), 1)
            w.callbacks["back"]()
        self.scenarios = [first]
        self.run_study()
        self.assertEqual(self.waits, 1)

    def test_changed_speed_persists_on_next_card(self):
        def first(w):
            w.callbacks["slower"]()
            self.assertEqual(w.speed_display.text, "Every 11 s")
            w.fire()
        def second(w):
            self.assertEqual(w.speed_display.text, "Every 11 s")
            w.callbacks["back"]()
        self.scenarios = [first, second]
        self.run_study()
        self.assertEqual(self.windows[0].delays, [10000, 11000, 11000])

    def test_speed_change_while_paused_does_not_restart_until_resume(self):
        def first(w):
            w.callbacks['pause']()
            self.assertFalse(w.pending)
            w.callbacks['faster']()
            self.assertEqual(w.speed_display.text, "Every 9 s")
            self.assertFalse(w.pending)
            w.callbacks['pause']()
            self.assertEqual(list(w.delays), [10000, 9000])
            w.callbacks['back']()
        self.scenarios = [first]
        with patch('tk_gui.time.monotonic', side_effect=[100., 101., 102.]):
            self.run_study()

    def test_stopped_speed_controls_are_inert(self):
        def first(w):
            w.callbacks['stop']()
            w.callbacks['faster']()
            self.assertEqual(w.speed_display.text, "Every 10 s")
            self.assertEqual(w.speed_controls['faster'].props['state'], 'disabled')
            self.assertFalse(w.pending)
            w.callbacks['back']()
        self.scenarios = [first]
        self.run_study()

    def test_speed_is_bounded(self):
        def first(w):
            for _ in range(30):
                w.callbacks['faster']()
            self.assertEqual(w.speed_display.text, "Every 1 s")
            w.callbacks['back']()
        self.scenarios = [first]
        self.run_study()

    def test_controls_from_old_cards_are_inert(self):
        def first(w):
            self.old_return = w.callbacks['back']
            w.fire()
        def second(w):
            self.old_return()  # Old callback cannot close new card.
            self.assertTrue(w.pending)
            w.callbacks['back']()
        self.scenarios = [first, second]
        self.run_study()
        self.assertEqual(self.waits, 2)

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
