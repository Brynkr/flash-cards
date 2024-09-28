import constants

class Card:

   def __init__(self, front, back, tags, card_id):
      self.id = card_id

      self.tags = []
      for tag in tags:
         if tag != constants.CARD_PRIORITY_TAG:
            self.tags.append(tag)

      self.priority = constants.CARD_PRIORITY_TAG in tags
      self.english = front
      self.chinese = back
      self.pinyin = ""
      self.hanzi = ""
      self.set_pinyin_hanzi()
      # TODO - self.mp3_location = ""  {.....}


   def set_pinyin_hanzi(self):
      hanzi = ""
      pinyin = ""
      for val in self.chinese.split(constants.WORD_DELIMITER):
         val = val.strip()
         for char in val:
            if ord(char) >= constants.UNICODE_CHINESE_LOWER_LIMIT\
                 and ord(char) <= constants.UNICODE_CHINESE_UPPER_LIMIT:
               hanzi = hanzi + char
            else:
               pinyin = pinyin + char

         self.hanzi = self.hanzi + hanzi.strip() + " "
         self.pinyin = self.pinyin + pinyin.strip() + " "

      print("-- set_pinyin_hanzi --\nhanzi={}\npinyin={}".format(self.hanzi, self.pinyin))


   def get_english(self):
      return self.english

   def get_chinese(self):
      return self.chinese

   def get_pinyin(self):
      return self.pinyin

   def get_hanzi(self):
      return self.hanzi

   def get_tags(self):
      return self.tags

   def get_id(self):
      return self.id

   def is_priority(self):
      return self.priority
