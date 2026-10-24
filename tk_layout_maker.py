import tkinter as tk
from tkinter import ttk
import constants


class TkLayoutMaker:

    def __init__(self):
        # Theme colors
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.button_bg = "#404040"
        self.yellow_color = "#ffff00"
        self.green_color = "#00ff00"
        self.red_color = "#ff0000"

    def _create_button(self, parent, text, command, width=12, height=2, focus=False):
        """Create a styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.button_bg,
            fg=self.fg_color,
            font=('Arial', 10),
            width=width,
            height=height,
            relief=tk.RAISED,
            borderwidth=2
        )
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

    def create_start_layout(self, window, card_count, on_menu_selection):
        """Create start menu layout"""
        window.configure(bg=self.bg_color)

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
            bg='#404040',
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

    def create_auto_layout(self, window, key, value):
        """Create auto study layout"""
        window.configure(bg=self.bg_color)

        frame = tk.Frame(window, bg=self.bg_color)
        frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        key_label = self._create_label(frame, str(key) + ':', 28)
        key_label.pack(pady=5)

        value_label = self._create_label(frame, str(value), 28, self.yellow_color)
        value_label.pack(pady=5)

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
                         bg=self.button_bg, fg=self.fg_color,
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
