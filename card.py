import itertools
import constants
from study_core.legacy_chinese import extract_hanzi_answers, extract_pinyin_answers

class Card:
   id_iter = itertools.count()

   def __init__(self, front, back, tags):
      self._id = next(self.id_iter)

      self._tags = []
      for tag in tags:
         if tag != constants.CARD_PRIORITY_TAG:
            self._tags.append(tag)

      self._priority = constants.CARD_PRIORITY_TAG in tags
      self._english = front
      self._chinese = back
      self._pinyin = ""
      self._hanzi = ""
      self.set_pinyin_hanzi()


   def set_pinyin_hanzi(self):
      """Parse each explicitly separated pronunciation as one alternative.

      Keep the original field for display and future data migration. Running
      this method more than once must never duplicate an answer.
      """
      delimiter = constants.WORD_DELIMITER
      self._hanzi_options = tuple(extract_hanzi_answers(self._chinese, delimiter))
      self._pinyin_options = tuple(extract_pinyin_answers(self._chinese, delimiter))
      separator = f" {delimiter.strip()} "
      self._hanzi = separator.join(self._hanzi_options)
      self._pinyin = separator.join(self._pinyin_options)

   @property
   def hanzi_options(self):
      return self._hanzi_options

   @property
   def pinyin_options(self):
      return self._pinyin_options


   @property
   def english(self):
      return self._english

   @property
   def chinese(self):
      return self._chinese

   @property
   def pinyin(self):
      return self._pinyin

   @property
   def hanzi(self):
      return self._hanzi

   @property
   def tags(self):
      return self._tags

   @property
   def id(self):
      return self._id

   @property
   def priority(self):
      return self._priority
