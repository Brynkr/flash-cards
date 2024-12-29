import itertools
import constants

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
      hanzi = ""
      pinyin = ""
      for val in self._chinese.split(constants.WORD_DELIMITER):
         val = val.strip()
         for char in val:
            if ord(char) >= constants.UNICODE_CHINESE_LOWER_LIMIT\
                 and ord(char) <= constants.UNICODE_CHINESE_UPPER_LIMIT:
               hanzi = hanzi + char
            else:
               pinyin = pinyin + char

         self._hanzi = self._hanzi + hanzi.strip() + " "
         self._pinyin = self._pinyin + pinyin.strip() + " "

      print("-- set_pinyin_hanzi --\nhanzi={}\npinyin={}".format(self._hanzi, self._pinyin))


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
