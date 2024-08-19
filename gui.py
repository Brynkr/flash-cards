import sys
import time
import PySimpleGUI as psg
import constants
from deck_handler import DeckHandler
from layout_maker import LayoutMaker
from voice_handler import VoiceHandler

# TODO
# Standardise windows
# Window Manager class. Create all windows at startup, set sizes. Open/Close depending on mode in use

# Categories -- Categories checkboxes, [___] [___]
# -- category recognition

# --> Theme viewer, selector
# sounds API? - pronounciation
# Test automation

class GUI:
   def __init__(self):
      self.fullscreen = False
      self.deck_handler = DeckHandler()
      self.layout_maker = LayoutMaker()
      self.voice_handler = VoiceHandler()
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
         self.setWindowSize(window, 420, 220)

         self.deck_handler.shuffleDeck()

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
         cards = self.deck_handler.getRecentCards()
      elif priority:
         cards = self.deck_handler.getPriorityCards()
      else:
         cards = self.deck_handler.getCards()

      for card in cards:
         print("front = {}, back = {}".format(card.getEnglish(), card.getChinese()))
         layouts = self.layout_maker.display(card.getEnglish(), card.getChinese(), priority)

         while True:
            window = psg.Window("Q", layouts["front"], 
                                finalize=True, resizable=True, element_justification='c')
            self.setWindowSize(window, 520, 160)

            event1, values1 = window.read()
            if event1 == "Answer":
               ### FIXME - self.writeAndPlayAudio(value)
               window.close()
               window = psg.Window("A", layouts["back"],
                                   finalize=True, resizable=True,
                                   element_justification='c')
               self.setWindowSize(window, 640, 210)
               
               event2, values2 = window.read()
               if event2 == "Next":
                  window.close()
                  break
               if event2 == "Priority":
                  self.deck_handler.addPriorityCard(key, value)
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
      for card in self.deck_handler.getCards():
         print("front = {0}, back = {1}".format(card.getEnglish(), card.getChinese()))
         layouts = self.layout_maker.input(card.getEnglish(), card.getChinese())
         if self.inputAnswerPoll(layouts, card.getChinese()) == "Return":
            return

      completed_window = self.layout_maker.completed()    # TODO - Could show correct/incorrect tally
      event_complete, values_complete = completed_window.read()


   # TODO - auto return button
   def autoStudy(self, priority=False):
      while True:
         if priority:
            cards = self.deck_handler.getPriorityCards()
         else:
            cards = self.deck_handler.getCards()

         for card in cards:
            print("front = {0}, back = {1}".format(card.getEnglish(), card.getChinese()))
            layouts = self.layout_maker.auto(card.getEnglish(), card.getChinese())
            window = psg.Window("Q", layouts["auto"], location=(950, 700),
                                finalize=True, resizable=True, element_justification='c')
            self.setWindowSize(window, 320, 120)
            time.sleep(10)
            window.close()


   def addCards(self):
      layouts = self.layout_maker.add()
      window = psg.Window("Add", layouts["add_cards_start"],
                          finalize=True, resizable=True, element_justification='c')
      self.setWindowSize(window, 280, 100)
      event1, values1 = window.read()
      added_status = "start"
      while True:
         if event1 == "Add":
            print("values find = {}".format(values1[0].find(":")))
            if values1[0].find(":") > 0:  # TODO, more syntax checking..
               if added_status != "start":
                  new_window.close()
               self.deck_handler.addCards(values1[0] + "\n")
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
         self.setWindowSize(window, 260, 150)
         event1, values1 = window.read()

         if event1 == "Answer":
            if self.deck_handler.correctAnswer(value, values1[0]):
               window.close()
               window = psg.Window("A", layouts["input_back"],
                                   finalize=True, resizable=True, element_justification='c')
               self.setWindowSize(window, 280, 220)
               time.sleep(8)
               window.close()
               return "Correct"
            else:
               window.close()
               window = psg.Window("Q", layouts["incorrect"],
                                   finalize=True, resizable=True, element_justification='c')
               self.setWindowSize(window, 640, 220)
               time.sleep(8)
               window.close()
               return "Incorrect"

         elif event1 == "Return":
            window.close()
            return "Return"
         elif event1 == psg.WIN_CLOSED:
            sys.exit()


   def writeAudio(self, value):
      self.voice_handler.writeTTSChineseFile(self.deck_handler.getHanZi(value))

   def playAudio(self, audio_path):
      self.voice_handler.closeVLC()
      print("playing {}".format(audio_path))
      self.voice_handler.playWithVLC(audio_path)
      # FIXME - opening instances for each play. If action a 
      #         close then closes immediately before audio can play.
      #         System sleep won't allow audio play.
      # time.sleep(10)
      # self.voice_handler.closeVLC()

   def writeAndPlayAudio(self, value, audio_path=constants.AUDIO_PATH):
      print("Writing audio for: {}".format(value))
      self.writeAudio(value)
      self.playAudio(audio_path)


   def setWindowSize(self, window, default_x=520, default_y=380):
      if self.fullscreen:
         window.Maximize()
      else:
         window.set_size(size=(default_x, default_y))

