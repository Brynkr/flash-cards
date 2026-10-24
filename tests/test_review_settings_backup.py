"""The new scheduler preference is safely covered by repository backups."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from study_core.review_preferences import save_review_mode
from tools.flashcards_backup import create_backup, verify_latest, _validate_archive


class ReviewSettingsBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / 'data'
        self.data.mkdir()
        (self.data / 'cards.txt').write_text('Example - 例子\n')
        self.backups = Path(self.temp.name) / 'backups'

    def test_new_settings_included_byte_for_byte(self):
        preference = self.data / 'review_settings.json'
        save_review_mode('adaptive', preference)
        original = preference.read_bytes()
        archive = create_backup(self.data, self.backups)
        with zipfile.ZipFile(archive) as z:
            self.assertEqual(z.read('review_settings.json'), original)
        latest, manifest = verify_latest(self.backups)
        self.assertEqual(latest, archive)
        self.assertIn('review_settings.json', manifest['files'])

    def test_old_archive_without_preferences_remains_valid(self):
        old = create_backup(self.data, self.backups)
        self.assertEqual(set(_validate_archive(old)['files']), {'cards.txt'})
        save_review_mode('adaptive', self.data / 'review_settings.json')
        new = create_backup(self.data, self.backups)
        self.assertIn('review_settings.json', _validate_archive(new)['files'])
        self.assertNotIn('review_settings.json', _validate_archive(old)['files'])

    def test_missing_preferences_are_optional(self):
        archive = create_backup(self.data, self.backups)
        self.assertNotIn('review_settings.json', _validate_archive(archive)['files'])


if __name__ == '__main__':
    unittest.main()
