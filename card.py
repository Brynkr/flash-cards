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

      # TODO
      # self.categories = []  [.., .., ..]
      # self.priority = False  (p)
      # self.mp3_location = ""  {.....}

   #TODO -- change to unicode check?
   def setPinyinHanZi(self):
      hanzi = None
      pinyin = None
      for val in self.chinese.split("/"):
         val = val.strip()
         word_len = len(val.split(" "))
         if word_len == 2:
            pinyin = val[:-1]
            hanzi = val[-1:]
         elif word_len == 3:
            pinyin = val[:-2]
            hanzi = val[-2:]
         elif word_len == 4:
            pinyin = val[:-3]
            hanzi = val[-3:]

         if hanzi != None:
            self.hanzi = self.hanzi + hanzi.strip() + " "
         if pinyin != None:
            self.pinyin = self.pinyin + pinyin.strip() + " "

      print("-- setPinyinHanZi --\nfull_hanzi={}\nfull_pinyin={}".format(self.hanzi, self.pinyin))


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
