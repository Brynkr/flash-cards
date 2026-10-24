"""Small, non-persistent study-session options for regular flashcard Study.

Selection respects the existing shuffled/category-filtered card order. Nothing
here writes review history, vocabulary, preferences or scheduling records.
"""

import tkinter as tk
from tkinter import ttk


DEFAULT_SESSION_SIZE = "20"
SESSION_SIZES = ("10", "20", "50", "all")


def select_session_cards(cards, selection=DEFAULT_SESSION_SIZE):
    """Return at most N distinct cards in existing order (or all distinct cards).

    Cards with exactly the same English and Chinese text appear once per
    session even if they appear multiple times in the input deck.
    """
    if selection not in SESSION_SIZES:
        raise ValueError("Session size must be 10, 20, 50 or all")

    limit = None if selection == "all" else int(selection)
    result = []
    seen = set()
    for card in cards:
        key = (card.english, card.chinese)
        if key in seen:
            continue
        seen.add(key)
        result.append(card)
        if limit is not None and len(result) >= limit:
            break
    return result


def choose_study_size(parent):
    """Modal preset picker; return selection string or None if cancelled."""
    window = tk.Toplevel(parent)
    window.title("Study session")
    window.resizable(False, False)
    # Avoid inheriting the hidden state of a withdrawn Tk root.
    if parent.winfo_viewable():
        window.transient(parent)

    frame = ttk.Frame(window, padding=18)
    frame.pack(fill=tk.BOTH, expand=True)
    ttk.Label(frame, text="How many cards would you like to study?").pack(
        anchor=tk.W, pady=(0, 12)
    )

    selected = tk.StringVar(master=window, value=DEFAULT_SESSION_SIZE)
    for label, value in (
        ("10 cards — quick session", "10"),
        ("20 cards — balanced session (default)", "20"),
        ("50 cards — longer session", "50"),
        ("All available cards", "all"),
    ):
        ttk.Radiobutton(frame, text=label, variable=selected, value=value).pack(
            anchor=tk.W, pady=3
        )

    outcome = {"selection": None}

    def finish(accept):
        if accept:
            outcome["selection"] = selected.get()
        window.destroy()

    actions = ttk.Frame(frame)
    actions.pack(fill=tk.X, pady=(14, 0))
    ttk.Button(actions, text="Cancel", command=lambda: finish(False)).pack(
        side=tk.RIGHT, padx=(8, 0)
    )
    start = ttk.Button(actions, text="Start study", command=lambda: finish(True))
    start.pack(side=tk.RIGHT)

    window.bind("<Return>", lambda _e: finish(True))
    window.bind("<Escape>", lambda _e: finish(False))
    window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
    window.update_idletasks()
    window.minsize(window.winfo_reqwidth(), window.winfo_reqheight())
    start.focus_set()
    window.grab_set()
    window.wait_window()
    return outcome["selection"]
