import os
import re
import json
from IPython.display import display, Markdown, clear_output
from ipywidgets import (Dropdown, HBox, 
                        VBox, Layout, Label, 
                        Output, Button,RadioButtons,
                        BoundedIntText, SelectMultiple,
                        Checkbox, GridBox)

class QuestionBase:
    def __init__(self, data, checkpoint=False):
        self.checkpoint = checkpoint
        self.prompt = data['prompt'] 
        self.options = data['options']
        if not checkpoint and 'value' not in data:
            raise ValueError('An "answer" key must be included in the `data` variable when checkpoint is set to False')
        self.correct = data['value'] if not checkpoint else None
        
        # ======== Set up configuration file ============
        self.config_path = os.path.join('questions', 'questions.json')
        if not os.path.isdir('questions'):
            os.mkdir('questions')
        
        if not os.path.isfile(self.config_path):
            data = {'questions': {self.prompt: {'options': self.options, 'value': self.correct}}}
            file = open(self.config_path, 'w')
            json.dump(data, file)
            file.close()
        else:
            file = open(self.config_path, 'r')
            data = json.load(file)
            file.close()
            if self.prompt not in data['questions']:
                data['questions'][self.prompt] = {'options': self.options, 'value': self.correct}
                
            file = open(self.config_path, 'w')
            json.dump(data, file)
            file.close()
            
        # =========== Layouts ==============
        self.layout_prompt = Layout(width='auto', bottom='5px')
        self.layout_box = Layout(flex_flow='column',
                                border='solid',
                                width='auto',
                                height='auto',
                                top='5px')
        self.layout_items = Layout(width='auto', 
                                   flex_flow='column', 
                                   top='2px') 
        
        
class QuestionInterface(QuestionBase):
    
    def __init__(self, data, checkpoint=False):
        QuestionBase.__init__(self, data, checkpoint=checkpoint)
        
        # ========= Create components =======
        self.out_prompt =  Output(layout=self.layout_prompt)
        with self.out_prompt:
            display(Markdown(self.prompt))

        self.out_feedback = Output()
        with self.out_feedback:
            display(Markdown('*Please click the submit button or your answer will not be saved!*'))
            
        self.button = Button(description="submit")
        self.button.button_style = 'info'
        self.button.on_click(self.save_answer)
        self.components()
        
        
    def display(self):
        """
        All components are added as rows to a VBox object
        and displayed.
        
        This function assumes the following objects for each question.
        
        1. An initial prompt called `out_prompt`
        2. The controls used to answer the question, 
           stored in a variable called `interface`
        3. A submit button called `button`
        4. A div for rendering feedback to the student
           called out_feedback
            
        """
        return VBox([self.out_prompt, self.interface, 
                    self.button, self.out_feedback], 
                    layout=self.layout_box)
        
    def components(self):
        """
        Should be replaced with a method  of the same name within the inheriting question type.
        
        This method should create the following components:
        1. `self.interface` - An ipywidget containing the controls 
                              used by the student (other than the submit button)
        """
        pass
    
    def collect_answer(self):
        """
        Should be replaced with a method of the same name within the inheriting question type.
        
        This method should 
        - collect a student's answer from the `self.interface` object
        - return the student's answer
        """
        pass
    
    def check(self, answer):
        """
        Default logic for checking a student's answer.
        
        This method should always receive an answer argument containing the student's 
        submitted answer.
        
        If custom answers are preferred based on the student's answer, a custom 
        check function should be added to the inheriting question class.
        
        """
        if answer==self.correct:
            feedback = "✅ **Correct!**"
        else:
            feedback = "❌ **Incorrect**"
        with self.out_feedback:
            clear_output()
            display(Markdown(feedback))
            
    def save_answer(self, object):
        """
        If checkpoint is set to True, a student's answers are saved 
        to the questions/questions.json configuration file.
        
        If checkpoint is set to False, the students answer is compared to
        the correct value and feedback is displayed.
        
        """
        answer = self.collect_answer()
        if not self.checkpoint:
            self.check(answer)
        else:
            
            file = open(self.config_path, 'r')
            data = json.load(file)
            file.close()
            data['questions'][self.prompt]['value'] = answer
            file = open(self.config_path, 'w')
            json.dump(data, file)
            file.close()
            with self.out_feedback:
                clear_output()
                display(Markdown('*Answer submitted!*\n\n>*If you would like to change your answer, simply select your desired answer and reclick submit!*'))
            return



