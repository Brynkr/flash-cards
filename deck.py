import random
import constants
from card import Card

class Deck:

   def __init__(self, cards):
      self.cards = cards
      self.num_cards = len(cards)
      self.cards_dict = {}
      self.priority_cards = []
      self.recent_cards = []
      self.set_categories()

      for card in cards:         
         if card.is_priority():
            self.priority_cards.append(card)

         if self.num_cards <= constants.RECENT_CARDS_AMOUNT:
            if card.get_id() >= self.num_cards - int(0.1 * self.num_cards):
               self.recent_cards.append(card)
         else:
            if card.get_id() >= self.num_cards - constants.RECENT_CARDS_AMOUNT:
               self.recent_cards.append(card)

         self.cards_dict[card.get_english()] = card

      self.num_priority_cards = len(self.priority_cards)


   def shuffle(self):
      shuffled_cards = []
      already_rolled = []
      while len(shuffled_cards) < self.num_cards:
         index = random.randint(0, self.num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self.cards[index])
            already_rolled.append(index)

      self.cards = shuffled_cards


   def shuffle_priority(self):
      shuffled_cards = []
      already_rolled = []
      num_cards = len(self.priority_cards)
      while len(shuffled_cards) < num_cards:
         index = random.randint(0, num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self.priority_cards[index])
            already_rolled.append(index)

      self.priority_cards = shuffled_cards


   def shuffle_recent(self):
      shuffled_cards = []
      already_rolled = []
      num_cards = len(self.recent_cards)
      while len(shuffled_cards) < num_cards:
         index = random.randint(0, num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self.recent_cards[index])
            already_rolled.append(index)

      self.recent_cards = shuffled_cards


   def shuffle_all(self):
      self.shuffle()
      self.shuffle_priority()
      self.shuffle_recent()


   def set_categories(self):
      self.categories = { constants.CATEGORY_ALL : True }
      for card in self.cards:
         for tag in card.get_tags():
            if tag not in self.categories:
               self.categories[tag] = False
               
      print("set categories={}".format(self.categories))


   def get_cards(self):
      return self.cards

   def get_cards_dict(self):
      return self.cards_dict

   def get_priority_cards(self):
      return self.priority_cards

   def get_recent_cards(self):
      return self.recent_cards

   def get_number_of_cards(self):
      return self.num_cards

   def get_number_of_priority_cards(self):
      return self.num_priority_cards

   def get_categories(self):
      return self.categories