"""Regression tests for per-alternative Hanzi and pinyin parsing."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import constants
from card import Card
from deck_handler import DeckHandler
from study_core.legacy_chinese import extract_hanzi_answers, extract_pinyin_answers


def alternatives(*values):
    return f' {constants.WORD_DELIMITER} '.join(values)


class CardParsingTests(unittest.TestCase):
    def test_single_pronunciation(self):
        card = Card('Hello', 'nǐ hǎo 你好', [])
        self.assertEqual(card.hanzi, '你好')
        self.assertEqual(card.pinyin, 'nǐ hǎo')
        self.assertEqual(card.hanzi_options, ('你好',))

    def test_multiple_options_do_not_merge(self):
        card = Card('Can', alternatives('kě yǐ 可以', 'néng 能'), [])
        self.assertEqual(card.hanzi_options, ('可以', '能'))
        self.assertEqual(card.pinyin_options, ('kě yǐ', 'néng'))
        self.assertEqual(card.hanzi, alternatives('可以', '能'))
        self.assertEqual(card.pinyin, alternatives('kě yǐ', 'néng'))

    def test_three_alternatives_keep_distinct_pinyin(self):
        card = Card('Here', alternatives('zhè r 这', 'zhè li 这', 'zhè biān 这边'), [])
        self.assertEqual(card.hanzi_options, ('这', '这边'))
        self.assertEqual(card.pinyin_options, ('zhè r', 'zhè li', 'zhè biān'))

    def test_parser_is_idempotent(self):
        card = Card('Money', alternatives('yuán 元', 'qián 钱'), [])
        before = (card.hanzi, card.pinyin, card.hanzi_options, card.pinyin_options)
        card.set_pinyin_hanzi()
        self.assertEqual(before,
                         (card.hanzi, card.pinyin, card.hanzi_options, card.pinyin_options))

    def test_original_chinese_field_unchanged(self):
        raw = alternatives('zuò fàn 做饭', 'zhǔ fàn 煮饭')
        self.assertEqual(Card('Cook', raw, []).chinese, raw)

    def test_missing_hanzi_does_not_invent_it(self):
        card = Card('Broken', 'pinyin only', [])
        self.assertEqual(card.hanzi_options, ())
        self.assertEqual(card.hanzi, '')
        self.assertEqual(card.pinyin, 'pinyin only')

    def test_legacy_parser_validates_delimiter(self):
        with self.assertRaises(ValueError):
            extract_pinyin_answers('nǐ 你', '')
        self.assertEqual(extract_hanzi_answers('nǐ 你', constants.WORD_DELIMITER), ['你'])

    def test_no_verbose_deck_output_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / 'cards.txt'
            file_path.write_text('Hello : nǐ hǎo 你好\nCan : ' +
                                 alternatives('kě yǐ 可以', 'néng 能') + '\n',
                                 encoding='utf-8')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                handler = DeckHandler(card_dir=str(file_path),
                                      priority_card_dir=str(Path(directory) / 'priority.txt'))
            self.assertEqual(len(handler.cards), 2)
            self.assertEqual(output.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
