import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import constants


class Phase1ConfigurationTests(unittest.TestCase):
    def test_default_path_points_to_cards_txt(self):
        self.assertEqual(Path(constants.CARD_PATH).name, "cards.txt")
        self.assertEqual(Path(constants.AUDIO_PATH).name, "audio")

    def test_environment_override_in_fresh_process(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, FLASH_CARDS_DATA_DIR=directory)
            result = subprocess.check_output(
                [sys.executable, "-c", "import constants; print(constants.CARD_PATH)"],
                cwd=Path(__file__).resolve().parents[1],
                env=env,
                text=True,
            ).strip()
            self.assertEqual(Path(result), Path(directory) / "cards.txt")

    def test_credentials_are_from_environment(self):
        self.assertEqual(constants.PLAYHT_USER_ID, os.getenv("PLAYHT_USER_ID", ""))
        self.assertEqual(constants.PLAYHT_API_KEY, os.getenv("PLAYHT_API_KEY", ""))


if __name__ == "__main__":
    unittest.main()
