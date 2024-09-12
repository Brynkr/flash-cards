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
      self.setPinyinHanZi()
      # TODO - self.mp3_location = ""  {.....}


   def setPinyinHanZi(self):
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

      print("-- setPinyinHanZi --\nhanzi={}\npinyin={}".format(self.hanzi, self.pinyin))


   def getEnglish(self):
      return self.english

   def getChinese(self):
      return self.chinese

   def getPinyin(self):
      return self.pinyin

   def getHanZi(self):
      return self.hanzi

   def getTags(self):
      return self.tags

   def getID(self):
      return self.id

   def isPriority(self):
      return self.priority
