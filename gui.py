import sys
import time
import PySimpleGUI as psg
import constants
from card_handler import CardHandler
from layout_maker import LayoutMaker


# TODO
# Standardise windows
# TODO - Freeview.. clickable cards
# Window Manager class. Create all windows at startup, set sizes. Open/Close depending on mode in use
# --> Theme viewer, selector
# sounds API??? - pronounciation
# Test automation!


class GUI:

   def __init__(self):
      self.fullscreen = False
      self.card_handler = CardHandler()
      self.layout_maker = LayoutMaker()
      #TODO - default_window_size
      psg.theme("DarkTeal2")


   def toggleFullscreen(self, window):
      self.fullscreen = not self.fullscreen
      window.close()


   def startMenu(self):
      while True:
         layouts = self.layout_maker.start()
         window = psg.Window("Flash Cards", layouts["start"],
                             finalize=True, resizable=True, element_justification='c')
         if self.fullscreen:
            window.Maximize()
         else:
            window.set_size(size=(420, 280))
         event, values = window.read()
         if event == "Study":
            window.close()
            self.displayCards()
         elif event == "Study Recent (100)":
            window.close()
            self.displayCards(recent=True)
         elif event == "Priority Study":
            window.close()
            self.displayCards(priority=True)
         elif event == "Input Study":
            window.close()
            self.inputStudy()
         elif event == "Auto":
            window.close()
            self.autoStudy()
         elif event == "Auto Priority":
            window.close()
            self.autoStudy(priority=True)
         elif event == "Free View":
            window.close()
            self.freeViewStudy()
         elif event == "Add Cards":
            window.close()
            self.addCards()
         elif event == "Fullscreen":
            self.toggleFullscreen(window)
            continue
         elif event == "Exit":
            sys.exit()


   def displayCards(self, recent=False, priority=False):
      if recent:
         cards = self.card_handler.getRecent(100)
      elif priority:
         cards = self.card_handler.getPriorityCards()
      else:
         cards = self.card_handler.getCards()

      for key, value in cards.items():
         print("front = {}, back = {}".format(key, value))
         layouts = self.layout_maker.display(key, value)

         while True:
            window = psg.Window("Q", layouts["front"], 
                                finalize=True, resizable=True, element_justification='c')
            if self.fullscreen:
               window.Maximize()
            else:
               window.set_size(size=(520, 160))
            event1, values1 = window.read()
            if event1 == "Answer":
               window.close()
               if priority:
                  window = psg.Window("A", layouts["priority_back"],
                                      finalize=True, resizable=True, element_justification='c')
               else:
                  window = psg.Window("A", layouts["back"],
                                      finalize=True, resizable=True, element_justification='c')

               if self.fullscreen:
                  window.Maximize()
               else:
                  if len(value) <= constants.WORD_LEN_LIM:
                     window.set_size(size=(520, 210))
                  else:
                     window.set_size(size=(640, 210))
               
               event2, values2 = window.read()
               if event2 == "Next":
                  window.close()
                  break
               if event2 == "Priority":
                  self.card_handler.addPriorityCard(key, value)
                  window.close()
                  break
               elif event2 == psg.WIN_CLOSED or event2 == "Return":
                  window.close()
                  return

            elif event1 == "Return":
               window.close()
               return
            elif event1 == psg.WIN_CLOSED:
               sys.exit()

      completed_window = psg.Window("Complete", layouts["completed"])
      event_complete, values_complete = completed_window.read()


   def inputStudy(self):
      for key, value in self.card_handler.getCards().items():
         print("front = {0}, back = {1}".format(key, value))
         layouts = self.layout_maker.input(key, value)
         self.inputAnswerPoll(layouts, value)

      completed_window = self.layout_maker.completed()
      event_complete, values_complete = completed_window.read()


   def autoStudy(self, priority=False):
      print("autostudy fullscreen={}".format(self.fullscreen))
      while True:
         if priority:
            cards = self.card_handler.getPriorityCards()
         else:
            cards = self.card_handler.getCards()

         for key, value in cards.items():
            print("front = {0}, back = {1}".format(key, value))
            layouts = self.layout_maker.auto(key, value)
            window = psg.Window("Q", layouts["auto"], location=(950, 700),
                                finalize=True, resizable=True, element_justification='c')
            if self.fullscreen:
               window.Maximize()
            else:
               window.set_size(size=(320, 120))
            time.sleep(10)
            window.close()


   def freeViewStudy(self):
      cards = self.card_handler.getCards()
      layouts = self.layout_maker.freeView(cards)
      free_view_window = psg.Window("Free View", layouts["free view"],
                                    finalize=True, resizable=True, element_justification='c')
      if self.fullscreen:
         free_view_window.Maximize()
      else:
         free_view_window.set_size(size=(560, 560))
      event1, values1 = free_view_window.read()

      for key, value in cards.items():
         if event1 == key:
            # free_view_window.close()
            layouts = self.layout_maker.input(key, value)
            input_window = psg.Window("Q", layouts["input_front"],
                                      finalize=True, resizable=True, element_justification='c')
            if self.fullscreen:
               input_window.Maximize()
            else:
               input_window.set_size(size=(520, 150))
            event1, values1 = input_window.read()
            if self.inputAnswerPoll(layouts, value):
               # tick box.... then continue
               tickCompleteButton(key)

