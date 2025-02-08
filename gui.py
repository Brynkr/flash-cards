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
# automated tests....
# specify auto timer duration

# FIXME - refactor to main.py? separate some functions out of GUI class

class GUI:
   def __init__(self):
      self._deck_handler = DeckHandler()
      self._layout_maker = LayoutMaker()
      self._voice_handler = VoiceHandler()

      self._fullscreen = False
      self._categories = self._deck_handler.categories
      self._categories[constants.CATEGORY_NO_TAGS] = False

      #TODO - default_window_size
      psg.theme(constants.GUI_THEME)


   def start_menu(self):
      while True:
         layouts = self._layout_maker.start(len(self._deck_handler.cards))
         window = psg.Window("Flash Cards", layouts["start"],
                             finalize=True, resizable=True, element_justification='c')
         self.set_window_size(window, 420, 380)
         self._deck_handler.shuffle_deck()

         event, values = window.read()

         if not self._deck_handler.cards:
            if event != "Add Cards" and event != "Fullscreen":
               print("No cards in the deck! Can't continue until cards are added.")
               sys.exit()

         if event == "Study":
            window.close()
            self.display_study()
         elif event == "Study Recent (100)":
            window.close()
            self.display_study(recent=True)
         elif event == "Priority Study":
            window.close()
            self.display_study(priority=True)
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
         elif event == "Toggle Audio":
            self.toggle_audio()
         elif event == "Generate Audio":
            self.generate_audio(self._deck_handler.deck)
         elif event == "Exit" or event == psg.WIN_CLOSED:
            sys.exit()


   def display_study(self, recent=False, priority=False):
      if recent:
         cards = self._deck_handler.category_card_filter(self._deck_handler.recent_cards,
                                                         self._categories)
      elif priority:
         cards = self._deck_handler.category_card_filter(self._deck_handler.priority_cards,
                                                         self._categories)
      else:
         cards = self._deck_handler.category_card_filter(self._deck_handler.cards,
                                                         self._categories)

      for card in cards:
         print("front = {}, back = {}".format(card.english, card.chinese))
         layout_display = self._layout_maker.display(card.english, card.chinese, priority)

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

               if self._voice_handler.is_enabled:
                  self._voice_handler.play_audio_files(card.english)
               
               event2, values2 = window.read()
               if event2 == constants.BUTTON_NEXT_TEXT:
                  window.close()
                  break
               if event2 == constants.BUTTON_PRIORITY_TEXT:
                  self._deck_handler.add_priority_card(key, value)
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

      layout_completed = self._layout_maker.completed()
      completed_window = psg.Window("Complete", layout_completed["completed"])
      event_complete, values_complete = completed_window.read()


   def input_study(self):
      for card in self._deck_handler.category_card_filter(self._deck_handler.cards, self._categories):
         print("front = {}, back = {}".format(card.english, card.chinese))
         layouts = self._layout_maker.input(card.english, card.chinese)
         if self.input_answer_poll(layouts, card) == constants.BUTTON_RETURN_TEXT:
            return

      completed_window = self._layout_maker.completed()
      event_complete, values_complete = completed_window.read()


   def auto_study(self, priority=False):
      while True:
         self._deck_handler.shuffle_deck()

         if priority:
            cards = self._deck_handler.category_card_filter(self._deck_handler.priority_cards, self._categories)
         else:
            cards = self._deck_handler.category_card_filter(self._deck_handler.cards, self._categories)

         for card in cards:
            print("front = {}, back = {}".format(card.english, card.chinese))
            auto_layout = self._layout_maker.auto(card.english, card.chinese)
            window = psg.Window("Q", auto_layout["auto"], location=(950, 700),
                                finalize=True, resizable=True, element_justification='c')
            self.set_window_size(window, 320, 120)

            if self._voice_handler.is_enabled:
               self._voice_handler.play_audio_files(card.english)

            time.sleep(constants.AUTO_DISPLAY_DELAY_SEC)
            window.close()


   def add_cards(self):
      layouts = self._layout_maker.add()
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
               self._deck_handler.add_cards(values[0] + "\n")
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


   def input_answer_poll(self, layouts, card):
      while True:
         window = psg.Window("Q", layouts["input_front"],
                             finalize=True, resizable=True, element_justification='c')
         self.set_window_size(window, 260, 150)
         event, input_values = window.read()

         if event == "Answer":
            if self._deck_handler.correct_answer(card.chinese, input_values[0]):
               window.close()
               window = psg.Window("A", layouts["input_back"],
                                   finalize=True, resizable=True, element_justification='c')
               self.set_window_size(window, 280, 220)

               if self._voice_handler.is_enabled:
                  self._voice_handler.play_audio_files(card.english)

               time.sleep(constants.ANSWER_DISPLAY_DELAY_SEC)
               window.close()
               return "Correct"
            else:
               window.close()
               window = psg.Window("Q", layouts["incorrect"],
                                   finalize=True, resizable=True, element_justification='c')
               self.set_window_size(window, 640, 220)
               time.sleep(constants.ANSWER_DISPLAY_DELAY_SEC)
               window.close()
               return "Incorrect"

         elif event == constants.BUTTON_RETURN_TEXT:
            window.close()
            return constants.BUTTON_RETURN_TEXT
         elif event == psg.WIN_CLOSED:
            sys.exit()


   def select_categories(self):
      layout = self._layout_maker.category_select(self._categories)
      window = psg.Window("Category Select", layout["category_select"],
                          finalize=True, resizable=True, element_justification='c')
      window_y = 220 + 100 * len(self._categories)
      self.set_window_size(window, 280, window_y)

      while True:
         event, values = window.read()
         print("select_categories categories={}\nvalues={}".format(self._categories, values))

         if event == constants.BUTTON_SAVE_AND_RETURN_TEXT:
            for category in self._categories:
               self._categories[category] = values[list(self._categories.keys()).index(category)]
               print("Saving category checkboxes. set categories[{}] = {}"\
                      .format(category.strip("[").strip("]"), values[list(self._categories.keys()).index(category)]))
            window.close()
            return

         elif event == psg.WIN_CLOSED:
            window.close()
            return


   def set_window_size(self, window, default_x=520, default_y=380):
      if self._fullscreen:
         window.Maximize()
      else:
         window.set_size(size=(default_x, default_y))


   def toggle_fullscreen(self, window):
      self._fullscreen = not self._fullscreen
      window.close()


   def toggle_audio(self):
      layout = self._layout_maker.toggle_audio(self._voice_handler.is_enabled)
      window = psg.Window("Toggle audio",  layout["toggle_audio"],
                          finalize=True, resizable=True, element_justification='c')
      self.set_window_size(window, 240, 120)

      if self._voice_handler.is_enabled:
         self._voice_handler.disable()
      else:
         self._voice_handler.enable()

      time.sleep(constants.TOGGLE_DISPLAY_DELAY_SEC)
      window.close()


   def generate_audio(self, deck):
      layout = self._layout_maker.generating_audio(len(deck.cards))
      window = psg.Window("Generating Audio", layout["generating_audio"],
                          finalize=True, resizable=True, element_justification='c')
      self.set_window_size(window, 480, 120)
      self._voice_handler.generate_audio_files(deck, window)
      window.close()

