import PySimpleGUI as psg

class LayoutMaker:

   def __init__(self):
      # must create layouts on the fly, therefore do nothing
      return


   def completed(self):
      completed_layout = [ [psg.Text("Completed all flash cards. Nice!")],
                           [],
                           [psg.Button("Complete")] ]
      return { "completed" : completed_layout }


   def start(self):
      start_layout = [ [psg.Button("Study", size=(12, 2)),
                        psg.Button("Study Recent (100)", size=(12, 2)),
                        psg.Button("Priority Study", size=(12, 2))],
                       [psg.Button("Input Study", size=(12, 2)),
                        psg.Button("Auto", size=(12, 2)),
                        psg.Button("Auto Priority", size=(12, 2))],
                       [psg.Button("Free View", size=(12, 2)),
                        psg.Button("Add Cards", size=(12, 2)),
                        psg.Button("Fullscreen", size=(12, 2))],
                       [psg.Button("Exit", size=(12, 2))] ]
      return { "start" : start_layout }


   def display(self, key, value):
      front_layout = [ [psg.VPush()],
                       [psg.Text(str(key), font=18)],
                       [psg.Text("")],
                       [psg.Button("Answer", focus=True, bind_return_key=True, size=(40, 4)),
                        psg.Button("Return", size=(16, 4))],
                       [psg.VPush()] ]
      back_layout = [ [psg.VPush()],
                      [psg.Text(str(key) + ':', font='Any 28')],
                      [psg.Text(str(value), font='Any 28', text_color='yellow')],
                      [psg.Text("")],
                      [psg.Button("Next", focus=True, bind_return_key=True, size=(32, 3)),
                       psg.Button("Priority", size=(8, 3)),
                       psg.Button("Return", size=(8, 3))],
                      [psg.VPush()] ]
      priority_back_layout = [ [psg.VPush()],
                               [psg.Text(str(key) + ':', font='Any 28')],
                               [psg.Text(str(value), font='Any 28', text_color='yellow')],
                               [psg.Text("")],
                               [psg.Button("Next", focus=True, bind_return_key=True, size=(15, 3)),
                                psg.Button("Return", size=(15, 3))],
                               [psg.VPush()] ]
      return { "front" : front_layout,
               "back" : back_layout,
               "priority_back" : priority_back_layout }


   def input(self, key, value):
      input_front_layout = [ [psg.VPush()],
                             [psg.Text(str(key), font=18)],
                             [psg.Input(size=(40, 4))],
                             [psg.Button("Answer", focus=True, bind_return_key=True, size=(40, 4)),
                              psg.Button("Return", size=(16, 4))],
                             [psg.VPush()] ]
      input_back_layout = [ [psg.VPush()],
                            [psg.Text(str(key) + ':', font='Any 28')],
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


   def freeView(self, cards):
      free_view_layout = []
      scroll_len = 0
      for key, value in cards.items():
         free_view_layout.append([psg.Button(key, size=(40, 4))])
         scroll_len = scroll_len + 1

      column = [[psg.Text("{}".format(i))] for i in range(scroll_len)]
      free_view_layout.append([psg.Column(column, scrollable=True, vertical_scroll_only=True)])
      return { "free view" : free_view_layout }


   def add(self):
      add_cards_start_layout = [ [psg.VPush()],
                                 [psg.Text("Add any number of cards. Format {} : {}")],
                                 [psg.Input(size=(40, 4))],
                                 [psg.Text("")],
                                 [psg.Button("Add", focus=True, bind_return_key=True), psg.Button("Return")],
                                 [psg.VPush()] ]
      add_cards_back_layout = [ [psg.VPush()],
                                [psg.Text("Add any number of cards. Format {} : {}")],
                                [psg.Input(size=(40, 4))],
                                [psg.Text("Added card", text_color='green')],
                                [psg.Button("Add", focus=True, bind_return_key=True), psg.Button("Return")],
                                [psg.VPush()] ]
      invalid_syntax_layout = [ [psg.VPush()],
                                [psg.Text("Add any number of cards. Format {} : {}")],
                                [psg.Input(size=(40, 4))],
                                [psg.Text("Invalid syntax. Must be key value pair.", text_color='red')],
                                [psg.Button("Add", focus=True, bind_return_key=True), psg.Button("Return")],
                                [psg.VPush()] ]
      return { "add_cards_start" : add_cards_start_layout,
               "add_cards_back" : add_cards_back_layout,
               "invalid_syntax" : invalid_syntax_layout }


   # def column(self, col_len):
      # column = [[psg.Text("")] for i in range(col_len)]