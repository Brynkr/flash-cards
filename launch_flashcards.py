#!/usr/bin/env python3
"""Start Flashcards with private per-user data and a verified prelaunch backup.

Unlike the original desktop shortcut, this entry point belongs to the repo
and is independent of the clone's location or the user's account name.
"""

import os
from pathlib import Path
import shutil
import sqlite3
import sys

from tools.flashcards_backup import BackupError, create_backup


PROJECT_ROOT = Path(__file__).resolve().parent


def default_data_dir():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Flashcards-v1.1"
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "Flashcards-v1.1"


def default_backups_dir():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Flashcards-v1.1-backups"
    base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "Flashcards-v1.1-backups"


def prepare_data(data_dir, project_root=None):
    """Initialize an absent vocabulary, without ever overwriting user files."""
    data_dir = Path(data_dir).expanduser()
    project_root = Path(project_root) if project_root is not None else PROJECT_ROOT
    source = project_root / "cards.txt"
    target = data_dir / "cards.txt"
    if data_dir.is_symlink():
        raise RuntimeError(f"Data directory may not be a symlink: {data_dir}")
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target.is_symlink():
        raise RuntimeError(f"Vocabulary may not be a symlink: {target}")
    if target.exists():
        if not target.is_file():
            raise RuntimeError(f"Vocabulary is not a regular file: {target}")
        return False
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(
            f"No personal cards.txt exists at {target}, and no starter cards.txt "
            f"was found in {project_root}. Supply a vocabulary file to continue."
        )
    # Exclusive creation prevents accidentally replacing existing vocabulary.
    try:
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
    except FileExistsError:
        # Another invocation created the vocabulary concurrently: keep it.
        if target.is_symlink() or not target.is_file():
            raise RuntimeError(f"Vocabulary is not a regular file: {target}")
        return False
    print(f"Initialized private vocabulary: {target}")
    return True


def main():
    os.umask(0o077)
    data_dir = Path(os.environ.get("FLASH_CARDS_DATA_DIR") or default_data_dir()).expanduser()
    backups_dir = Path(os.environ.get("FLASH_CARDS_BACKUP_DIR") or default_backups_dir()).expanduser()
    try:
        prepare_data(data_dir)
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f"STOP: Cannot prepare Flashcards data: {exc}") from exc
    os.environ["FLASH_CARDS_DATA_DIR"] = str(data_dir)

    # Backup is deliberately best-effort, matching the existing Desktop launcher.
    # Never risk losing access to the application because of a backup failure.
    try:
        archive = create_backup(data_dir, backups_dir)
        print(f"Verified data backup: {archive}")
    except (BackupError, OSError, sqlite3.Error) as exc:
        print(f"WARNING: Backup failed; opening Flashcards anyway: {exc}", file=sys.stderr)

    os.chdir(PROJECT_ROOT)
    from tk_gui import GUI  # Delayed until data location is configured.
    GUI().run()


if __name__ == "__main__":
    main()
