import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
import constants
from deck_handler import DeckHandler
from tk_layout_maker import TkLayoutMaker
import threading


class GUI:
    MENU_STUDY = "Study"
    MENU_STUDY_RECENT = "Study Recent (100)"
    MENU_PRIORITY_STUDY = "Priority Study"
    MENU_INPUT_STUDY = "Input Study"
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
        """Apply a dark theme"""
        bg_color = "#2b2b2b"
        fg_color = "#2c5059"
        button_bg = "#e60e0e"

        self.root.configure(bg=bg_color)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background=button_bg, foreground=fg_color,
                        borderwidth=1, font=('Arial', 10))
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)

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
                self._on_menu_selection
            )

            self.set_window_size(self.current_window, 420, 380)

            # Wait for window to close
            self.current_window.wait_window()

            # Check if we should exit
            if not hasattr(self, '_next_action'):
                break

            action = self._next_action
            delattr(self, '_next_action')

            match action:
                case self.MENU_STUDY:
                    self.display_study()
                case self.MENU_STUDY_RECENT:
                    self.display_study(recent=True)
                case self.MENU_PRIORITY_STUDY:
                    self.display_study(priority=True)
                case self.MENU_INPUT_STUDY:
                    self.input_study()
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

    def _on_menu_selection(self, action):
        """Callback for menu button clicks"""
        match action:
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

    def display_study(self, recent=False, priority=False):
        if recent:
            cards = self._deck_handler.filter_cards_by_category(self._deck_handler.recent_cards,
                                                                self._categories)
        elif priority:
            cards = self._deck_handler.filter_cards_by_category(self._deck_handler.priority_cards,
                                                                self._categories)
        else:
            cards = self._deck_handler.filter_cards_by_category(self._deck_handler.cards,
                                                                self._categories)

        for card in cards:
            print(f"front = {card.english}, back = {card.chinese}")

            # Show front of card
            result = self._show_card_front(card, priority)

            if result == "RETURN":
                return
            elif result == "SHOW_BACK":
                back_result = self._show_card_back(card, priority)
                if back_result == "RETURN":
                    return

        # Show completion message
        self._show_completion()

    def _show_card_front(self, card, priority):
        """Show the front of a flashcard"""
        window = tk.Toplevel(self.root)
        window.title("Q")

        result = {"action": None}

        def on_answer():
            result["action"] = "SHOW_BACK"
            window.destroy()

        def on_return():
            result["action"] = "RETURN"
            window.destroy()

        self._layout_maker.create_display_front_layout(
            window, card.english, on_answer, on_return
        )

        self.set_window_size(window, 520, 160)
        window.wait_window()

        return result["action"]

    def _show_card_back(self, card, priority):
        """Show the back of a flashcard"""
        window = tk.Toplevel(self.root)
        window.title("A")

        result = {"action": None}

        def on_next():
            result["action"] = "NEXT"
            window.destroy()

        def on_priority():
            self._deck_handler.add_priority_card(card.english, card.chinese)
            result["action"] = "NEXT"
            window.destroy()

        def on_return():
            result["action"] = "RETURN"
            window.destroy()

        self._layout_maker.create_display_back_layout(
            window, card.english, card.chinese, priority,
            on_next, on_priority, on_return
        )

        self.set_window_size(window, 640, 210)
        window.wait_window()

        return result["action"]

    def _show_completion(self):
        """Show completion message"""
        window = tk.Toplevel(self.root)
        window.title("Complete")

        self._layout_maker.create_completed_layout(window, lambda: window.destroy())

        self.set_window_size(window, 300, 150)
        window.wait_window()

    def input_study(self):
        cards = self._deck_handler.filter_cards_by_category(self._deck_handler.cards, self._categories)

        for card in cards:
            print(f"front = {card.english}, back = {card.chinese}")

            result = self._input_answer_poll(card)

            if result == constants.BUTTON_RETURN_TEXT:
                return

        self._show_completion()

    def _input_answer_poll(self, card):
        """Poll for input answer"""
        window = tk.Toplevel(self.root)
        window.title("Q")

        result = {"action": None}
        user_input = {"value": ""}

        def on_answer():
            if self._deck_handler.correct_answer(card.chinese, user_input["value"]):
                window.destroy()
                self._show_correct_answer(card)
                result["action"] = "Correct"
            else:
                window.destroy()
                self._show_incorrect_answer(card)
                result["action"] = "Incorrect"

        def on_return():
            result["action"] = constants.BUTTON_RETURN_TEXT
            window.destroy()

        def on_input_change(value):
            user_input["value"] = value

        self._layout_maker.create_input_front_layout(
            window, card.english, on_answer, on_return, on_input_change
        )

        self.set_window_size(window, 260, 150)
        window.wait_window()

        return result["action"]

    def _show_correct_answer(self, card):
        """Show correct answer feedback"""
        window = tk.Toplevel(self.root)
        window.title("A")

        self._layout_maker.create_input_back_layout(window, card.english, card.chinese)

        self.set_window_size(window, 280, 220)

        self.root.after(int(constants.ANSWER_DISPLAY_DELAY_SEC * 1000), window.destroy)
        window.wait_window()

    def _show_incorrect_answer(self, card):
        """Show incorrect answer feedback"""
        window = tk.Toplevel(self.root)
        window.title("Q")

        self._layout_maker.create_incorrect_layout(window, card.english, card.chinese)

        self.set_window_size(window, 640, 220)
        self.root.after(int(constants.ANSWER_DISPLAY_DELAY_SEC * 1000), window.destroy)
        window.wait_window()

    def auto_study(self, priority=False):
        while True:
            self._deck_handler.shuffle_deck()

            if priority:
                cards = self._deck_handler.filter_cards_by_category(
                    self._deck_handler.priority_cards, self._categories
                )
            else:
                cards = self._deck_handler.filter_cards_by_category(
                    self._deck_handler.cards, self._categories
                )

            for card in cards:
                print(f"front = {card.english}, back = {card.chinese}")

                window = tk.Toplevel(self.root)
                window.title("Q")
                window.geometry("+950+700")

                self._layout_maker.create_auto_layout(window, card.english, card.chinese)

                self.set_window_size(window, 320, 120)

                self.root.after(int(constants.AUTO_DISPLAY_DELAY_SEC * 1000), window.destroy)
                window.wait_window()

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
        if self._fullscreen:
            window.attributes('-fullscreen', True)
        else:
            window.geometry(f"{default_x}x{default_y}")

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