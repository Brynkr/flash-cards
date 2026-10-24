"""Private, persistent choice of Review Due scheduling mode.

The choice is a preference only: neither loading nor saving it changes review
history, card data, or calculated review dates. It is backed up with user data.
"""
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk

import constants

DEFAULT_MODE = "standard"
MODES = ("standard", "adaptive")
FILENAME = "review_settings.json"


def settings_file():
    return Path(constants.CARD_PATH).expanduser().with_name(FILENAME)


def _mode(value):
    if value not in MODES or not isinstance(value, str):
        raise ValueError("Review mode must be standard or adaptive")
    return value


def load_review_mode(path=None):
    """Return a validated saved preference or the safe v1.1 default."""
    dest = Path(path) if path is not None else settings_file()
    if dest.is_symlink():
        raise ValueError("Review settings may not be a symbolic link")
    if not dest.exists():
        return DEFAULT_MODE
    document = json.loads(dest.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("version") != 1:
        raise ValueError("Unsupported review settings format")
    return _mode(document.get("review_mode"))


def save_review_mode(mode, path=None):
    """Save the explicit preference atomically with private file permissions."""
    _mode(mode)
    dest = Path(path) if path is not None else settings_file()
    if dest.is_symlink():
        raise ValueError("Review settings may not be a symbolic link")
    dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        fd, name = tempfile.mkstemp(prefix=".review-settings-", suffix=".tmp", dir=dest.parent)
        temporary = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"version": 1, "review_mode": mode}, stream, sort_keys=True)
            stream.write("\n")
        temporary.chmod(0o600)
        os.replace(temporary, dest)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def choose_review_mode(parent, selected_mode=DEFAULT_MODE):
    """Let the user choose a saved mode. Cancel returns None and writes nothing."""
    _mode(selected_mode)
    window = tk.Toplevel(parent)
    window.title("Review settings")
    window.resizable(False, False)
    if parent.winfo_viewable():
        window.transient(parent)

    frame = ttk.Frame(window, padding=18)
    frame.pack(fill=tk.BOTH, expand=True)
    ttk.Label(frame, text="Review Due scheduling").pack(anchor=tk.W, pady=(0, 9))
    selected = tk.StringVar(master=window, value=selected_mode)
    for label, mode in (
        ("Standard — v1.1 intervals", "standard"),
        ("Adaptive — v1.2 experimental intervals", "adaptive"),
    ):
        ttk.Radiobutton(frame, text=label, variable=selected, value=mode).pack(anchor=tk.W, pady=4)
    ttk.Label(frame, text="Your review history will not be changed.").pack(anchor=tk.W, pady=(10, 2))
    outcome = {"mode": None}

    def finish(save):
        if save:
            outcome["mode"] = selected.get()
        window.destroy()

    actions = ttk.Frame(frame)
    actions.pack(fill=tk.X, pady=(14, 0))
    ttk.Button(actions, text="Cancel", command=lambda: finish(False)).pack(side=tk.RIGHT, padx=(8, 0))
    save_button = ttk.Button(actions, text="Save", command=lambda: finish(True))
    save_button.pack(side=tk.RIGHT)
    window.bind("<Return>", lambda _event: finish(True))
    window.bind("<Escape>", lambda _event: finish(False))
    window.protocol("WM_DELETE_WINDOW", lambda: finish(False))
    window.update_idletasks()
    window.minsize(window.winfo_reqwidth(), window.winfo_reqheight())
    save_button.focus_set()
    window.grab_set()
    window.wait_window()
    return outcome["mode"]
