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
      self.setCategories()

      for card in cards:         
         if card.isPriority():
            self.priority_cards.append(card)

         if self.num_cards <= constants.RECENT_CARDS_AMOUNT:
            if card.getID() >= self.num_cards - int(0.1 * self.num_cards):
               self.recent_cards.append(card)
         else:
            if card.getID() >= self.num_cards - constants.RECENT_CARDS_AMOUNT:
               self.recent_cards.append(card)

         self.cards_dict[card.getEnglish()] = card

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


   def shufflePriority(self):
      shuffled_cards = []
      already_rolled = []
      num_cards = len(self.priority_cards)
      while len(shuffled_cards) < num_cards:
         index = random.randint(0, num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self.priority_cards[index])
            already_rolled.append(index)

      self.priority_cards = shuffled_cards


   def shuffleRecent(self):
      shuffled_cards = []
      already_rolled = []
      num_cards = len(self.recent_cards)
      while len(shuffled_cards) < num_cards:
         index = random.randint(0, num_cards - 1)
         if index not in already_rolled:
            shuffled_cards.append(self.recent_cards[index])
            already_rolled.append(index)

      self.recent_cards = shuffled_cards


   def shuffleAll(self):
      self.shuffle()
      self.shufflePriority()
      self.shuffleRecent()


   def setCategories(self):
      self.categories = {constants.CATEGORY_ALL : True}
      for card in self.cards:
         for tag in card.getTags():
            if tag not in self.categories:
               self.categories[tag] = False

      print("set categories={}".format(self.categories))


   def getCards(self):
      return self.cards

   def getCardsDict(self):
      return self.cards_dict

   def getPriorityCards(self):
      return self.priority_cards

   def getRecentCards(self):
      return self.recent_cards

   def getNumberOfCards(self):
      return self.num_cards

   def getNumberOfPriorityCards(self):
      return self.num_priority_cards

   def getCategories(self):
      return self.categories