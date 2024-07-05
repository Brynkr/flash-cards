import random
import constants

class CardHandler:

   def __init__(self,
                card_dir=constants.CARD_DICT_PATH,
                priority_card_dir=constants.PRIORITY_CARD_DICT_PATH):
      self.card_dir = card_dir
      self.priority_card_dir = priority_card_dir
      self.cards = self.retrieveCards(self.card_dir)
      self.priority_cards = self.retrieveCards(self.priority_card_dir)
      self.num_cards = len(self.cards)
      self.num_priority_cards = len(self.priority_cards)

      self.shuffleCards()
      self.shufflePriorityCards()


   def getCards(self):
      return self.cards


   def getPriorityCards(self):
      return self.priority_cards


   def addCards(self, card):
      with open(self.card_dir, 'a') as file:
         print("writing card: {}".format(card))
         file.write(card)
      return


   def retrieveCards(self, card_dir):
      card_dict = {}
      with open(card_dir, 'r') as cards:
         for line in cards:
            print("Line = {}".format(line))
            if line.strip() != "" and line[0] != "#":
               split_line = line.split(":")
               card_dict[split_line[0].strip(":").strip()] = split_line[1].strip(":").strip()
      return card_dict


   def shuffleCards(self):
      keys = list(self.cards.keys())
      shuffled_cards = [(key, self.cards[key]) for key in keys]
      random.shuffle(shuffled_cards)
      self.cards = dict(shuffled_cards)


   def shuffleSpecifiedCards(self, cards):
      keys = list(cards.keys())
      shuffled_cards = [(key, cards[key]) for key in keys]
      random.shuffle(shuffled_cards)
      return dict(shuffled_cards)


   def shufflePriorityCards(self):
      keys = list(self.priority_cards.keys())
      shuffled_cards = [(key, self.priority_cards[key]) for key in keys]
      random.shuffle(shuffled_cards)
      self.priority_cards = dict(shuffled_cards)


   def getRecent(self, card_amount):
      card_dict = {}
      with open(self.card_dir, 'r') as cards:
         card_list = list(cards)
         if len(card_list) >= card_amount:
            index = int(-card_amount)
         else:
            index = len(card_list)

         for line in card_list[index:]:
            if line.strip() != "" and line[0] != "#":
               split_line = line.split(":")
               card_dict[split_line[0].strip(":").strip()] = split_line[1].strip(":").strip()

      return self.shuffleSpecifiedCards(card_dict)


   def addPriorityCard(self, side_one, side_two):
      with open(self.priority_card_dir, 'r') as cards:
         for line in cards:
            line_list = line.split(':')
            if line_list[0].strip() == side_one and line_list[1].strip() == side_two:
               print("Priority card already exists, skipping.\n")
               return
      with open(self.priority_card_dir, 'a') as file:
         file.write("\n{0} : {1}".format(side_one, side_two))
         print("Added priority card.\n")


   def correctAnswer(self, value, input_val):
      print("value={}\ninput_val={}".format(value, input_val))
      answer = ""
      value_ary = value.split("/")
      for val in value_ary:
         val = val.strip()
         word_len = len(val.split(" "))
         if word_len == 2:
            answer = val[-1:]
         elif word_len == 3:
            answer = val[-2:]
         elif word_len == 4:
            answer = val[-3:]
         answer = answer.strip()
         print("Answer==input_val: {}".format(bool(answer == input_val)))
         print("Answer={}".format(answer))
         if answer == input_val:
            return True
      return False


   def getHanZi(self, value):
      answers = ""
      value_ary = value.split("/")
      for val in value_ary:
         val = val.strip()
         word_len = len(val.split(" "))
         if word_len == 2:
            answer = val[-1:]
         elif word_len == 3:
            answer = val[-2:]
         elif word_len == 4:
            answer = val[-3:]
         if answer != None:
            answers = answers + answer.strip()
      return answers

