"""Regression tests for the GUI-independent answer checker."""

import unittest

from study_core.answers import answer_matches, normalize_answer


class AnswerCheckerTests(unittest.TestCase):
    def test_english_case_spacing_and_punctuation(self):
        self.assertTrue(answer_matches("  HELLO   there! ", ["Hello there"], "en"))

    def test_english_missing_article_not_accepted(self):
        self.assertFalse(answer_matches("want water", ["I want water"], "en"))

    def test_english_word_order_matters(self):
        self.assertFalse(answer_matches("drink water I", ["I drink water"], "en"))

    def test_apostrophe_variants(self):
        self.assertTrue(answer_matches("I’m here", ["I'm here"], "en"))

    def test_explicit_synonyms(self):
        self.assertTrue(answer_matches("hi", ["hello", "hi"], "en"))
        self.assertFalse(answer_matches("hey", ["hello", "hi"], "en"))

    def test_chinese_spaces_and_punctuation(self):
        self.assertTrue(answer_matches("我 想 喝 水。", ["我想喝水"], "zh"))

    def test_chinese_fullwidth_normalization(self):
        self.assertTrue(answer_matches("你好！", ["你好"], "zh"))

    def test_chinese_character_differences_not_ignored(self):
        self.assertFalse(answer_matches("喝茶", ["喝水"], "zh"))

    def test_pinyin_tone_marks_remain_significant(self):
        self.assertFalse(answer_matches("ma", ["mǎ"], "pinyin"))
        self.assertFalse(answer_matches("mà", ["mǎ"], "pinyin"))
        self.assertTrue(answer_matches("WǑ", ["wǒ"], "pinyin"))

    def test_no_unintended_pinyin_number_conversion(self):
        self.assertFalse(answer_matches("ma3", ["mǎ"], "pinyin"))

    def test_reject_empty_reference_answers(self):
        with self.assertRaises(ValueError):
            answer_matches("anything", ["", "   "], "en")

    def test_reject_single_string_as_alternatives(self):
        with self.assertRaises(TypeError):
            answer_matches("hello", "hello|hi", "en")

    def test_reject_blank_response(self):
        self.assertFalse(answer_matches(" ... ", ["hello"], "en"))

    def test_unicode_whitespace(self):
        self.assertEqual(normalize_answer("a\u00a0\u00a0b", "en"), "a b")

    def test_invalid_language(self):
        with self.assertRaises(ValueError):
            normalize_answer("hello", "xx")


if __name__ == "__main__":
    unittest.main()
