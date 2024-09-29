import random
import constants
from card import Card

class Deck:

   def __init__(self, cards):
      self._cards = cards
      self._num_cards = len(cards)
      self._cards_dict = {}
      self._priority_cards = []
      self._recent_cards = []
      self.set_categories()

      for card in cards:         
         if card.priority:
            self._priority_cards.append(card)

         if self._num_cards <= constants.RECENT_CARDS_AMOUNT:
            if card.id >= self._num_cards - int(0.1 * self._num_cards):
               self._recent_cards.append(card)
         else:
            if card.id >= self._num_cards - constants.RECENT_CARDS_AMOUNT:
               self._recent_cards.append(card)

         self._cards_dict[card.english] = card

      self._num_priority_cards = len(self._priority_cards)


   def shuffle(self):
      shuffled_cards = []
      already_rolled = []
      while len(shuffled_cards) < self._num_cards:
         index = random.randint(0, self._num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self._cards[index])
            already_rolled.append(index)

      self._cards = shuffled_cards


   def shuffle_priority(self):
      shuffled_cards = []
      already_rolled = []
      num_cards = len(self.priority_cards)
      while len(shuffled_cards) < num_cards:
         index = random.randint(0, num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self._priority_cards[index])
            already_rolled.append(index)

      self._priority_cards = shuffled_cards


   def shuffle_recent(self):
      shuffled_cards = []
      already_rolled = []
      num_cards = len(self._recent_cards)
      while len(shuffled_cards) < num_cards:
         index = random.randint(0, num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self._recent_cards[index])
            already_rolled.append(index)

      self._recent_cards = shuffled_cards


   def shuffle_all(self):
      self.shuffle()
      self.shuffle_priority()
      self.shuffle_recent()


   def set_categories(self):
      self._categories = { constants.CATEGORY_ALL : True }
      for card in self._cards:
         for tag in card.tags:
            if tag not in self._categories:
               self._categories[tag] = False
               
      print("set categories={}".format(self._categories))


   @property
   def cards(self):
      return self._cards

   @property
   def cards_dict(self):
      return self._cards_dict

   @property
   def priority_cards(self):
      return self._priority_cards

   @property
   def recent_cards(self):
      return self._recent_cards

   @property
   def number_of_cards(self):
      return self._num_cards

   @property
   def number_of_priority_cards(self):
      return self._num_priority_cards

   @property
   def categories(self):
      return self._categories