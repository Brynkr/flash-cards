import PySimpleGUI as psg
import constants


# TODO - Standardise button sizes, define button constants for use
# BUTTON_NEXT_TEXT            = "Next"
# BUTTON_ANSWER_TEXT          = "Answer"
# BUTTON_ADD_TEXT             = "Add"
# BUTTON_PRIORITY_TEXT        = "Priority"
# BUTTON_RETURN_TEXT          = "Return"
# BUTTON_SAVE_AND_RETURN_TEXT = "Save and return"


class LayoutMaker:

   def __init__(self):
      # must create layouts on the fly, therefore do nothing
      return


   def completed(self):
      completed_layout = [ [psg.Text("Completed all flash cards. Nice!")],
                           [],
                           [psg.Button("Complete")] ]
      return { "completed" : completed_layout }


   def start(self, card_count):
      start_layout = [ [psg.VPush()],
                       [psg.Text("Cards: {}".format(card_count), text_color='yellow', font=("Arial", 18))],
                       
                       [psg.VPush()],
                       [psg.Button("Study", size=(12, 2)),
                        psg.Button("Study Recent", size=(12, 2)),
                        psg.Button("Priority Study", size=(12, 2))],

                       [psg.Button("Input Study", size=(12, 2)),
                        psg.Button("Auto", size=(12, 2)),
                        psg.Button("Auto Priority", size=(12, 2))],

                       [psg.VPush()],
                       [psg.VPush()],

                       [psg.Button("Add Cards", size=(12, 2)),
                        psg.Button("Generate Audio", size=(12, 2)),
                        psg.Button("Categories", size=(12, 2))],

                       [psg.Button("Toggle Audio", size=(12, 2)),
                        psg.Button("Fullscreen", size=(12, 2)),
                        psg.Button("Exit", size=(12, 2))],
                       [psg.VPush()] ]

      return { "start" : start_layout }


   def display(self, key, value, priority=False):
      front_layout = [ [psg.VPush()],
                       [psg.Text(str(key), font=18)],
                       [psg.Text("")],
                       [psg.Button(constants.BUTTON_ANSWER_TEXT, focus=True, bind_return_key=True, size=(40, 4)),
                        psg.Button(constants.BUTTON_RETURN_TEXT, size=(16, 4))],
                       [psg.VPush()] ]
      if priority:
         back_layout = [ [psg.VPush()],
                         [psg.Text(str(key) + ':', font='Any 28')],
                         [psg.Text(str(value), font='Any 28', text_color='yellow')],
                         [psg.Text("")],
                         [psg.Button(constants.BUTTON_NEXT_TEXT, focus=True, bind_return_key=True, size=(46, 4)),
                          psg.Button(constants.BUTTON_RETURN_TEXT, size=(22, 4))],
                         [psg.VPush()] ]
      else:
         back_layout = [ [psg.VPush()],
                         [psg.Text(str(key) + ':', font='Any 28')],
                         [psg.Text(str(value), font='Any 28', text_color='yellow')],
                         [psg.Text("")],
                         [psg.Button(constants.BUTTON_NEXT_TEXT, focus=True, bind_return_key=True, size=(46, 3)),
                          psg.Button(constants.BUTTON_PRIORITY_TEXT, size=(8, 3)),
                          psg.Button(constants.BUTTON_RETURN_TEXT, size=(8, 3))],
                         [psg.VPush()] ]
      
      return { "front" : front_layout,
               "back" : back_layout }


   def input(self, key, value):
      input_front_layout = [ [psg.VPush()],
                             [psg.Text(str(key), font=18)],
                             [psg.Input(size=(40, 4))],
                             [psg.Button(constants.BUTTON_ANSWER_TEXT, focus=True, bind_return_key=True, size=(7, 3)),
                              psg.Button(constants.BUTTON_RETURN_TEXT, size=(7, 3))],
                             [psg.VPush()] ]
      input_back_layout = [ [psg.VPush()],
                            [psg.Text(str(key) + ':', font='Any 28', text_color='green2')],
                            [psg.Text(str(value), font='Any 28', text_color='yellow')],
                            [psg.VPush()] ]
      incorrect_answer_layout = [ [psg.VPush()],
                                  [psg.Text("INCORRECT", font=18, text_color='red')],
                                  [psg.Text("", font=18)],
                                  [psg.Text(str(key) + "   :", font='Any 28'),
                                   psg.Text(str(value), font='Any 28', text_color='yellow')],
                                  [psg.VPush()] ]
      return { "input_front" : input_front_layout,
               "input_back" : input_back_layout,
               "incorrect" : incorrect_answer_layout }


   def auto(self, key, value):
      auto_layout = [ [psg.VPush()],
                      [psg.Text(str(key) + ':', font='Any 28')],
                      [psg.Text(str(value), font='Any 28', text_color='yellow')],
                      [psg.VPush()] ]
      return { "auto" : auto_layout }


   def add(self):
      add_cards_start_layout = [ [psg.VPush()],
                                 [psg.Text("Add any number of cards. Format {} : {}")],
                                 [psg.Input(size=(40, 4))],
                                 [psg.Text("")],
                                 [psg.Button(constants.BUTTON_ADD_TEXT, focus=True, bind_return_key=True), psg.Button(constants.BUTTON_RETURN_TEXT)],
                                 [psg.VPush()] ]
      add_cards_back_layout = [ [psg.VPush()],
                                [psg.Text("Add any number of cards. Format {} : {}")],
                                [psg.Input(size=(40, 4))],
                                [psg.Text("Added card", text_color='green')],
                                [psg.Button(constants.BUTTON_ADD_TEXT, focus=True, bind_return_key=True), psg.Button(constants.BUTTON_RETURN_TEXT)],
                                [psg.VPush()] ]
      invalid_syntax_layout = [ [psg.VPush()],
                                [psg.Text("Add any number of cards. Format {} : {}")],
                                [psg.Input(size=(40, 4))],
                                [psg.Text("Invalid syntax. Must be key value pair.", text_color='red')],
                                [psg.Button(constants.BUTTON_ADD_TEXT, focus=True, bind_return_key=True), psg.Button(constants.BUTTON_RETURN_TEXT)],
                                [psg.VPush()] ]
      return { "add_cards_start" : add_cards_start_layout,
               "add_cards_back" : add_cards_back_layout,
               "invalid_syntax" : invalid_syntax_layout }


   def category_select(self, categories):
      print("Category select. categories={}".format(categories))
      category_layout = [[psg.VPush()]]
      
      for category in categories.keys():
         category_layout.append([psg.Checkbox(category.strip("[").strip("]"),
                                default=categories[category], font=18)])

      category_layout.append([psg.VPush()])
      category_layout.append([psg.Button("Save and return", size=(8, 3))])
      category_layout.append([psg.VPush()])
      return { "category_select" : category_layout }


   def toggle_audio(self, audio_currently_enabled):
      if audio_currently_enabled:
         return { "toggle_audio" : [ [psg.Text("Audio disabled")], [psg.Button(constants.BUTTON_RETURN_TEXT)] ] }
      else:
         return { "toggle_audio" : [ [psg.Text("Audio enabled")], [psg.Button(constants.BUTTON_RETURN_TEXT)] ] }


   def generating_audio(self, card_count):
      generating_audio_layout = [ [psg.ProgressBar(card_count, key="GEN-AUDIO")],
                                  [psg.Text("Generating audio 0/{}".format(card_count), key="GEN-AUDIO-TEXT")] ]
      return { "generating_audio" : generating_audio_layout }
