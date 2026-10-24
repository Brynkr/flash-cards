import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from pathlib import Path
import constants
from deck_handler import DeckHandler
from tk_layout_maker import TkLayoutMaker
from study_core.history import ReviewHistory
from study_core.sessions import choose_study_size, select_session_cards
import os
from study_core.scheduler import prioritized_due_cards
from study_core.adaptive import adaptive_due_cards
from study_core.progress import load_progress
from study_core.goals import load_goals, save_daily_target
from study_core.review_preferences import (
    load_review_mode, save_review_mode, choose_review_mode,
)
from study_core.appearance import (
    BACKGROUND_PRESETS, BUTTON_PRESETS, is_readable_background,
    is_readable_button, load_background, load_buttons, active_button_color,
    preference_path, save_background, save_buttons,
)
import sqlite3
import threading


class GUI:
    MENU_STUDY = "Study"
    MENU_STUDY_RECENT = "Study Recent (100)"
    MENU_PRIORITY_STUDY = "Priority Study"
    MENU_INPUT_STUDY = "Input Study"
    MENU_REVIEW_DUE = "Review Due"
    MENU_REVIEW_SETTINGS = "Review Settings"
    MENU_PROGRESS = "Progress"
    MENU_AUTO_STUDY = "Auto"
    MENU_AUTO_PRIORITY_STUDY = "Auto Priority"
    MENU_ADD_CARDS = "Add Cards"
    MENU_CATEGORIES = "Categories"
    MENU_FULLSCREEN = "Fullscreen"
    MENU_TOGGLE_AUDIO = "Toggle Audio"
    MENU_EXIT = "Exit"

    def __init__(self):
        self._deck_handler  = DeckHandler()
        self._layout_maker  = TkLayoutMaker()
        self._appearance_path = preference_path(constants.CARD_PATH)
        self._layout_maker.bg_color = load_background(self._appearance_path)
        self._layout_maker.button_bg = load_buttons(self._appearance_path)
        self._layout_maker.button_active_bg = active_button_color(
            self._layout_maker.button_bg
        )
        self._review_history = None  # Open the database only after a submitted answer.

        self._fullscreen = False
        self._categories = self._deck_handler.categories
        self._categories[constants.CATEGORY_NO_TAGS] = False

        # Initialize root window
        self.root = tk.Tk()
        self.root.title("Flash Cards")
        self.root.withdraw()  # Only show the study and menu windows

        # Apply theme colors (customize as needed)
        self._apply_theme()

        self.current_window = None

    def _apply_theme(self):
        """Use the same high-contrast light palette as the Tk widgets."""
        layout = self._layout_maker
        self.root.configure(bg=layout.bg_color)

        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TButton', background=layout.button_bg,
                        foreground=layout.fg_color,
                        borderwidth=1, font=('Arial', 10))
        style.map('TButton',
                  background=[('active', layout.button_active_bg)],
                  foreground=[('active', layout.fg_color)])
        style.configure('TLabel', background=layout.bg_color,
                        foreground=layout.fg_color)
        style.configure('TFrame', background=layout.bg_color)

    def start_menu(self):
        while True:
            self._deck_handler.shuffle_deck()

            # Create main menu window
            if self.current_window:
                self.current_window.destroy()

            self.current_window = tk.Toplevel(self.root)
            self.current_window.title("Flash Cards")
            self.current_window.protocol("WM_DELETE_WINDOW", self._on_close)

            self._layout_maker.create_start_layout(
                self.current_window,
                len(self._deck_handler.cards),
                self._on_menu_selection,
                self._pick_background,
                self._pick_buttons,
            )

            self.set_window_size(self.current_window, 420, 495)

            # Wait for window to close
            self.current_window.wait_window()

            # Check if we should exit
            if not hasattr(self, '_next_action'):
                break

            action = self._next_action
            delattr(self, '_next_action')

            match action:
                case self.MENU_STUDY:
                    # Ask only for regular Study; other study modes stay unchanged.
                    selection = choose_study_size(self.root)
                    if selection is not None:
                        self.display_study(session_size=selection)
                case self.MENU_STUDY_RECENT:
                    self.display_study(recent=True)
                case self.MENU_PRIORITY_STUDY:
                    self.display_study(priority=True)
                case self.MENU_INPUT_STUDY:
                    self.input_study()
                case self.MENU_REVIEW_DUE:
                    self.review_due()
                case self.MENU_REVIEW_SETTINGS:
                    self.review_settings()
                case self.MENU_PROGRESS:
                    self.show_progress()
                case self.MENU_AUTO_STUDY:
                    self.auto_study()
                case self.MENU_AUTO_PRIORITY_STUDY:
                    self.auto_study(priority=True)
                case self.MENU_ADD_CARDS:
                    self.add_cards()
                case self.MENU_CATEGORIES:
                    self.select_categories()
                case self.MENU_EXIT | _:
                    break

    def _set_background_colour(self, colour):
        """Apply an accessible colour, save it, and redraw the current menu."""
        if not is_readable_background(colour):
            messagebox.showwarning(
                "Unreadable background",
                "Please choose a lighter background so all text stays readable.",
                parent=self.current_window,
            )
            return False

        self._layout_maker.bg_color = colour.upper()
        self._apply_theme()
        try:
            save_background(self._appearance_path, colour)
        except OSError as error:
            messagebox.showwarning(
                "Background not saved",
                f"Colour changed for this session, but it could not be saved:\n{error}",
                parent=self.current_window,
            )

        if self.current_window is not None and self.current_window.winfo_exists():
            for child in self.current_window.winfo_children():
                # Keep the palette popup alive until its callback closes it.
                if not isinstance(child, tk.Toplevel):
                    child.destroy()
            self._layout_maker.create_start_layout(
                self.current_window,
                len(self._deck_handler.cards),
                self._on_menu_selection,
                self._pick_background,
                self._pick_buttons,
            )
        return True

    def _set_button_colour(self, colour):
        """Persist a readable button colour and redraw the active main menu."""
        if not is_readable_button(colour):
            messagebox.showwarning(
                "Unreadable buttons",
                "Choose a lighter button colour so the labels stay readable.",
                parent=self.current_window,
            )
            return False

        self._layout_maker.button_bg = colour.upper()
        self._layout_maker.button_active_bg = active_button_color(colour)
        self._apply_theme()
        try:
            save_buttons(self._appearance_path, colour)
        except OSError as error:
            messagebox.showwarning(
                "Button colour not saved",
                f"Colour changed for this session, but could not be saved:\n{error}",
                parent=self.current_window,
            )

        if self.current_window is not None and self.current_window.winfo_exists():
            for child in self.current_window.winfo_children():
                if not isinstance(child, tk.Toplevel):
                    child.destroy()
            self._layout_maker.create_start_layout(
                self.current_window, len(self._deck_handler.cards),
                self._on_menu_selection, self._pick_background,
                self._pick_buttons,
            )
        return True

    def _pick_buttons(self):
        """Show twelve button colours and an optional custom-colour picker."""
        menu = self.current_window
        if menu is None or not menu.winfo_exists():
            return
        popup = tk.Toplevel(menu)
        popup.title("Choose button colour")
        popup.configure(bg=self._layout_maker.bg_color)
        popup.transient(menu)
        popup.resizable(False, False)
        frame = tk.Frame(popup, bg=self._layout_maker.bg_color)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
        self._layout_maker._create_label(frame, "Button colour", 14).pack(pady=(0, 6))

        def select(colour):
            if self._set_button_colour(colour):
                popup.destroy()

        for index in range(0, len(BUTTON_PRESETS), 2):
            row = tk.Frame(frame, bg=self._layout_maker.bg_color)
            row.pack(fill=tk.X, pady=3)
            for name, colour in BUTTON_PRESETS[index:index + 2]:
                choice = tk.Frame(row, bg=self._layout_maker.bg_color)
                choice.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
                tk.Label(choice, text="  ", width=2, bg=colour,
                         relief=tk.SOLID, borderwidth=1).pack(side=tk.LEFT, padx=(0, 6))
                button = self._layout_maker._create_button(
                    choice, name, lambda value=colour: select(value),
                    width=15, height=1,
                )
                button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def custom_colour():
            result = colorchooser.askcolor(
                color=self._layout_maker.button_bg, parent=popup,
                title="Choose a light button colour",
            )
            if result and result[1]:
                select(result[1])

        self._layout_maker._create_button(
            frame, "Custom colour…", custom_colour, width=19, height=1
        ).pack(pady=(11, 3))
        self._layout_maker._create_button(
            frame, "Cancel", popup.destroy, width=12, height=1
        ).pack()
        popup.grab_set()
        popup.focus_set()

    def _pick_background(self):
        """Show a small popup of gentle colours, plus a native custom picker."""
        menu = self.current_window
        if menu is None or not menu.winfo_exists():
            return
        popup = tk.Toplevel(menu)
        popup.title("Choose background colour")
        popup.configure(bg=self._layout_maker.bg_color)
        popup.transient(menu)
        popup.resizable(False, False)

        frame = tk.Frame(popup, bg=self._layout_maker.bg_color)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)
        self._layout_maker._create_label(
            frame, "Background colour", 14
        ).pack(pady=(0, 6))

        def select(colour):
            if self._set_background_colour(colour):
                popup.destroy()

        # Two columns keep all twelve choices visible on a laptop screen.
        for index in range(0, len(BACKGROUND_PRESETS), 2):
            row = tk.Frame(frame, bg=self._layout_maker.bg_color)
            row.pack(fill=tk.X, pady=3)
            for name, colour in BACKGROUND_PRESETS[index:index + 2]:
                choice = tk.Frame(row, bg=self._layout_maker.bg_color)
                choice.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
                tk.Label(choice, text="  ", width=2, bg=colour,
                         relief=tk.SOLID, borderwidth=1).pack(
                             side=tk.LEFT, padx=(0, 6)
                         )
                button = self._layout_maker._create_button(
                    choice, name, lambda value=colour: select(value),
                    width=15, height=1,
                )
                button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def custom_colour():
            result = colorchooser.askcolor(
                color=self._layout_maker.bg_color,
                parent=popup,
                title="Choose a light background",
            )
            if result and result[1]:
                select(result[1])

        self._layout_maker._create_button(
            frame, "Custom colour…", custom_colour, width=19, height=1
        ).pack(pady=(11, 3))
        self._layout_maker._create_button(
            frame, "Cancel", popup.destroy, width=12, height=1
        ).pack()
        popup.grab_set()
        popup.focus_set()

    def _on_menu_selection(self, action):
        """Callback for menu button clicks"""
        match action:
            case "Generate Audio":
                messagebox.showinfo(
                    "Audio generation",
                    "Audio generation is not yet available in this Tkinter interface.",
                    parent=self.current_window,
                )
            case self.MENU_FULLSCREEN:
                self.toggle_fullscreen(self.current_window)
            case self.MENU_TOGGLE_AUDIO:
                self.toggle_audio()
            case _:
                self._next_action = action
                if self.current_window:
                    self.current_window.destroy()

    def _on_close(self):
        """Handle window close event"""
        sys.exit()

    def display_study(self, recent=False, priority=False, session_size=None):
        if recent:
            cards = self._deck_handler.filter_cards_by_category(self._deck_handler.recent_cards,
                                                                self._categories)
        elif priority:
            cards = self._deck_handler.filter_cards_by_category(self._deck_handler.priority_cards,
                                                                self._categories)
        else:
            cards = self._deck_handler.filter_cards_by_category(self._deck_handler.cards,
                                                                self._categories)

        if session_size is not None and not (recent or priority):
            cards = select_session_cards(cards, session_size)

        # Study tests can still stub the existing front/back methods. In the
        # real UI both methods share one Toplevel, cleaned up exactly once.
        completed = False
        try:
            for card in cards:
                print(f"front = {card.english}, back = {card.chinese}")
                result = self._show_card_front(card, priority)
                if result == "RETURN":
                    return
                if result == "SHOW_BACK":
                    back_result = self._show_card_back(card, priority)
                    if back_result == "RETURN":
                        return
            completed = True
        finally:
            window = getattr(self, '_visual_study_window', None)
            self._visual_study_window = None
            if window is not None:
                try:
                    if window.winfo_exists():
                        window.destroy()
                except tk.TclError:
                    pass

        if completed:
            self._show_completion()

    def _visual_study_surface(self):
        """Use one outer Tk window for an entire visual Study session."""
        window = getattr(self, '_visual_study_window', None)
        if window is None or not window.winfo_exists():
            window = tk.Toplevel(self.root)
            self._visual_study_window = window
            return window, True
        return window, False

    def _clear_visual_study_surface(self, window):
        """Remove widgets and old shortcuts, never the outer study window."""
        for key in ('<Return>', '<space>', '<Escape>'):
            window.unbind(key)
        for child in window.winfo_children():
            child.destroy()

    def _fit_visual_study_surface(self, window, first_view):
        """Preserve position and dimensions; grow only for oversized content."""
        if first_view:
            # A common size for Q and A avoids the old 520x160 -> 640x210 jump.
            self.set_window_size(window, 680, 350)
            return
        if self._fullscreen:
            return
        window.update_idletasks()
        width = max(window.winfo_width(), window.winfo_reqwidth())
        height = max(window.winfo_height(), window.winfo_reqheight())
        if width > window.winfo_width() or height > window.winfo_height():
            # Geometry without +x+y retains the window's current screen location.
            window.geometry(f"{width}x{height}")

    def _show_card_front(self, card, priority):
        """Display Q in the session window, waiting for a user action."""
        window, first_view = self._visual_study_surface()
        self._clear_visual_study_surface(window)
        window.title("Q")
        action = tk.StringVar(master=window, value="WAIT")

        def on_answer():
            action.set("SHOW_BACK")

        def on_return():
            action.set("RETURN")

        window.protocol("WM_DELETE_WINDOW", on_return)
        self._layout_maker.create_display_front_layout(
            window, card.english, on_answer, on_return
        )
        self._fit_visual_study_surface(window, first_view)
        window.wait_variable(action)
        return action.get()

    def _show_card_back(self, card, priority):
        """Replace Q with A; leave the session window exactly where it is."""
        window, first_view = self._visual_study_surface()
        self._clear_visual_study_surface(window)
        window.title("A")
        action = tk.StringVar(master=window, value="WAIT")

        def on_next():
            action.set("NEXT")

        def on_priority():
            self._deck_handler.add_priority_card(card.english, card.chinese)
            action.set("NEXT")

        def on_return():
            action.set("RETURN")

        window.protocol("WM_DELETE_WINDOW", on_return)
        self._layout_maker.create_display_back_layout(
            window, card.english, card.chinese, priority,
            on_next, on_priority, on_return
        )
        self._fit_visual_study_surface(window, first_view)
        window.wait_variable(action)
        return action.get()

    def _show_completion(self):
        """Show completion message"""
        window = tk.Toplevel(self.root)
        window.title("Complete")

        self._layout_maker.create_completed_layout(window, lambda: window.destroy())

        self.set_window_size(window, 300, 150)
        window.wait_window()

    def input_study(self):
        cards = self._deck_handler.filter_cards_by_category(self._deck_handler.cards, self._categories)

        try:
            for card in cards:
                print(f"front = {card.english}, back = {card.chinese}")

                result = self._input_answer_poll(card)

                if result == constants.BUTTON_RETURN_TEXT:
                    return
        finally:
            self._close_input_study_surface()

        self._show_completion()

    def review_settings(self):
        """Edit the privately saved Review Due algorithm, without touching history."""
        try:
            current = load_review_mode()
        except (OSError, ValueError) as error:
            messagebox.showwarning(
                "Review settings unavailable", f"Could not read review settings:\n{error}",
                parent=self.root,
            )
            return
        choice = choose_review_mode(self.root, current)
        if choice is None:
            return
        try:
            save_review_mode(choice)
        except (OSError, ValueError) as error:
            messagebox.showwarning(
                "Review settings not saved", f"Could not save review settings:\n{error}",
                parent=self.root,
            )

    def review_due(self):
        """Review previously graded due cards once, respecting active categories.

        A wrong card is due again at the next session, not repeated endlessly in
        this one. Viewing, returning, and selection do not record reviews.
        """
        cards = self._deck_handler.filter_cards_by_category(
            self._deck_handler.cards, self._categories
        )
        try:
            if self._review_history is None:
                self._review_history = ReviewHistory()
            # Experimental v1.2 scheduler must be explicitly enabled per launch.
            # Leave existing Review Due as the default until validated on real data.
            if (os.environ.get('FLASHCARDS_ADAPTIVE_REVIEWS') == '1'
                    or load_review_mode() == 'adaptive'):
                selected = adaptive_due_cards(cards, self._review_history)
            else:
                selected = prioritized_due_cards(cards, self._review_history)
        except (sqlite3.Error, OSError, RuntimeError, ValueError) as error:
            messagebox.showwarning(
                "Review unavailable", f"Could not load due cards:\n{error}",
                parent=self.root,
            )
            return

        if not selected:
            messagebox.showinfo(
                "No reviews due", "No previously studied cards are due in the selected categories.",
                parent=self.root,
            )
            return

        try:
            for card in selected:
                result = self._input_answer_poll(card)
                if result is None or result == constants.BUTTON_RETURN_TEXT:
                    return
        finally:
            self._close_input_study_surface()

        self._show_completion()

    def show_progress(self):
        """Show progress, daily target and streaks without writing study history."""
        path = getattr(self._review_history, "path", None)
        try:
            report = load_progress(self._deck_handler.cards, db_path=path)
            goals = load_goals(self._deck_handler.cards, db_path=path)
        except (sqlite3.Error, OSError, RuntimeError, ValueError) as error:
            messagebox.showwarning(
                "Progress unavailable", f"Could not read study progress:\n{error}",
                parent=self.root,
            )
            return

        window = tk.Toplevel(self.root)
        window.title("Study Progress")

        def on_save_goal(value):
            try:
                save_daily_target(value)
                return load_goals(self._deck_handler.cards, db_path=path)
            except (sqlite3.Error, OSError, RuntimeError, ValueError) as error:
                messagebox.showwarning(
                    "Goal not saved", f"Could not save daily goal:\n{error}",
                    parent=window,
                )
                return None

        self._layout_maker.create_progress_layout(
            window, report, window.destroy, goals=goals, on_save_goal=on_save_goal,
        )
        self.set_window_size(window, 560, 700)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
        window.wait_window()

    def _record_input_review(self, card, correct):
        """Persist one graded Input Study attempt (never the typed response)."""
        if self._review_history is None:
            self._review_history = ReviewHistory()
        self._review_history.record_review(card.english, card.chinese, correct, mode="input")

    def _input_study_surface(self):
        """Return the shared Input Study/Review Due window (create it once)."""
        window = getattr(self, '_input_study_window', None)
        if window is None or not window.winfo_exists():
            window = tk.Toplevel(self.root)
            self._input_study_window = window
            return window, True
        return window, False

    def _clear_input_study_surface(self, window):
        """Remove a previous question/feedback view but retain its window."""
        for key in ('<Return>', '<Escape>', '<space>'):
            window.unbind(key)
        for child in window.winfo_children():
            child.destroy()

    def _fit_input_study_surface(self, window, first_view):
        """Start at a common Q/feedback size; never shrink or move."""
        if first_view:
            self.set_window_size(window, 700, 350)
        elif not self._fullscreen:
            window.update_idletasks()
            width = max(window.winfo_width(), window.winfo_reqwidth())
            height = max(window.winfo_height(), window.winfo_reqheight())
            if width > window.winfo_width() or height > window.winfo_height():
                window.geometry(f"{width}x{height}")

    def _close_input_study_surface(self):
        """Close shared Input Study window on completion, Return, or exception."""
        window = getattr(self, '_input_study_window', None)
        self._input_study_window = None
        if window is not None:
            try:
                if window.winfo_exists():
                    window.destroy()
            except tk.TclError:
                pass

    def _input_answer_poll(self, card):
        """Grade a submitted answer once, using the same window for feedback."""
        window, first_view = self._input_study_surface()
        self._clear_input_study_surface(window)
        window.title("Q")

        result = {"action": None}
        user_input = {"value": ""}
        action = tk.StringVar(master=window, value="WAIT")

        def on_answer():
            if result["action"] is not None:
                return  # Prevent duplicate grading from double-click/Enter.
            correct = self._deck_handler.correct_answer(card.chinese, user_input["value"])
            result["action"] = "Correct" if correct else "Incorrect"
            try:
                self._record_input_review(card, correct)
            except (sqlite3.Error, OSError, RuntimeError) as error:
                messagebox.showwarning(
                    "Review not saved",
                    f"Answer checked, but the review was not saved:\n{error}",
                    parent=window,
                )
            action.set(result["action"])

        def on_return():
            if result["action"] is None:
                result["action"] = constants.BUTTON_RETURN_TEXT
                action.set(result["action"])

        def on_input_change(value):
            user_input["value"] = value

        window.protocol("WM_DELETE_WINDOW", on_return)
        self._layout_maker.create_input_front_layout(
            window, card.english, on_answer, on_return, on_input_change
        )
        self._fit_input_study_surface(window, first_view)
        window.wait_variable(action)

        if result["action"] in ("Correct", "Incorrect"):
            if result["action"] == "Correct":
                feedback_action = self._show_correct_answer(card)
            else:
                feedback_action = self._show_incorrect_answer(card)
            if feedback_action == "RETURN":
                return constants.BUTTON_RETURN_TEXT
        return result["action"]

    def _show_input_feedback(self, card, correct):
        """Show timed feedback in the *same* Tk window, with safe cancellation."""
        window, first_view = self._input_study_surface()
        self._clear_input_study_surface(window)
        window.title("A")
        state = tk.StringVar(master=window, value="WAIT")

        def on_return():
            state.set("RETURN")

        window.protocol("WM_DELETE_WINDOW", on_return)
        window.bind('<Escape>', lambda event: on_return())
        if correct:
            self._layout_maker.create_input_back_layout(
                window, card.english, card.chinese
            )
        else:
            self._layout_maker.create_incorrect_layout(
                window, card.english, card.chinese
            )
        self._fit_input_study_surface(window, first_view)

        timer = window.after(
            max(1, int(constants.ANSWER_DISPLAY_DELAY_SEC * 1000)),
            lambda: state.set("NEXT"),
        )
        try:
            window.wait_variable(state)
        finally:
            try:
                window.after_cancel(timer)
            except tk.TclError:
                pass
        return state.get()

    def _show_correct_answer(self, card):
        """Display correct feedback without creating a separate window."""
        return self._show_input_feedback(card, correct=True)

    def _show_incorrect_answer(self, card):
        """Display incorrect feedback without creating a separate window."""
        return self._show_input_feedback(card, correct=False)

    def auto_study(self, priority=False):
        """Cycle flashcards with an interruptible timer and visible controls."""
        while True:
            self._deck_handler.shuffle_deck()
            source = (self._deck_handler.priority_cards if priority
                      else self._deck_handler.cards)
            cards = self._deck_handler.filter_cards_by_category(
                source, self._categories
            )
            if not cards:
                messagebox.showinfo("Auto Study", "No cards match the selected categories.")
                return

            for card in cards:
                window = tk.Toplevel(self.root)
                window.title("Auto Study")
                state = {
                    "action": None, "paused": False, "stopped": False,
                    "remaining": max(0.0, float(constants.AUTO_DISPLAY_DELAY_SEC)),
                    "started": None, "timeout": None,
                }

                def cancel_timeout():
                    if state["timeout"] is not None:
                        window.after_cancel(state["timeout"])
                        state["timeout"] = None

                def advance():
                    state["timeout"] = None
                    if not state["paused"] and not state["stopped"]:
                        state["action"] = "NEXT"
                        window.destroy()

                def schedule():
                    state["started"] = time.monotonic()
                    state["timeout"] = window.after(
                        max(1, round(state["remaining"] * 1000)), advance
                    )

                def set_pause_label(text):
                    button = controls["pause"]
                    button.configure(text=text)
                    if hasattr(button, "_coloured_face"):
                        button._coloured_face.configure(text=text)

                def pause_resume():
                    if state["stopped"]:
                        return
                    if state["paused"]:
                        state["paused"] = False
                        controls["status"].configure(text="Playing")
                        set_pause_label("Pause")
                        schedule()
                    else:
                        state["paused"] = True
                        state["remaining"] = max(
                            0.0, state["remaining"] -
                            (time.monotonic() - state["started"])
                        )
                        cancel_timeout()
                        controls["status"].configure(text="Paused")
                        set_pause_label("Resume")

                def stop():
                    state["stopped"] = True
                    cancel_timeout()
                    controls["pause"].configure(state="disabled")
                    controls["stop"].configure(state="disabled")
                    controls["status"].configure(
                        text="Stopped — select Return to Menu"
                    )

                def return_to_menu():
                    state["action"] = "RETURN"
                    cancel_timeout()
                    window.destroy()

                controls = self._layout_maker.create_auto_layout(
                    window, card.english, card.chinese,
                    on_pause_resume=pause_resume, on_stop=stop,
                    on_return=return_to_menu,
                )
                self.set_window_size(window, 520, 260)
                window.protocol("WM_DELETE_WINDOW", return_to_menu)
                schedule()
                window.wait_window()
                if state["action"] != "NEXT":
                    return

    def add_cards(self):
        window = tk.Toplevel(self.root)
        window.title("Add")

        added_status = {"status": "start"}
        user_input = {"value": ""}

        def on_add():
            text = user_input["value"].strip()
            sides = text.split(constants.CARD_SIDE_DELIMITER, 1)
            if len(sides) == 2 and all(part.strip() for part in sides):
                self._deck_handler.add_cards(text + "\n")
                user_input["value"] = ""
                added_status["status"] = "added"
            else:
                added_status["status"] = "invalid"

            # Recreate layout with feedback
            for widget in window.winfo_children():
                widget.destroy()

            self._layout_maker.create_add_cards_layout(window, on_add, on_return, on_input_change, added_status["status"])

        def on_return():
            window.destroy()

        def on_input_change(value):
            user_input["value"] = value

        self._layout_maker.create_add_cards_layout(window, on_add, on_return, on_input_change, "start")

        self.set_window_size(window, 640, 230)
        window.wait_window()

    def select_categories(self):
        window = tk.Toplevel(self.root)
        window.title("Category Select")

        category_vars = {}

        def on_save():
            for category, var in category_vars.items():
                self._categories[category] = var.get()
                print(f"Saving category checkboxes. set categories[{category}] = {var.get()}")
            window.destroy()

        self._layout_maker.create_category_select_layout(window, self._categories, category_vars, on_save)

        window_y = min(760, max(330, 180 + 35 * len(self._categories)))
        self.set_window_size(window, 350, window_y)
        window.wait_window()

    def set_window_size(self, window, default_x=520, default_y=380):
        """Respect each screen's requested size so controls are not clipped."""
        if self._fullscreen:
            window.attributes('-fullscreen', True)
        else:
            # The former fixed sizes clipped buttons on macOS, especially in
            # Study Recent and Input Study. Calculate the complete layout first.
            window.update_idletasks()
            required_width = window.winfo_reqwidth()
            required_height = window.winfo_reqheight()
            window.minsize(required_width, required_height)
            window.geometry(
                f"{max(default_x, required_width)}x{max(default_y, required_height)}"
            )

    def toggle_fullscreen(self, window):
        self._fullscreen = not self._fullscreen
        if window:
            window.attributes('-fullscreen', self._fullscreen)

    def toggle_audio(self):
        window = tk.Toplevel(self.root)
        window.title("Toggle audio")

        self.set_window_size(window, 240, 120)

        self.root.after(int(constants.TOGGLE_DISPLAY_DELAY_SEC * 1000), window.destroy)
        window.wait_window()

    def run(self):
        """Run menu's Tk event loop, then close the hidden root cleanly."""
        try:
            self.start_menu()
        finally:
            if self.root.winfo_exists():
                self.root.destroy()
