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

   def getCategories(self):
      return self.deck.getCategories()


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
            line = line.strip()
            if line and not line.startswith(constants.COMMENTED_LINE_CHAR):
               split_line = line.split(constants.CARD_SIDE_DELIMITER)
               front = split_line[constants.ENGLISH_INDEX].strip()
               back = split_line[constants.CHINESE_INDEX].strip()
               tags = []

               if len(split_line) > constants.TAG_INDEX:
                  for tag in split_line[constants.TAG_INDEX].strip().split(" "):
                     tags.append(tag.strip("[").strip("]"))

               card_list.append(Card(front, back, tags, card_id))
               card_id = card_id + 1

      self.deck = Deck(card_list)


   def addPriorityCard(self, side_one, side_two):
      with open(self.priority_card_dir, 'r') as cards:
         for line in cards:
            line_list = line.split(constants.CARD_SIDE_DELIMITER)
            if line_list[constants.ENGLISH_INDEX].strip() == side_one\
             and line_list[constants.CHINESE_INDEX].strip() == side_two:
               print("Priority card already exists, skipping.\n")
               return
      with open(self.priority_card_dir, 'a') as file:
         file.write("\n{} {} {}".format(side_one, constants.CARD_SIDE_DELIMITER, side_two))
         print("Added priority card.\n")


   def correctAnswer(self, value, input_val):
      print("value={}\ninput_val={}".format(value, input_val))
      answer = ""
      value_ary = value.split(constants.WORD_DELIMITER)
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


   def categoryCardFilter(self, cards, categories):
      print("card category filter. categories={}".format(categories))
      filtered_cards = []
      filtered_card_english = []
      for card in cards:
         card_tags = card.getTags()
         
         if categories[constants.CATEGORY_ALL] == True:
            filtered_cards.append(card)
            filtered_card_english.append(card.getEnglish())

         elif not card_tags and categories[constants.CATEGORY_NO_TAGS] == True:
            filtered_cards.append(card)
            filtered_card_english.append(card.getEnglish())

         else:
            for tag in card_tags:
               if tag in categories.keys() and categories[tag] == True:
                  filtered_cards.append(card)
                  filtered_card_english.append(card.getEnglish())
                  break

      print("len cards used={} filtered_cards={}".format(len(filtered_card_english), filtered_card_english))
      return filtered_cards


