import random
import logging
import constants
from card import Card
from deck import Deck
from study_core.answers import answer_matches
from study_core.legacy_chinese import extract_hanzi_answers

logger = logging.getLogger(__name__)


class DeckHandler:

   def __init__(self,
                card_dir=constants.CARD_PATH,
                priority_card_dir=constants.PRIORITY_CARD_PATH):
      self._card_dir = card_dir
      self._priority_card_dir = priority_card_dir

      self._deck = None
      self.build_deck(card_dir)
      self._load_saved_priority_cards()
      self._deck.shuffle_all()


   def shuffle_deck(self):
      self._deck.shuffle_all()

   @property
   def deck(self):
      return self._deck

   @property
   def cards(self):
      return self._deck.cards

   @property
   def cards_dict(self):
      return self._deck.cards_dict

   @property
   def priority_cards(self):
      return self._deck.priority_cards

   @property
   def recent_cards(self):
      return self._deck.recent_cards

   @property
   def categories(self):
      return self._deck.categories


   def add_cards(self, card):
      with open(self._card_dir, 'a') as file:
         print("writing card: {}".format(card))
         file.write(card)
      return


   def build_deck(self, card_dir):
      card_list = []
      with open(card_dir, 'r') as cards:
         for line in cards:
            logger.debug("Building Deck. Line = %s", line.rstrip())
            line = line.strip()
            if line and not line.startswith(constants.COMMENTED_LINE_CHAR):
               split_line = line.split(constants.CARD_SIDE_DELIMITER)
               front = split_line[constants.ENGLISH_INDEX].strip()
               back = split_line[constants.CHINESE_INDEX].strip()
               tags = []

               if len(split_line) > constants.TAG_INDEX:
                  for tag in split_line[constants.TAG_INDEX].strip().split(" "):
                     tags.append(tag.strip("[").strip("]"))

               card_list.append(Card(front, back, tags))

      self._deck = Deck(card_list)


   def _priority_pairs(self, text):
      """Recognize existing selections, including legacy leading blank lines."""
      pairs = set()
      for line in text.splitlines():
         sides = line.split(constants.CARD_SIDE_DELIMITER, 1)
         if len(sides) == 2:
            pairs.add((sides[0].strip(), sides[1].strip()))
      return pairs


   def _include_priorities(self, pairs):
      """Use the actual deck card objects so Priority Study works immediately."""
      for card in self._deck.cards:
         if ((card.english, card.chinese) in pairs and
               card not in self._deck._priority_cards):
            self._deck._priority_cards.append(card)
      self._deck._num_priority_cards = len(self._deck._priority_cards)


   def _load_saved_priority_cards(self):
      """A new installation may have no priority list yet."""
      from pathlib import Path
      path = Path(self._priority_card_dir)
      if path.is_file():
         self._include_priorities(self._priority_pairs(
            path.read_text(encoding='utf-8')
         ))


   def add_priority_card(self, side_one, side_two):
      """Create the list on first use and keep saved/in-memory priorities synced."""
      from pathlib import Path
      path = Path(self._priority_card_dir)
      path.parent.mkdir(parents=True, exist_ok=True)
      pair = (side_one, side_two)
      with path.open('a+', encoding='utf-8') as cards:
         cards.seek(0)
         existing = cards.read()
         if pair in self._priority_pairs(existing):
            print("Priority card already exists, skipping.\n")
         else:
            # Avoid both a leading blank line and joining onto an old last line.
            gap = '\n' if existing and not existing.endswith(('\n', '\r')) else ''
            cards.write(f"{gap}{side_one} {constants.CARD_SIDE_DELIMITER} {side_two}\n")
            print("Added priority card.\n")
      self._include_priorities({pair})


   def correct_answer(self, value, input_val):
      """Check Hanzi against each translation explicitly listed on the card."""
      options = extract_hanzi_answers(value, constants.WORD_DELIMITER)
      return bool(options) and answer_matches(input_val, options, "zh")


   def filter_cards_by_category(self, cards, categories):
      """Compatibility alias used by tk_gui.py study modes."""
      return self.category_card_filter(cards, categories)


   def get_hanzi(self, value):
      cards = self._deck.cards_dict
      return cards[value].hanzi


   def category_card_filter(self, cards, categories):
      logger.debug("card category filter: %s", categories)
      filtered_cards = []
      filtered_card_english = []
      for card in cards:
         card_tags = card.tags
         
         if categories[constants.CATEGORY_ALL]:
            filtered_cards.append(card)
            filtered_card_english.append(card.english)

         elif not card_tags and categories[constants.CATEGORY_NO_TAGS]:
            filtered_cards.append(card)
            filtered_card_english.append(card.english)

         else:
            for tag in card_tags:
               if tag in categories.keys() and categories[tag]:
                  filtered_cards.append(card)
                  filtered_card_english.append(card.english)
                  break

      logger.debug("filtered %d cards", len(filtered_card_english))
      return filtered_cards


