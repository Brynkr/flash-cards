import random
import constants
from card import Card
from deck import Deck

class DeckHandler:

   def __init__(self,
                card_dir=constants.CARD_DICT_PATH,
                priority_card_dir=constants.PRIORITY_CARD_DICT_PATH):
      self.card_dir = card_dir
      self.priority_card_dir = priority_card_dir

      self.deck = None
      self.buildDeck(card_dir)
      self.deck.shuffleAll()


   def shuffleDeck(self):
      self.deck.shuffleAll()

   def getCards(self):
      return self.deck.getCards()

   def getCardsDict(self):
      return self.deck.getCardsDict()

   def getPriorityCards(self):
      return self.deck.getPriorityCards()

   def getRecentCards(self):
      return self.deck.getRecentCards()


   def addCards(self, card):
      with open(self.card_dir, 'a') as file:
         print("writing card: {}".format(card))
         file.write(card)
      return


   def buildDeck(self, card_dir):
      card_list = []
      card_id = 0
      with open(card_dir, 'r') as cards:
         for line in cards:
            print("\nBuilding Deck. Line = {}".format(line))
            if line.strip() != "" and line[0] != "#":
               split_line = line.split(":")
               front = split_line[0].strip()
               back = split_line[1].strip()
               card_list.append(Card(front, back, card_id))
               card_id = card_id + 1

      self.deck = Deck(card_list)


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
         print("Answer={}".format(answer))
         if answer == input_val:
            return True
      return False


   def getHanZi(self, value):
      cards = self.deck.getCardsDict()
      return cards[value].getHanZi()

