# Flashcards v1.1

A local Tkinter vocabulary-study application with scheduled review, priority study,
a study-progress dashboard, daily goals, and customizable appearance.

## Starting the application

Use **Python 3 with Tkinter** and install any dependencies required by the
application's existing audio features. From the repository directory:

```sh
python3 launch_flashcards.py
```

On macOS, you can also use `launch-flashcards.command` from the repository
(directory-relative; no username or absolute clone path is hard-coded). If your
Tkinter-enabled Python is not on `PATH`, run:

```sh
FLASHCARDS_PYTHON="$HOME/.local/bin/python3" ./launch-flashcards.command
```

The command script uses `~/.local/bin/python3` automatically when available,
otherwise `python3` on `PATH`. It does **not** install packages, create a
Desktop shortcut, or replace a pre-existing launcher.

## Private vocabulary and study history

By default on macOS the program stores personal data here:

- `~/Library/Application Support/Flashcards-v1.1/cards.txt`
- `~/Library/Application Support/Flashcards-v1.1/priority_cards.txt`
- `~/Library/Application Support/Flashcards-v1.1/flashcards.db`
- `~/Library/Application Support/Flashcards-v1.1/study_goals.json`

The first run copies the repository's `cards.txt` **only when a private
`cards.txt` does not already exist**. Existing data is never overwritten or
migrated. If the repository has no starter `cards.txt`, supply your own in the
private data directory before launching.

Set `FLASH_CARDS_DATA_DIR` to use another private data directory. For example:

```sh
FLASH_CARDS_DATA_DIR="$HOME/my-flashcards" python3 launch_flashcards.py
```

On other systems, the default is under `XDG_DATA_HOME` or `~/.local/share`.

## Automatic, validated backups

Each launch attempts to create a checksum-validated ZIP backup before opening
the GUI. The backup includes available data from `cards.txt`,
`priority_cards.txt`, `flashcards.db`, and `study_goals.json`. SQLite is copied
using its backup API for a consistent snapshot. Missing optional data files are
fine, and backup failure produces a warning without blocking the application.

On macOS, ZIPs default to:
`~/Library/Application Support/Flashcards-v1.1-backups/`

Set `FLASH_CARDS_BACKUP_DIR` to customize the archive destination.

You can manually create and verify a backup with the bundled utility:

```sh
python3 -m tools.flashcards_backup snapshot
python3 -m tools.flashcards_backup verify-latest
```

For a custom data path, specify the paths explicitly:

```sh
python3 -m tools.flashcards_backup snapshot \
  --data-dir "$HOME/my-flashcards" --backups-dir "$HOME/my-flashcards-backups"
python3 -m tools.flashcards_backup verify-latest \
  --backups-dir "$HOME/my-flashcards-backups"
```

Verification checks archive manifests and SHA-256 checksums. Restoring a backup
is intentionally **not automatic**, to avoid overwriting newer study progress.
Keep separate copies of important data as well.

## Development / verification

```sh
python3 -m unittest discover -s tests -q
```

The application has been exercised on macOS. Packaging and dependencies on a
completely fresh computer should still be tested before distributing broadly.
