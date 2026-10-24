import tkinter as tk
import sys
from tkinter import ttk
import constants


def _mac_buttons_need_overlay():
    # Native Aqua tk.Button ignores -background; draw a coloured face above it.
    return sys.platform == 'darwin'


class TkLayoutMaker:

    def __init__(self):
        # Theme colors
        self.bg_color = "#F4F6FA"
        self.fg_color = "#17212B"
        self.button_bg = "#DEE5EE"
        self.entry_bg = "#FFFFFF"
        self.button_active_bg = "#CBD6E5"
        self.yellow_color = "#895000"
        self.green_color = "#116239"
        self.red_color = "#A61B1B"

    def _create_button(self, parent, text, command, width=12, height=2, focus=False):
        """Create a styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.button_bg,
            fg=self.fg_color,
            activebackground=self.button_active_bg,
            activeforeground=self.fg_color,
            font=('Arial', 10),
            width=width,
            height=height,
            relief=tk.RAISED,
            borderwidth=2
        )
        if _mac_buttons_need_overlay():
            # Aqua accepts bg= but paints the native white face regardless.
            # A Label inside the real Button is rendered with our chosen colour.
            # Retain the native button for keyboard access and .invoke().
            face = tk.Label(
                btn, text=text, bg=self.button_bg, fg=self.fg_color,
                font=('Arial', 10), relief=tk.RAISED, borderwidth=1,
                cursor='hand2', takefocus=0,
            )
            face.place(x=2, y=2, relwidth=1, relheight=1, width=-4, height=-4)
            face.bind('<Enter>', lambda event: face.configure(bg=self.button_active_bg))
            face.bind('<Leave>', lambda event: face.configure(bg=self.button_bg))
            face.bind('<ButtonPress-1>', lambda event: face.configure(bg=self.button_active_bg))
            face.bind('<ButtonRelease-1>', lambda event: btn.invoke()
                      if face.winfo_containing(event.x_root, event.y_root) == face
                      else None)
            btn._coloured_face = face  # Keep the visible face accessible for tests.
        if focus:
            btn.focus_set()
        return btn

    def _create_label(self, parent, text, font_size=12, color=None, **kwargs):
        """Create a styled label"""
        fg = color if color else self.fg_color
        return tk.Label(
            parent,
            text=text,
            bg=self.bg_color,
            fg=fg,
            font=('Arial', font_size),
            **kwargs
        )

    def create_completed_layout(self, window, on_complete):
        """Create completion screen"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        label = self._create_label(frame, "Completed all flash cards. Nice!", 14)
        label.pack(pady=20)

        btn = self._create_button(frame, "Complete", on_complete, width=15, height=2)
        btn.pack(pady=10)

    def create_start_layout(self, window, card_count, on_menu_selection,
                            on_background=None, on_buttons=None):
        """Create start menu with small stacked appearance controls on the right."""
        window.configure(bg=self.bg_color)

        if on_background is not None or on_buttons is not None:
            top_bar = tk.Frame(window, bg=self.bg_color)
            top_bar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(5, 0))
            controls = tk.Frame(top_bar, bg=self.bg_color)
            controls.pack(side=tk.RIGHT)
            for label, callback in (("Background", on_background),
                                    ("Buttons", on_buttons)):
                if callback is None:
                    continue
                row = tk.Frame(controls, bg=self.bg_color)
                row.pack(side=tk.TOP, fill=tk.X, pady=1)
                picker = self._create_button(
                    row, label, callback, width=10, height=1
                )
                picker.configure(font=('Arial', 9), borderwidth=1)
                picker.pack(side=tk.RIGHT)

        main_frame = tk.Frame(window, bg=self.bg_color)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Card count label
        count_label = self._create_label(
            main_frame,
            f"Cards: {card_count}",
            18,
            self.yellow_color
        )
        count_label.pack(pady=10)

        # Spacer
        tk.Frame(main_frame, bg=self.bg_color, height=20).pack()

        # First row of buttons
        row1 = tk.Frame(main_frame, bg=self.bg_color)
        row1.pack(pady=5)

        self._create_button(
            row1, "Study",
            lambda: on_menu_selection("Study")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row1, "Study Recent",
            lambda: on_menu_selection("Study Recent (100)")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row1, "Priority Study",
            lambda: on_menu_selection("Priority Study")
        ).pack(side=tk.LEFT, padx=5)

        # Second row of buttons
        row2 = tk.Frame(main_frame, bg=self.bg_color)
        row2.pack(pady=5)

        self._create_button(
            row2, "Input Study",
            lambda: on_menu_selection("Input Study")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row2, "Auto",
            lambda: on_menu_selection("Auto")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row2, "Auto Priority",
            lambda: on_menu_selection("Auto Priority")
        ).pack(side=tk.LEFT, padx=5)

        # Review Due is an independent typed-answer mode.
        review_row = tk.Frame(main_frame, bg=self.bg_color)
        review_row.pack(pady=5)
        self._create_button(
            review_row, "Review Due",
            lambda: on_menu_selection("Review Due"), width=20
        ).pack(side=tk.LEFT, padx=5)
        self._create_button(
            review_row, "Progress",
            lambda: on_menu_selection("Progress"), width=18
        ).pack(side=tk.LEFT, padx=5)

        # Spacer
        tk.Frame(main_frame, bg=self.bg_color, height=20).pack()

        # Third row of buttons
        row3 = tk.Frame(main_frame, bg=self.bg_color)
        row3.pack(pady=5)

        self._create_button(
            row3, "Add Cards",
            lambda: on_menu_selection("Add Cards")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row3, "Generate Audio",
            lambda: on_menu_selection("Generate Audio")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row3, "Categories",
            lambda: on_menu_selection("Categories")
        ).pack(side=tk.LEFT, padx=5)

        # Fourth row of buttons
        row4 = tk.Frame(main_frame, bg=self.bg_color)
        row4.pack(pady=5)

        self._create_button(
            row4, "Toggle Audio",
            lambda: on_menu_selection("Toggle Audio")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row4, "Fullscreen",
            lambda: on_menu_selection("Fullscreen")
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            row4, "Exit",
            lambda: on_menu_selection("Exit")
        ).pack(side=tk.LEFT, padx=5)

    def create_progress_layout(self, window, report, on_return, *, goals=None, on_save_goal=None):
        """Render saved graded progress; do not mutate history or deck state."""
        window.configure(bg=self.bg_color)
        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=15)

        self._create_label(frame, "Study Progress", 20).pack(pady=(0, 10))
        metrics = (
            ("Unique deck cards", report.total_cards),
            ("Cards reviewed", report.reviewed_cards),
            ("Cards due now", report.due_cards),
            ("Graded attempts", report.attempts),
            ("Correct attempts", report.correct),
            ("Answer accuracy", "Not yet available" if report.accuracy_percent is None
             else f"{report.accuracy_percent}%"),
        )
        for name, value in metrics:
            row = tk.Frame(frame, bg=self.bg_color)
            row.pack(fill=tk.X, pady=2)
            self._create_label(row, name, 11).pack(side=tk.LEFT)
            self._create_label(row, str(value), 11, self.green_color).pack(side=tk.RIGHT)

        if goals is not None:
            self._create_label(frame, "Daily Study Goal", 14).pack(pady=(12, 3))
            summary = self._create_label(
                frame, f"Today: {goals.completed_today}/{goals.target} graded reviews", 11
            )
            summary.pack(pady=2)
            progress_track = tk.Frame(frame, bg=self.button_bg, height=12, width=260)
            progress_track.pack(pady=3)
            progress_track.pack_propagate(False)
            progress_fill = tk.Frame(progress_track, bg=self.green_color, height=12)
            progress_fill.place(x=0, y=0, width=round(260 * min(1, goals.completed_today / goals.target)))
            completion = self._create_label(
                frame, "Daily goal achieved" if goals.goal_reached
                else f"{goals.remaining} reviews to reach today's goal", 10
            )
            completion.pack(pady=2)
            streak = self._create_label(
                frame,
                f"Current streak: {goals.current_streak} days    Longest: {goals.longest_streak} days",
                11,
            )
            streak.pack(pady=2)
            self._create_label(
                frame, "Streaks count days with at least one graded review.", 9
            ).pack(pady=1)
            if on_save_goal is not None:
                edit_row = tk.Frame(frame, bg=self.bg_color)
                edit_row.pack(pady=4)
                self._create_label(edit_row, "Daily target (1–500):", 10).pack(side=tk.LEFT, padx=4)
                target_value = tk.StringVar(master=window, value=str(goals.target))
                entry = tk.Spinbox(
                    edit_row, from_=1, to=500, width=5, textvariable=target_value,
                    font=('Arial', 11), bg=self.entry_bg, fg=self.fg_color,
                )
                entry.pack(side=tk.LEFT, padx=4)

                def save_goal():
                    try:
                        value = int(entry.get())
                    except ValueError:
                        from tkinter import messagebox
                        messagebox.showwarning(
                            "Invalid goal", "Enter a whole number from 1 to 500.", parent=window
                        )
                        return
                    updated = on_save_goal(value)
                    if updated is not None:
                        summary.configure(
                            text=f"Today: {updated.completed_today}/{updated.target} graded reviews"
                        )
                        streak.configure(
                            text=f"Current streak: {updated.current_streak} days    "
                                 f"Longest: {updated.longest_streak} days"
                        )
                        target_value.set(str(updated.target))
                        progress_fill.place_configure(
                            width=round(260 * min(1, updated.completed_today / updated.target))
                        )
                        completion.configure(
                            text="Daily goal achieved" if updated.goal_reached
                            else f"{updated.remaining} reviews to reach today's goal"
                        )

                self._create_button(
                    edit_row, "Save Goal", save_goal, width=12, height=1
                ).pack(side=tk.LEFT, padx=4)

        self._create_label(frame, "Graded reviews — last 7 days", 13).pack(
            pady=(16, 7)
        )
        max_count = max((count for _, count in report.daily_reviews), default=0)
        for day, count in report.daily_reviews:
            row = tk.Frame(frame, bg=self.bg_color)
            row.pack(fill=tk.X, pady=2)
            self._create_label(row, day.strftime("%a %d %b"), 10,
                               width=13, anchor="w").pack(side=tk.LEFT)
            track = tk.Frame(row, bg=self.button_bg, height=13, width=210)
            track.pack(side=tk.LEFT, padx=(6, 8))
            track.pack_propagate(False)
            if count:
                tk.Frame(track, bg=self.green_color, height=13,
                         width=round(count * 210 / max_count)).place(x=0, y=0)
            self._create_label(row, str(count), 10).pack(side=tk.LEFT)

        self._create_label(
            frame, "Only graded answers count. Viewing cards and Auto Study do not.",
            9, wraplength=450, justify=tk.CENTER,
        ).pack(pady=(16, 6))
        self._create_button(frame, "Return to Menu", on_return, width=19,
                            height=1).pack(pady=(4, 0))

    def create_display_front_layout(self, window, key, on_answer, on_return):
        """Create front of flashcard display"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        label = self._create_label(frame, str(key), 18)
        label.pack(pady=20)

        tk.Label(frame, text="", bg=self.bg_color).pack()

        button_frame = tk.Frame(frame, bg=self.bg_color)
        button_frame.pack(pady=10)

        self._create_button(
            button_frame,
            constants.BUTTON_ANSWER_TEXT,
            on_answer,
            width=40,
            height=4,
            focus=True
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            button_frame,
            constants.BUTTON_RETURN_TEXT,
            on_return,
            width=16,
            height=4
        ).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to answer
        window.bind('<Return>', lambda e: on_answer())

    def create_display_back_layout(self, window, key, value, priority,
                                   on_next, on_priority, on_return):
        """Create back of flashcard display"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        key_label = self._create_label(frame, str(key) + ':', 28)
        key_label.pack(pady=5)

        value_label = self._create_label(frame, str(value), 28, self.yellow_color)
        value_label.pack(pady=5)

        tk.Label(frame, text="", bg=self.bg_color).pack()

        button_frame = tk.Frame(frame, bg=self.bg_color)
        button_frame.pack(pady=10)

        if priority:
            self._create_button(
                button_frame,
                constants.BUTTON_NEXT_TEXT,
                on_next,
                width=46,
                height=4,
                focus=True
            ).pack(side=tk.LEFT, padx=5)

            self._create_button(
                button_frame,
                constants.BUTTON_RETURN_TEXT,
                on_return,
                width=22,
                height=4
            ).pack(side=tk.LEFT, padx=5)
        else:
            self._create_button(
                button_frame,
                constants.BUTTON_NEXT_TEXT,
                on_next,
                width=46,
                height=3,
                focus=True
            ).pack(side=tk.LEFT, padx=5)

            self._create_button(
                button_frame,
                constants.BUTTON_PRIORITY_TEXT,
                on_priority,
                width=8,
                height=3
            ).pack(side=tk.LEFT, padx=5)

            self._create_button(
                button_frame,
                constants.BUTTON_RETURN_TEXT,
                on_return,
                width=8,
                height=3
            ).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to next
        window.bind('<Return>', lambda e: on_next())

    def create_input_front_layout(self, window, key, on_answer, on_return, on_input_change):
        """Create input study front layout"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        label = self._create_label(frame, str(key), 18)
        label.pack(pady=10)

        entry = tk.Entry(
            frame,
            width=40,
            font=('Arial', 12),
            bg=self.entry_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color
        )
        entry.pack(pady=10)
        entry.focus_set()

        # Update on change
        entry.bind('<KeyRelease>', lambda e: on_input_change(entry.get()))

        button_frame = tk.Frame(frame, bg=self.bg_color)
        button_frame.pack(pady=10)

        self._create_button(
            button_frame,
            constants.BUTTON_ANSWER_TEXT,
            on_answer,
            width=7,
            height=3
        ).pack(side=tk.LEFT, padx=5)

        self._create_button(
            button_frame,
            constants.BUTTON_RETURN_TEXT,
            on_return,
            width=7,
            height=3
        ).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to answer
        window.bind('<Return>', lambda e: on_answer())
        window.bind('<Escape>', lambda e: on_return())

    def create_input_back_layout(self, window, key, value):
        """Create input study back layout (correct answer)"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        key_label = self._create_label(frame, str(key) + ':', 28, self.green_color)
        key_label.pack(pady=5)

        value_label = self._create_label(frame, str(value), 28, self.yellow_color)
        value_label.pack(pady=5)

    def create_incorrect_layout(self, window, key, value):
        """Create incorrect answer layout"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        incorrect_label = self._create_label(frame, "INCORRECT", 18, self.red_color)
        incorrect_label.pack(pady=10)

        tk.Label(frame, text="", bg=self.bg_color, font=('Arial', 18)).pack()

        answer_frame = tk.Frame(frame, bg=self.bg_color)
        answer_frame.pack(pady=10)

        key_label = self._create_label(answer_frame, str(key) + "   :", 28)
        key_label.pack(side=tk.LEFT, padx=5)

        value_label = self._create_label(answer_frame, str(value), 28, self.yellow_color)
        value_label.pack(side=tk.LEFT, padx=5)

    def create_auto_layout(self, window, key, value, on_pause_resume=None,
                           on_stop=None, on_return=None):
        """Create Auto Study display, optionally with playback controls."""
        window.configure(bg=self.bg_color)
        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=12)

        self._create_label(frame, str(key) + ':', 28).pack(pady=5)
        self._create_label(frame, str(value), 28, self.yellow_color).pack(pady=5)

        if not all((on_pause_resume, on_stop, on_return)):
            return None  # Compatible with existing display-only callers.

        status = self._create_label(frame, "Playing", 11)
        status.pack(pady=(5, 0))
        row = tk.Frame(frame, bg=self.bg_color)
        row.pack(pady=(7, 0))
        pause = self._create_button(
            row, "Pause", on_pause_resume, width=12, height=1
        )
        pause.pack(side=tk.LEFT, padx=5)
        stop = self._create_button(
            row, "Stop", on_stop, width=12, height=1
        )
        stop.pack(side=tk.LEFT, padx=5)
        back = self._create_button(
            row, "Return to Menu", on_return, width=16, height=1
        )
        back.pack(side=tk.LEFT, padx=5)
        return {"pause": pause, "stop": stop, "return": back, "status": status}

    def create_add_cards_layout(self, window, on_add, on_return, on_input_change, status):
        """Add vocabulary with a visible input and validation feedback."""
        window.configure(bg=self.bg_color)
        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=18, pady=14)

        self._create_label(frame, "Add vocabulary", 16).pack(pady=(0, 6))
        self._create_label(
            frame, "Format: English : pinyin 汉字  (optional : [Category])", 10
        ).pack(pady=(0, 6))

        entry = tk.Entry(frame, width=55, font=('Arial', 12),
                         bg=self.entry_bg, fg=self.fg_color,
                         insertbackground=self.fg_color)
        entry.pack(pady=6, fill=tk.X)
        entry.focus_set()

        feedback = {
            'start': 'Enter a card, then press Add.',
            'added': 'Card added successfully.',
            'invalid': 'Invalid card: both sides of the colon must contain text.',
        }
        feedback_colour = (self.red_color if status == 'invalid'
                           else self.green_color if status == 'added'
                           else self.fg_color)
        self._create_label(frame, feedback.get(status, ''), 10,
                           feedback_colour).pack(pady=4)

        def submit(event=None):
            on_input_change(entry.get())  # also works when input was pasted
            on_add()

        actions = tk.Frame(frame, bg=self.bg_color)
        actions.pack(pady=8)
        self._create_button(actions, 'Add', submit, width=14, height=2).pack(
            side=tk.LEFT, padx=8)
        self._create_button(actions, 'Return', on_return, width=14, height=2).pack(
            side=tk.LEFT, padx=8)
        entry.bind('<KeyRelease>', lambda event: on_input_change(entry.get()))
        window.bind('<Return>', submit)

    def create_category_select_layout(self, window, categories, category_vars, on_save):
        """Display selectable categories, with 'All' mutually exclusive."""
        window.configure(bg=self.bg_color)
        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=16, pady=12)
        self._create_label(frame, 'Study categories', 16).pack(pady=(0, 5))
        self._create_label(frame, 'Select All or one or more categories.', 10).pack(
            pady=(0, 8))

        panel = tk.Frame(frame, bg=self.bg_color)
        panel.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(panel, bg=self.bg_color, highlightthickness=0,
                           borderwidth=0)
        scrollbar = tk.Scrollbar(panel, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        checks = tk.Frame(canvas, bg=self.bg_color)
        embedded = canvas.create_window((0, 0), window=checks, anchor='nw')
        checks.bind('<Configure>', lambda event: canvas.configure(
            scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(
            embedded, width=event.width))

        for category, enabled in categories.items():
            category_vars[category] = tk.BooleanVar(master=window, value=bool(enabled))

        def changed(chosen):
            if chosen == constants.CATEGORY_ALL:
                if category_vars[chosen].get():
                    for other, variable in category_vars.items():
                        if other != constants.CATEGORY_ALL:
                            variable.set(False)
            elif category_vars[chosen].get():
                if constants.CATEGORY_ALL in category_vars:
                    category_vars[constants.CATEGORY_ALL].set(False)

        for category, variable in category_vars.items():
            checkbox = tk.Checkbutton(
                checks, text=category, variable=variable,
                command=lambda name=category: changed(name),
                bg=self.bg_color, fg=self.fg_color,
                selectcolor=self.button_bg,
                activebackground=self.bg_color, activeforeground=self.fg_color,
                anchor='w', font=('Arial', 11))
            checkbox.pack(fill=tk.X, anchor='w', pady=2)

        def save():
            if not any(variable.get() for variable in category_vars.values()):
                from tkinter import messagebox
                messagebox.showwarning('Select a category',
                                       'Please select at least one category.',
                                       parent=window)
                return
            on_save()

        self._create_button(frame, 'Save categories', save, width=22, height=2).pack(
            pady=(10, 0))