class FillBlank(QuestionInterface):
    def __init__(self, data, checkpoint=False):
        QuestionInterface.__init__(self, data, checkpoint=checkpoint)
        
    def components(self):
        file = open(self.config_path, 'r')
        data = json.load(file)
        options = data['questions'][self.prompt]['value']
        self._parse_options()
        self._parse_sentence()
        self.dropdowns = [Dropdown(
                            options=self.dropdown_options[idx],
                            value=options[idx] if options and self.checkpoint else None,
                            description='',
                            disabled=False,
                            layout=self.layout_items) for idx in range(len(self.dropdown_options))]
        
        self.full_sentence = list(self.sentence)
        count = 1
        for idx in range(len(self.dropdowns)):
            self.full_sentence = self.full_sentence[:idx + count] + [self.dropdowns[idx]] + self.full_sentence[idx + count:]
            count += 1
        
            if idx == len(self.dropdowns) - 1 and len(self.sentence) > len(self.dropdowns):
                remainder = self.full_sentence[idx + count:]
                self.full_sentence = self.full_sentence[:idx + count]
                self.full_sentence.append(''.join(remainder))
                
        for idx in range(len(self.full_sentence)):
            item = self.full_sentence[idx]
            if isinstance(item, str):
                if item.strip() == '.':
                    self.full_sentence.remove(item)
                    continue
                self.full_sentence[idx] = Output()
                with self.full_sentence[idx]:
                    display(Markdown(item))

        self.interface = HBox(self.full_sentence)

            

    def _parse_options(self):
        self.dropdown_options = []
        options = re.findall(r'\{(.*?)\}', self.options)
        for idx in range(len(options)):
            split = options[idx].split(',')
            self.dropdown_options.append([x.strip() for x in split])
            
    def _parse_sentence(self):
        self.sentence = re.findall(r"(.*?)(?:\{.*?\}|$)",self.options)
      
    def collect_answer(self):
        return [drop.value for drop in self.dropdowns]
    

            
class MultiChoice(QuestionInterface):
    
    def __init__(self, data, checkpoint=False):
        QuestionInterface.__init__(self, data,  checkpoint=checkpoint)
        
    def components(self):
        file = open(self.config_path, 'r')
        data = json.load(file)
        value = data['questions'][self.prompt]['value']        
        radio_options = [word for word in self.options]
        
        self.interface = RadioButtons(
            options = radio_options,
            description = '',
            disabled = False,
            value=value if value and self.checkpoint else None,
            layout=self.layout_items)

    def collect_answer(self):
        return self.interface.value
    
class IntegerField(QuestionInterface):
    
    def __init__(self, data, min=0, max=10, steps=1, checkpoint=False):
        self.min = min
        self.max = max
        self.steps = steps
        QuestionInterface.__init__(self, data, checkpoint=checkpoint)
        
    def components(self):
        
        file = open(self.config_path, 'r')
        data = json.load(file)
        value = data['questions'][self.prompt]['value']        
        
        self.interface = BoundedIntText(
                            value=value if value and self.checkpoint else None,
                            min=self.min,
                            max=self.max,
                            step=self.steps,
                            description='',
                            disabled=False,
                            layout=self.layout_items
                          )
        
    def collect_answer(self):
        return self.interface.value
    
    
class MultiSelect(QuestionInterface):
    
    def __init__(self, data, checkpoint=False, rows = False):
        self.rows = rows
        QuestionInterface.__init__(self, data, checkpoint=checkpoint)
        
        
    def components(self):
        
        file = open(self.config_path, 'r')
        data = json.load(file)
        value = data['questions'][self.prompt]['value'] 
        

        
        self.blocks = [Checkbox(value=False, description=str(option)) for option in self.options]
        
#         if self.rows:
#             blocks = []
#             row = []
#             for box in self.blocks:
#                 row.append(box)
#                 if len(row) == self.rows:
#                     blocks.append(HBox(row))
#                     row = []
#                 elif box == self.blocks[-1]:
#                     blocks.append(HBox(row))
#             self.blocks = blocks
        
#         self.interface = VBox(self.blocks)
        columns = round(len(self.blocks)/self.rows)
        
        self.interface = GridBox(children=self.blocks,
                                layout=Layout(
                                    width='50%',
                                    grid_template_rows=('auto '*self.rows).strip() ,
                                    grid_template_columns='{:.0%}'.format(100/columns * 1/100)*columns))
        
    def collect_answer(self):
        selected_data = [block.description for block in self.blocks if block.value]

        return selected_data
    