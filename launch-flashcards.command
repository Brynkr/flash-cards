#!/usr/bin/env bash
# Portable macOS/Linux launcher. Does not change any existing Desktop shortcut.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${FLASHCARDS_PYTHON:-}" ]]; then
  PYTHON="$FLASHCARDS_PYTHON"
elif [[ -x "$HOME/.local/bin/python3" ]]; then
  PYTHON="$HOME/.local/bin/python3"
else
  PYTHON="$(command -v python3 || true)"
fi

if [[ -z "$PYTHON" || ! -x "$PYTHON" ]]; then
  echo "STOP: Cannot find Python 3. Set FLASHCARDS_PYTHON to a Python with Tkinter."
  exit 1
fi

cd "$ROOT"
exec "$PYTHON" "$ROOT/launch_flashcards.py"
