import constants

class Card:

   def __init__(self, front, back, card_id):
      self.id = card_id
      self.english = front
      self.chinese = back
      self.pinyin = ""
      self.hanzi = ""
      self.setPinyinHanZi()
      self.checkPriority()
      # self.checkCategories()

      # TODO
      # self.categories = []  [.., .., ..]
      # self.priority = False  (p)
      # self.mp3_location = ""  {.....}


   def setPinyinHanZi(self):
      hanzi = ""
      pinyin = ""
      for val in self.chinese.split("/"):
         val = val.strip()
         for char in val:
            if ord(char) >= 19968 and ord(char) <= 40959:
               hanzi = hanzi + char
            else:
               pinyin = pinyin + char

         self.hanzi = self.hanzi + hanzi.strip() + " "
         self.pinyin = self.pinyin + pinyin.strip() + " "

      print("-- setPinyinHanZi --\nhanzi={}\npinyin={}".format(self.hanzi, self.pinyin))


   def checkPriority(self):
      with open(constants.PRIORITY_CARD_DICT_PATH, 'r')\
       as priority_cards:
       for line in priority_cards:
         if self.english in line:
            self.priority = True
            return

      self.priority = False


   def getEnglish(self):
      return self.english

   def getChinese(self):
      return self.chinese

   def getPinyin(self):
      return self.pinyin

   def getHanZi(self):
      return self.hanzi

   # TODO
   # def getCategories(self):
   #    return self.categories

   def getID(self):
      return self.id

   def isPriority(self):
      return self.priority
