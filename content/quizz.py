# %load quizz.py
try:
    from ipywidgets import widgets
except ImportError:
    widgets = None
# from metakernel import Magic, option
import os
import getpass
import datetime

from collections import OrderedDict
from IPython.display import Markdown, Image
import re
from functools import reduce
from random import shuffle

from datetime import datetime, timedelta
# from metakernel.display import display, Javascript
import threading

import json



        
class QuizTimeOut(Exception):
    def __init__(self, body):
        DialogBox('Quiz Time Out', body)
        
        
class DialogBox():
    
    def __init__(self, title, body):
        
        self.js = """require(["base/js/dialog"],function(dialog) {{dialog.modal({{title: "{0}",body: "{1}",buttons: {{'OK': {{}}}} }});}});""".format(title, body)
                
        self.display()
        
    def display(self):
        display(Javascript(self.js))

        
class Activity(object):
    def __init__(self, datetime, alloted_time):
        self.questions = []
        self.filename = None
        self.results_filename = None
        self.instructors = []
        self.show_initial = True
        self.last_id = None
        self.start_datetime = datetime
        self.alloted_time = alloted_time
        
        self.quiz_container = []
        self.results = []
        self.overall_right_options = []
        self.mark = None
        self.submit_button = False
        self.timer = None

    def load(self, filename):
        if filename.startswith("~"):
            filename = os.path.expanduser(filename)
        filename = os.path.abspath(filename)
        self.filename = filename
        
#         if self.quiz_filename is None:
#             self.quiz_filename = filename + ".quiz"
#         touch(self.quiz_filename)
        
        with open(self.filename, 'r') as f:
            filestr = f.read()
            filestr, num_quizzes = typeset_quizzes1(filestr, insert_missing_quiz_header=False)
            json_quiz, _, _ = extract_quizzes(filestr, 'python')            
#         with open(filename, "w") as fp:
#             fp.write(self.code)
        self.load_json(json_quiz)
                
        
    def load_json(self, json_text):
        self.index = 0
        for item in json_text:
            question = item["question"]
            question_figure = item.get("figure", None)
            keywords = item.get("keywords", None)
            label = item.get("label", None)
            options = item["choices"]
            q = Question(item["id"], question, question_figure, options, keywords, label)
            self.questions.append(q)

        self.build_quiz_env()
       
    def handle_submit(self, sender):

        for item in self.quiz_container[:-1]:
            results = {}
            answers = []
            
            id = item.children[0].children[0].children[0].children[1].get_state()['outputs'][0]['data']['text/markdown'].split(':')[1].strip('**')
            results['no'] = int(id)
#             question = item.children[0].children[0].children[1].value.strip('</h1>')
#             results['question'] = question
            
            for q in self.questions:
                if int(q.id) == int(id):
                    for i in range(len(q.options)):
                        if item.children[0].children[0].children[i+2].children[0].value == True:
                            answers.append(item.children[0].children[0].children[i+2].children[1].children[0].\
                                          get_state()['outputs'][0]['data']['text/markdown'])
                           
                        # disable the check button
                        item.children[0].children[0].children[i+2].children[0].disabled = self.submit_button = True
#                         self.timer.cancel()
                        
                    results['choices'] = answers
                    
                    self.results.append(results)
                    
#                     print(self.results)
            
            
#         print(self.results)
        #self.grader()
                
            
        with open(self.results_filename, "a+") as g:
            self.results.append({'submitted@': datetime.today().strftime('%m/%d/%Y %I:%M%p')})
            g.write(json.dumps(self.results))
            
        

    def callback(self):
        if not self.submit_button:
            self.handle_submit(None)

    def render(self):
        try:

            # if date and time does not => than current time and date display a beautiful message and clear it
            #         datetime1 = datetime.strptime('07/11/2019 02:45PM', '%m/%d/%Y %I:%M%p')
            # quiz_time = datetime.strptime(self.start_datetime, '%m/%d/%Y %I:%M%p')

            # prep_time = 10 # loading time

            # alloted_time = (quiz_time + timedelta(seconds=(int(self.alloted_time) + prep_time)) -  datetime.now()).total_seconds()

#             if quiz_time > datetime.today():
#                 raise QuizTimeOut('There is an active quiz, but please check back at {} prompt!'.format(quiz_time.strftime('%I:%M%p')))

#             if alloted_time <= 0:
#                 raise QuizTimeOut('There is no active quiz at this time')

            return widgets.VBox(self.quiz_container)

#             self.timer = threading.Timer(alloted_time, self.callback)
#             self.timer.start() 

        except QuizTimeOut:
            pass


    def build_quiz_env(self):
        # enable pages using Tab widget
        
        for item in self.questions:
            self.results_html = widgets.HTML("")
            self.top_margin = widgets.HTML("")
            #self.top_margin.layout.height = "100px"
            right_stack = widgets.VBox([self.top_margin, self.results_html])
            self.stack = widgets.VBox([widgets.HBox([item.tick_widget, item.id_widget]), widgets.VBox([item.question_widget, item.question_figure_widget, item.keywords_widget])] + item.choice_row_list)
