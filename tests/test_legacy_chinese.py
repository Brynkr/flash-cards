"""Language-study integration: legacy Chinese fields and DeckHandler."""

import unittest

import constants
from deck_handler import DeckHandler
from study_core.legacy_chinese import extract_hanzi_answers


class LegacyChineseTests(unittest.TestCase):
    def test_long_phrases_do_not_depend_on_word_count(self):
        field = "wǒ xiǎng hē shuǐ 我想喝水"
        self.assertEqual(extract_hanzi_answers(field, constants.WORD_DELIMITER), ["我想喝水"])
        self.assertTrue(DeckHandler.correct_answer(None, field, "我想喝水"))
        self.assertTrue(DeckHandler.correct_answer(None, field, "我 想 喝 水。"))
        self.assertFalse(DeckHandler.correct_answer(None, field, "我想喝茶"))

    def test_explicit_alternative_translations(self):
        field = constants.WORD_DELIMITER.join([
            "nǐ hǎo 你好",
            "zài jiàn 再见",
        ])
        self.assertEqual(
            extract_hanzi_answers(field, constants.WORD_DELIMITER),
            ["你好", "再见"],
        )
        self.assertTrue(DeckHandler.correct_answer(None, field, "再见"))
        self.assertTrue(DeckHandler.correct_answer(None, field, "你好"))
        self.assertFalse(DeckHandler.correct_answer(None, field, "晚安"))

    def test_does_not_accept_incomplete_hanzi_or_pinyin(self):
        field = "nǐ hǎo 你好"
        self.assertFalse(DeckHandler.correct_answer(None, field, "你"))
        self.assertFalse(DeckHandler.correct_answer(None, field, "nǐ hǎo"))
        self.assertFalse(DeckHandler.correct_answer(None, field, ""))

    def test_empty_and_non_hanzi_translations_never_match(self):
        field = constants.WORD_DELIMITER.join(["", "nǐ hǎo", "   "])
        self.assertEqual(extract_hanzi_answers(field, constants.WORD_DELIMITER), [])
        self.assertFalse(DeckHandler.correct_answer(None, field, "你好"))
        self.assertFalse(DeckHandler.correct_answer(None, field, ""))

    def test_ignores_duplicate_hanzi_alternatives(self):
        field = constants.WORD_DELIMITER.join(["nǐ 你", "nǐ 你"])
        self.assertEqual(extract_hanzi_answers(field, constants.WORD_DELIMITER), ["你"])

    def test_deckhandler_has_method_used_by_tkinter(self):
        self.assertTrue(callable(DeckHandler.filter_cards_by_category))

    def test_category_filter_forwards_to_existing_implementation(self):
        class FakeHandler:
            calls = []
            def category_card_filter(self, cards, categories):
                self.calls.append((cards, categories))
                return ["filtered"]

        handler = FakeHandler()
        result = DeckHandler.filter_cards_by_category(handler, ["card"], {"All": True})
        self.assertEqual(result, ["filtered"])
        self.assertEqual(handler.calls, [(["card"], {"All": True})])

    def test_no_chinese_character_in_false_pinyin_answer(self):
        field = "shuǐ 水"
        self.assertFalse(DeckHandler.correct_answer(None, field, "shui3"))
        self.assertTrue(DeckHandler.correct_answer(None, field, "水"))


if __name__ == "__main__":
    unittest.main()