#FIXME
   def tickCompleteButton(self, key):
      cards = self.card_handler.getCards()
      layouts = self.layout_maker.freeView(cards)

      # todo - update the key button with only 'tick' icon

      psg.Window("Free View", layouts["free view"],
                 finalize=True, resizable=True, element_justification='c')
      free_view_window.set_size(size=(560, 560))
      event1, values1 = free_view_window.read()


   def addCards(self):
      layouts = self.layout_maker.add()
      window = psg.Window("Add", layouts["add_cards_start"],
                          finalize=True, resizable=True, element_justification='c')
      if self.fullscreen:
         window.Maximize()
      else:
         window.set_size(size=(280, 100))
      event1, values1 = window.read()
      added_status = "start"
      while True:
         if event1 == "Add":
            print("values find = {}".format(values1[0].find(":")))
            if values1[0].find(":") > 0:  # TODO, more syntax checking..
               if added_status != "start":
                  new_window.close()
               self.card_handler.addCards(values1[0] + "\n")
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
            event1, values1 = new_window.read()
         elif event1 == "Return":
            window.close()
            return
         elif event1 == psg.WIN_CLOSED:
               sys.exit()



   def inputAnswerPoll(self, layouts, value):
      while True:
         window = psg.Window("Q", layouts["input_front"],
                             finalize=True, resizable=True, element_justification='c')
         if self.fullscreen:
            window.Maximize()
         else:
            window.set_size(size=(520, 150))
         event1, values1 = window.read()

         if event1 == "Answer":
            if self.card_handler.correctAnswer(value, values1[0]):
               window.close()
               window = psg.Window("A", layouts["input_back"],
                                   finalize=True, resizable=True, element_justification='c')
               if self.fullscreen:
                  window.Maximize()
               else:
                  if len(value) <= constants.WORD_LEN_LIM:
                     window.set_size(size=(520, 220))
                  else:
                     window.set_size(size=(640, 220))
               time.sleep(8)
               window.close()
               # return True / False to indicate if answered correctly? for use in Free View
               return True
               # break
            else:
               window.close()
               window = psg.Window("Q", layouts["incorrect"],
                                   finalize=True, resizable=True, element_justification='c')
               if self.fullscreen:
                  window.Maximize()
               else:
                  if len(value) <= constants.WORD_LEN_LIM:
                     window.set_size(size=(520, 340))
                  else:
                     window.set_size(size=(640, 220))
               time.sleep(8)
               window.close()
               # break
               return False
         elif event1 == "Return":
            window.close()
            return
         elif event1 == psg.WIN_CLOSED:
            sys.exit()
