import sys
import time
import PySimpleGUI as psg
import constants
from deck_handler import DeckHandler
from layout_maker import LayoutMaker
from voice_handler import VoiceHandler

# TODO
# Window Manager class. Create and standardise all windows at startup. Open/Close depending on mode in use
# --> Theme viewer, selector
# sounds API? - pronounciation
# automated Tests....

class GUI:
   def __init__(self):
      self.deck_handler = DeckHandler()
      self.layout_maker = LayoutMaker()
      self.voice_handler = VoiceHandler()

      self.fullscreen = False
      self.categories = self.deck_handler.get_categories()
      self.categories[constants.CATEGORY_NO_TAGS] = False

      #TODO - default_window_size
      psg.theme(constants.GUI_THEME)


   def toggle_fullscreen(self, window):
      self.fullscreen = not self.fullscreen
      window.close()


   def start_menu(self):
      while True:
         layouts = self.layout_maker.start()
         window = psg.Window("Flash Cards", layouts["start"],
                             finalize=True, resizable=True, element_justification='c')
         self.set_window_size(window, 420, 300)

         self.deck_handler.shuffle_deck()

         event, values = window.read()
         if event == "Study":
            window.close()
            self.display_cards()
         elif event == "Study Recent (100)":
            window.close()
            self.display_cards(recent=True)
         elif event == "Priority Study":
            window.close()
            self.display_cards(priority=True)
         elif event == "Input Study":
            window.close()
            self.input_study()
         elif event == "Auto":
            window.close()
            self.auto_study()
         elif event == "Auto Priority":
            window.close()
            self.auto_study(priority=True)
         elif event == "Add Cards":
            window.close()
            self.add_cards()
         elif event == "Categories":
            window.close()
            self.select_categories()
         elif event == "Fullscreen":
            self.toggle_fullscreen(window)
            continue
         elif event == "Exit":
            sys.exit()


   def display_cards(self, recent=False, priority=False):
      if recent:
         cards = self.deck_handler.category_card_filter(self.deck_handler.get_recent_cards(),
                                                      self.categories)
      elif priority:
         cards = self.deck_handler.category_card_filter(self.deck_handler.get_priority_cards(),
                                                      self.categories)
      else:
         cards = self.deck_handler.category_card_filter(self.deck_handler.get_cards(),
                                                      self.categories)

      for card in cards:
         print("front = {}, back = {}".format(card.get_english(), card.get_chinese()))
         layout_display = self.layout_maker.display(card.get_english(), card.get_chinese(), priority)

         while True:
            window = psg.Window("Q", layout_display["front"], 
                                finalize=True, resizable=True, element_justification='c')
            self.set_window_size(window, 520, 160)

            event1, values1 = window.read()
            if event1 == "Answer":
               window.close()
               window = psg.Window("A", layout_display["back"],
                                   finalize=True, resizable=True,
                                   element_justification='c')
               self.set_window_size(window, 640, 210)
               
               event2, values2 = window.read()
               if event2 == constants.BUTTON_NEXT_TEXT:
                  window.close()
                  break
               if event2 == constants.BUTTON_PRIORITY_TEXT:
                  self.deck_handler.add_priority_card(key, value)
                  window.close()
                  break
               elif event2 == psg.WIN_CLOSED or event2 == constants.BUTTON_RETURN_TEXT:
                  window.close()
                  return

            elif event1 == constants.BUTTON_RETURN_TEXT:
               window.close()
               return
            elif event1 == psg.WIN_CLOSED:
               sys.exit()

      layout_completed = self.layout_maker.completed()
      completed_window = psg.Window("Complete", layout_completed["completed"])
      event_complete, values_complete = completed_window.read()


   def input_study(self):
      for card in self.deck_handler.category_card_filter(self.deck_handler.get_cards(), self.categories):
         print("front = {}, back = {}".format(card.get_english(), card.get_chinese()))
         layouts = self.layout_maker.input(card.get_english(), card.get_chinese())
         if self.input_answer_poll(layouts, card.get_chinese()) == constants.BUTTON_RETURN_TEXT:
            return

      completed_window = self.layout_maker.completed()
      event_complete, values_complete = completed_window.read()


   def auto_study(self, priority=False):
      while True:
         self.deck_handler.shuffle_deck()

         if priority:
            cards = self.deck_handler.category_card_filter(self.deck_handler.get_priority_cards(), self.categories)
         else:
            cards = self.deck_handler.category_card_filter(self.deck_handler.get_cards(), self.categories)

         for card in cards:
            print("front = {}, back = {}".format(card.get_english(), card.get_chinese()))
            auto_layout = self.layout_maker.auto(card.get_english(), card.get_chinese())
            window = psg.Window("Q", auto_layout["auto"], location=(950, 700),
                                finalize=True, resizable=True, element_justification='c')
            self.set_window_size(window, 320, 120)
            time.sleep(constants.AUTO_DISPLAY_DELAY)
            window.close()


   def add_cards(self):
      layouts = self.layout_maker.add()
      window = psg.Window("Add", layouts["add_cards_start"],
                          finalize=True, resizable=True, element_justification='c')
      self.set_window_size(window, 280, 100)
      event, values = window.read()
      added_status = "start"
      while True:
         if event == constants.BUTTON_ADD_TEXT:
            print("values find = {}".format(values[0].find(constants.CARD_SIDE_DELIMITER)))
            if values[0].find(constants.CARD_SIDE_DELIMITER) > 0:  # TODO, more syntax checking..
               if added_status != "start":
                  new_window.close()
               self.deck_handler.add_cards(values[0] + "\n")
               new_window = psg.Window("Add", layouts["add_cards_back"],
                                       finalize=True, resizable=True, element_justification='c')
               added_status = "added"
            else:
               if added_status != "start":
                  new_window.close()
               new_window = psg.Window("Add", layouts["invalid_syntax"],
                                       finalize=True, resizable=True, element_justification='c')
               added_status = "invalid"

            window.close()
            layouts = self.layoutMaker()
            event, values = new_window.read()
         elif event == constants.BUTTON_RETURN_TEXT:
            window.close()
            return
         elif event == psg.WIN_CLOSED:
               sys.exit()


   def input_answer_poll(self, layouts, correct_value):
      while True:
         window = psg.Window("Q", layouts["input_front"],
                             finalize=True, resizable=True, element_justification='c')
         self.set_window_size(window, 260, 150)
         event, input_values = window.read()

         if event == "Answer":
            if self.deck_handler.correct_answer(correct_value, input_values[0]):
               window.close()
               window = psg.Window("A", layouts["input_back"],
                                   finalize=True, resizable=True, element_justification='c')
               self.set_window_size(window, 280, 220)
               time.sleep(constants.ANSWER_DISPLAY_DELAY)
               window.close()
               return "Correct"
            else:
               window.close()
               window = psg.Window("Q", layouts["incorrect"],
                                   finalize=True, resizable=True, element_justification='c')
               self.set_window_size(window, 640, 220)
               time.sleep(constants.ANSWER_DISPLAY_DELAY)
               window.close()
               return "Incorrect"

         elif event == constants.BUTTON_RETURN_TEXT:
            window.close()
            return constants.BUTTON_RETURN_TEXT
         elif event == psg.WIN_CLOSED:
            sys.exit()


   def select_categories(self):
      layout = self.layout_maker.category_select(self.categories)
      window = psg.Window("Category Select", layout["category_select"],
                          finalize=True, resizable=True, element_justification='c')
      window_y = 220 + 100 * len(self.categories)
      self.set_window_size(window, 280, window_y)

      while True:
         event, values = window.read()
         print("select_categories categories={}\nvalues={}".format(self.categories, values))

         if event == constants.BUTTON_SAVE_AND_RETURN_TEXT:
            for category in self.categories:
               self.categories[category] = values[list(self.categories.keys()).index(category)]
               print("Saving category checkboxes. set categories[{}] = {}"\
                      .format(category.strip("[").strip("]"), values[list(self.categories.keys()).index(category)]))
            window.close()
            return

         elif event == psg.WIN_CLOSED:
            window.close()
            return


   def set_window_size(self, window, default_x=520, default_y=380):
      if self.fullscreen:
         window.Maximize()
      else:
         window.set_size(size=(default_x, default_y))