#                                        + [widgets.HBox([self.prev_button, self.results_button, self.next_button])])
            self.output = widgets.Output(layout={'border': '1px solid black'})
            self.top_level = widgets.VBox([widgets.HBox([self.stack, right_stack]), self.output])
            
            self.quiz_container.append(self.top_level)
            
            item.tick_widget.layout.visibility = 'hidden'
            item.keywords_widget.layout.visibility = 'hidden'
            
            item.id_widget.layout.visibility = 'hidden'
            
            for wid in item.explain_buttons:
                wid.layout.visibility = 'hidden'

            
        self.button = widgets.Button(description = "Submit")
        self.button.on_click(self.handle_submit)
        self.button.layout.margin = "20px"
        self.score_widgets = widgets.HTML("""<br/><br clear="all"/><b>Score</b>: """)
        
        shuffle(self.quiz_container)
        
        self.quiz_container.append(widgets.VBox([self.score_widgets, self.button]))
        
        self.score_widgets.layout.visibility = 'hidden'
        
        
    def grader(self):
        for i in self.questions:
            self.overall_right_options += i.right_options
            i.keywords_widget.layout.visibility = 'visible'
            for wid in i.explain_buttons:
                if wid.disabled == False:
                    wid.layout.visibility = 'visible'
                    
#         print(self.overall_right_options)
            
        self.mark = [self.results[k] for k in range(len(self.overall_right_options))\
                     if self.results[k] in self.overall_right_options]
        
#         print(self.mark)
        
        self.score_widgets.value += 'Submission successfully recorded'#str(len(self.mark))

        self.score_widgets.layout.visibility = 'visible' #make visible to show score
        self.button.disabled = True
        
        mark = [mark.get('no')for mark in self.mark]
            
        for wid in self.quiz_container[:-1]: # removed the last vbox that contained html widget
            
            id = wid.children[0].children[0].children[0].children[1].get_state()['outputs'][0]['data']['text/markdown'].split(':')[1].strip('**')
            
#             section for displaying ticks as either right or wrong
            
#             if int(id) in mark:
#                 wid.children[0].children[0].children[0].children[0].layout.visibility='visible'
#                 wid.children[0].children[0].children[0].children[0].value = True
                
#             else:
#                 wid.children[0].children[0].children[0].children[0].layout.visibility='visible'
#                 wid.children[0].children[0].children[0].children[0].value = False
                


class Question(object):
    def __init__(self, id, question, question_figure, options, keywords, label):
        self.id = id
        self.question = question
        self.question_figure = question_figure
        self.options = options
        self.keywords = keywords
        self.label = label
        
        self.right_options =  [{'no': self.id}]
        
        self.tick_widget = widgets.Valid()
        self.id_widget = widgets.Output(layout={'border': '1px solid black'})
#         self.question_widget = widgets.HTML("")
        self.question_widget = widgets.Output()
        self.question_figure_widget = widgets.Output()
        self.keywords_widget = widgets.Output()
                                                    
        
        self.choice_widgets = []
        self.explain_widgets = []
        self.choice_row_list = []
        self.explain_buttons = []
        
        
        
        for count in range(len(self.options)):
#             self.choice_widgets.append(widgets.HTML(""))
            self.choice_widgets.append(widgets.Output())
            self.explain_widgets.append(widgets.Output(layout={'border': '1px solid black'}))
            self.explain_buttons.append(widgets.Button(description='', tooltip='See explanation', \
                            layout=widgets.Layout(flex='0 1 auto', width='auto'), icon='fa-info-circle'))
            checkbox = widgets.Checkbox(value=False, disabled=False, description="{}".format(chr(count+97)))
            self.choice_row_list.append(widgets.HBox([checkbox, widgets.HBox([self.choice_widgets[-1], self.explain_buttons[-1]])]))
#             self.choice_row_list.append(widgets.HBox([checkbox,self.choice_widgets[-1]]))

        self.set_id()
        self.set_question()
        self.set_options()
        self.extract_right_options()

            
    def set_question(self):
#         self.question_widget.value = "<h1>%s</h1>" % self.question
        self.question_widget.append_display_data(Markdown(self.question))
        if self.question_figure:
            info = self.question_figure.strip('[').split(']')
            arg_string = info[0].split()
            caption = info[1]
            self.question_figure_widget.append_display_data(Image(arg_string[0], **eval(f"dict({arg_string[1]},{arg_string[2]})")))
        if self.keywords:
            self.keywords_widget.append_display_data(Markdown('<font color=red>*Read up on: {}*</font>'.\
                                                              format(reduce((lambda x,y: x+', '+y), self.keywords))))
    def set_id(self):
#         self.id_widget.value = "<p><b>Question ID</b>: %s</p>" % self.id
        self.id_widget.append_display_data(Markdown('**Question: {}**'.format(str(self.id))))
    def set_options(self):
        for i in range(len(self.options)):
#             print(self.options[i][1])
#             self.choice_widgets[i].value = self.options[i][1]
            self.choice_widgets[i].append_display_data(Markdown(self.options[i][1]))
            try:
                self.explain_widgets[i].append_display_data\
                (Markdown('<font color=red>{}</font>'.format(self.options[i][2])))
                self.explain_buttons[i].tooltip=str(self.options[i][2])

            except:
                self.explain_buttons[i].disabled=True
                pass
    
    def extract_right_options(self):
        self.right_options[0].update({'choices':[option[1] for option in self.options if option[0] == 'right']})
            


