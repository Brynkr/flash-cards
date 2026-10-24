"""Repository packaging and backup safety; no writes to a real user profile."""
from contextlib import closing
import hashlib
import io
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import zipfile

import launch_flashcards as launch
from tools import flashcards_backup as backup


class ReleasePackagingTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "cards.txt").write_bytes(b"Example: \xe4\xbe\x8b\xe5\xad\x90\n")
        self.data = self.root / "data"
        self.backups = self.root / "backups"

    def test_initial_setup_copies_public_starter_only_once(self):
        self.assertTrue(launch.prepare_data(self.data, self.project))
        self.assertEqual((self.data / "cards.txt").read_bytes(),
                         (self.project / "cards.txt").read_bytes())
        (self.data / "cards.txt").write_text("MY VOCABULARY\n")
        self.assertFalse(launch.prepare_data(self.data, self.project))
        self.assertEqual((self.data / "cards.txt").read_text(), "MY VOCABULARY\n")

    def test_existing_database_and_settings_are_untouched(self):
        self.data.mkdir()
        (self.data / "cards.txt").write_text("Original")
        (self.data / "flashcards.db").write_bytes(b"database-marker")
        (self.data / "study_goals.json").write_text('{"daily_goal": 23}')
        self.assertFalse(launch.prepare_data(self.data, self.project))
        self.assertEqual((self.data / "flashcards.db").read_bytes(), b"database-marker")
        self.assertEqual((self.data / "study_goals.json").read_text(), '{"daily_goal": 23}')

    def test_missing_cards_and_starter_refuses_to_start(self):
        (self.project / "cards.txt").unlink()
        with self.assertRaises(FileNotFoundError):
            launch.prepare_data(self.data, self.project)

    def test_symbolic_vocabulary_is_refused(self):
        self.data.mkdir()
        (self.data / "cards.txt").symlink_to(self.project / "cards.txt")
        with self.assertRaises(RuntimeError):
            launch.prepare_data(self.data, self.project)

    def test_symbolic_data_dir_is_refused(self):
        self.data.symlink_to(self.project, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            launch.prepare_data(self.data, self.project)

    def test_backup_includes_all_four_data_files(self):
        launch.prepare_data(self.data, self.project)
        (self.data / "priority_cards.txt").write_text("Example\n")
        (self.data / "study_goals.json").write_text('{"daily_goal": 11}')
        db = self.data / "flashcards.db"
        with closing(sqlite3.connect(db)) as conn:
            conn.execute("CREATE TABLE reviews (score INTEGER)")
            conn.execute("INSERT INTO reviews VALUES (1)")
            conn.commit()
        archive = backup.create_backup(self.data, self.backups)
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(set(z.namelist()), {
                "cards.txt", "priority_cards.txt", "flashcards.db", "study_goals.json", "manifest.json"})
            self.assertEqual(z.read("study_goals.json"), b'{"daily_goal": 11}')
            db_snapshot = self.root / "snapshot.db"
            db_snapshot.write_bytes(z.read("flashcards.db"))
        with closing(sqlite3.connect(db_snapshot)) as conn:
            self.assertEqual(conn.execute("SELECT score FROM reviews").fetchone(), (1,))
        self.assertEqual(backup.verify_latest(self.backups)[0], archive)

    def test_optional_data_can_be_missing(self):
        launch.prepare_data(self.data, self.project)
        path = backup.create_backup(self.data, self.backups)
        with zipfile.ZipFile(path) as z:
            self.assertEqual(set(z.namelist()), {"cards.txt", "manifest.json"})
        self.assertEqual(set(backup.verify_latest(self.backups)[1]["files"]), {"cards.txt"})

    def test_invalid_zip_checksum_is_rejected(self):
        launch.prepare_data(self.data, self.project)
        path = backup.create_backup(self.data, self.backups)
        with zipfile.ZipFile(path, "r") as z:
            manifest = z.read("manifest.json")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("cards.txt", b"INTRUDER")
            z.writestr("manifest.json", manifest)
        with self.assertRaises(backup.BackupError):
            backup.verify_latest(self.backups)

    def test_old_archive_remains_accepted(self):
        launch.prepare_data(self.data, self.project)
        old = backup.create_backup(self.data, self.backups)
        (self.data / "study_goals.json").write_text('{"daily_goal": 7}')
        new = backup.create_backup(self.data, self.backups)
        self.assertEqual(set(backup._validate_archive(old)["files"]), {"cards.txt"})
        self.assertIn("study_goals.json", backup._validate_archive(new)["files"])

    def test_sqlite_wal_backups_include_committed_rows(self):
        launch.prepare_data(self.data, self.project)
        db = self.data / "flashcards.db"
        conn = sqlite3.connect(db)
        self.addCleanup(conn.close)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE reviews (score INTEGER)")
        conn.execute("INSERT INTO reviews VALUES (17)")
        conn.commit()
        archive = backup.create_backup(self.data, self.backups)
        with zipfile.ZipFile(archive) as z:
            snapshot = self.root / "wal-copy.db"
            snapshot.write_bytes(z.read("flashcards.db"))
        with closing(sqlite3.connect(snapshot)) as restored:
            self.assertEqual(restored.execute("SELECT score FROM reviews").fetchone(), (17,))

    def test_cli_snapshot_and_verify_custom_directories(self):
        launch.prepare_data(self.data, self.project)
        script = Path(backup.__file__).resolve()
        for action in ("snapshot", "verify-latest"):
            result = subprocess.run(
                [sys.executable, str(script), action, "--data-dir", str(self.data),
                 "--backups-dir", str(self.backups)], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("SUCCESS:", result.stdout)

    def test_launcher_opens_gui_after_verified_backup(self):
        seen = []
        fake_gui = types.SimpleNamespace(GUI=lambda: types.SimpleNamespace(run=lambda: seen.append('open')))
        environment = {"FLASH_CARDS_DATA_DIR": str(self.data),
                       "FLASH_CARDS_BACKUP_DIR": str(self.backups)}
        with (mock.patch.dict(os.environ, environment),
              mock.patch.dict(sys.modules, {"tk_gui": fake_gui}),
              mock.patch.object(launch, "PROJECT_ROOT", self.project),
              mock.patch.object(launch.os, "chdir"),
              mock.patch.object(launch.os, "umask")):
            launch.main()
        self.assertEqual(seen, ['open'])
        self.assertTrue(list(self.backups.glob('flashcards-backup-*.zip')))

    def test_failed_backup_warns_but_still_opens_gui(self):
        seen = []
        fake_gui = types.SimpleNamespace(GUI=lambda: types.SimpleNamespace(run=lambda: seen.append('open')))
        environment = {"FLASH_CARDS_DATA_DIR": str(self.data),
                       "FLASH_CARDS_BACKUP_DIR": str(self.backups)}
        warning = io.StringIO()
        with (mock.patch.dict(os.environ, environment),
              mock.patch.dict(sys.modules, {"tk_gui": fake_gui}),
              mock.patch.object(launch, "PROJECT_ROOT", self.project),
              mock.patch.object(launch, "create_backup", side_effect=backup.BackupError("disk full")),
              mock.patch.object(launch.os, "chdir"),
              mock.patch.object(launch.os, "umask"),
              mock.patch("sys.stderr", warning)):
            launch.main()
        self.assertEqual(seen, ['open'])
        self.assertIn('Backup failed', warning.getvalue())

    def test_command_launcher_is_valid_shell(self):
        script = Path(launch.__file__).parent / "launch-flashcards.command"
        if not script.is_file():
            self.skipTest("Shell launcher unavailable in isolated module fixture")
        check = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_bundle_has_no_absolute_developer_directory(self):
        script = Path(launch.__file__).parent / "launch-flashcards.command"
        if not script.is_file():
            self.skipTest("Shell launcher unavailable in isolated module fixture")
        content = script.read_text()
        self.assertNotIn('/Users/bryn', content)
        self.assertIn('"$ROOT/launch_flashcards.py"', content)


if __name__ == "__main__":
    unittest.main()
