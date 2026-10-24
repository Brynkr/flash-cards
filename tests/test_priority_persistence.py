"""Regression tests for a new or existing personal priority file."""
import tempfile
import unittest
from pathlib import Path
from deck_handler import DeckHandler
import constants


class PriorityPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.cards = self.folder / "cards.txt"
        self.priority = self.folder / "priority_cards.txt"
        self.cards.write_text(
            f"One : yī 一\nTwo : èr 二\nTagged : biāo 标 : [{constants.CARD_PRIORITY_TAG}]\n",
            encoding="utf-8",
        )

    def handler(self):
        return DeckHandler(str(self.cards), str(self.priority))

    def test_missing_file_is_not_created_until_needed(self):
        handler = self.handler()
        self.assertFalse(self.priority.exists())
        self.assertEqual([c.english for c in handler.priority_cards], ["Tagged"])

    def test_mark_creates_file_and_updates_current_deck(self):
        handler = self.handler()
        handler.add_priority_card("One", "yī 一")
        self.assertEqual(self.priority.read_text(encoding="utf-8"), "One : yī 一\n")
        self.assertEqual({c.english for c in handler.priority_cards}, {"One", "Tagged"})
        self.assertEqual(handler.deck.number_of_priority_cards, 2)

    def test_duplicate_mark_does_not_duplicate_file_or_deck(self):
        handler = self.handler()
        handler.add_priority_card("One", "yī 一")
        handler.add_priority_card("One", "yī 一")
        self.assertEqual(self.priority.read_text(encoding="utf-8").count("One :"), 1)
        self.assertEqual(len(handler.priority_cards), 2)

    def test_selection_survives_restart(self):
        first = self.handler()
        first.add_priority_card("Two", "èr 二")
        second = self.handler()
        self.assertEqual({c.english for c in second.priority_cards}, {"Two", "Tagged"})

    def test_old_file_without_final_newline_appends_safely(self):
        self.priority.write_text("\nOne : yī 一", encoding="utf-8")
        handler = self.handler()
        self.assertEqual({c.english for c in handler.priority_cards}, {"One", "Tagged"})
        handler.add_priority_card("Two", "èr 二")
        self.assertTrue(self.priority.read_text(encoding="utf-8").endswith(
            "One : yī 一\nTwo : èr 二\n"
        ))

    def test_legacy_blank_lines_and_unknown_cards_are_ignored(self):
        self.priority.write_text("\nUnknown : ??\nOne : yī 一\nINVALID\n", encoding="utf-8")
        handler = self.handler()
        self.assertEqual({c.english for c in handler.priority_cards}, {"One", "Tagged"})

    def test_tagged_card_is_not_duplicated_if_saved_too(self):
        handler = self.handler()
        handler.add_priority_card("Tagged", "biāo 标")
        self.assertEqual([c.english for c in handler.priority_cards], ["Tagged"])

    def test_vocabulary_is_unchanged(self):
        before = self.cards.read_bytes()
        self.handler().add_priority_card("One", "yī 一")
        self.assertEqual(self.cards.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
