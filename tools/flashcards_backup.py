#!/usr/bin/env python3
"""Private, consistent Flashcards v1.1 backups (Python standard library only).

Backs up vocabulary, optional priority list and a transactionally consistent
snapshot of the SQLite review database. Never writes to the source files.
Restore deliberately not automated to prevent accidentally replacing progress.
"""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import shutil
import sqlite3
import stat
import tempfile
from urllib.parse import quote
import zipfile

def _default_parent():
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


DEFAULT_DATA = Path(os.environ.get("FLASH_CARDS_DATA_DIR") or
                    _default_parent() / "Flashcards-v1.1").expanduser()
DEFAULT_BACKUPS = Path(os.environ.get("FLASH_CARDS_BACKUP_DIR") or
                       _default_parent() / "Flashcards-v1.1-backups").expanduser()
BACKUP_PREFIX = "flashcards-backup-"
FILE_NAMES = ("cards.txt", "priority_cards.txt", "flashcards.db", "study_goals.json", "review_settings.json")


class BackupError(Exception):
    pass


def _regular_file(path):
    if path.is_symlink() or not path.is_file():
        raise BackupError("Expected a regular file (no symlinks): " + str(path))


def _sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def _snapshot_sqlite(source, destination):
    # SQLite's backup API takes a transactionally consistent snapshot even when
    # another connection is writing. This is safer than copying a live .db.
    uri = "file:" + quote(str(source.resolve()), safe="/") + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=15)) as live:
        with closing(sqlite3.connect(str(destination), timeout=15)) as copied:
            live.backup(copied)
            result = copied.execute("PRAGMA quick_check").fetchone()[0]
            if result != "ok":
                raise BackupError("SQLite snapshot failed integrity check: " + str(result))


def _add_content(archive, filename, data, manifest):
    archive.writestr(filename, data)
    manifest["files"][filename] = {"bytes": len(data), "sha256": _sha256(data)}


def _validate_archive(path):
    _regular_file(path)
    try:
        with zipfile.ZipFile(path, "r") as archive:
            files = archive.namelist()
            if len(files) != len(set(files)) or "manifest.json" not in files:
                raise BackupError("Invalid archive: missing manifest or duplicate filenames")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            if manifest.get("format") != "flashcards-backup-v1" or not isinstance(manifest.get("files"), dict):
                raise BackupError("Invalid archive manifest format")
            expected = set(manifest["files"]) | {"manifest.json"}
            if set(files) != expected or "cards.txt" not in manifest["files"]:
                raise BackupError("Invalid archive contents")
            if not set(manifest["files"]).issubset(FILE_NAMES):
                raise BackupError("Unexpected archive member")
            for filename, detail in manifest["files"].items():
                raw = archive.read(filename)
                if len(raw) != detail["bytes"] or _sha256(raw) != detail["sha256"]:
                    raise BackupError("Corrupted backup member: " + filename)
            return manifest
    except (zipfile.BadZipFile, KeyError, UnicodeError, ValueError, TypeError, OSError) as exc:
        raise BackupError("Backup verification failed: " + str(exc)) from exc


def create_backup(data_dir=DEFAULT_DATA, backups_dir=DEFAULT_BACKUPS):
    data_dir, backups_dir = Path(data_dir).expanduser(), Path(backups_dir).expanduser()
    if data_dir.resolve() == backups_dir.resolve() or data_dir.resolve() in backups_dir.resolve().parents:
        raise BackupError("Backup destination must be separate from the source data directory")
    cards = data_dir / "cards.txt"
    _regular_file(cards)
    backups_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    if backups_dir.is_symlink():
        raise BackupError("Backup directory may not be a symbolic link")
    name = BACKUP_PREFIX + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f") + "-" + secrets.token_hex(3) + ".zip"
    final = backups_dir / name
    temp_archive = None
    with tempfile.TemporaryDirectory(prefix=".flashcards-snapshot-", dir=backups_dir) as work:
        stage = Path(work)
        try:
            with tempfile.NamedTemporaryFile(dir=backups_dir, prefix=".flashcards-", suffix=".tmp", delete=False) as out:
                temp_archive = Path(out.name)
            temp_archive.chmod(0o600)
            manifest = {"format": "flashcards-backup-v1", "created_at_utc": datetime.now(timezone.utc).isoformat(), "files": {}}
            with zipfile.ZipFile(temp_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for filename in ("cards.txt", "priority_cards.txt", "study_goals.json", "review_settings.json"):
                    source = data_dir / filename
                    if source.exists() or source.is_symlink():
                        _regular_file(source)
                        _add_content(archive, filename, source.read_bytes(), manifest)
                database = data_dir / "flashcards.db"
                if database.exists() or database.is_symlink():
                    _regular_file(database)
                    db_snapshot = stage / "flashcards.db"
                    _snapshot_sqlite(database, db_snapshot)
                    _add_content(archive, "flashcards.db", db_snapshot.read_bytes(), manifest)
                archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True, indent=2))
            _validate_archive(temp_archive)
            os.replace(str(temp_archive), str(final))
            temp_archive = None
        finally:
            if temp_archive is not None:
                temp_archive.unlink(missing_ok=True)
    return final


def verify_latest(backups_dir=DEFAULT_BACKUPS):
    directory = Path(backups_dir).expanduser()
    if not directory.is_dir():
        raise BackupError("No backup directory exists")
    candidates = sorted(directory.glob(BACKUP_PREFIX + "*.zip"))
    if not candidates:
        raise BackupError("No Flashcards backups found")
    latest = candidates[-1]
    manifest = _validate_archive(latest)
    return latest, manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Safe private Flashcards backups")
    parser.add_argument("command", choices=("snapshot", "verify-latest"))
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--backups-dir", type=Path, default=DEFAULT_BACKUPS)
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        if args.command == "snapshot":
            latest = create_backup(args.data_dir, args.backups_dir)
            print("SUCCESS: Created and verified backup")
            print("Backup:", latest)
        else:
            latest, manifest = verify_latest(args.backups_dir)
            print("SUCCESS: Latest backup passes checksum validation")
            print("Backup:", latest)
            print("Included:", ", ".join(sorted(manifest["files"])))
    except (BackupError, OSError, sqlite3.Error) as exc:
        parser.exit(1, "STOP: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
