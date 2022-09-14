# Kivy boilerplate
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.recycleview import RecycleView
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivy.properties import DictProperty, ColorProperty, StringProperty
from kivymd.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.config import Config

# Dependencies
from validator import Validator
from collections import OrderedDict
import logging as lg
import webbrowser

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.size = (800, 600)
Window.minimum_width, Window.minimum_height = Window.size

font = 'Roboto'

class LinkCard(MDCard):
    linktext = StringProperty()
    
    def open_url(self, *args):
        webbrowser.open(self.linktext)
        
    def delete(self, *args):
        def place(*args):
            props = {
                'linktext': self.linktext
            }
            self.parent.parent.data.remove(props)
            self.parent.remove_widget(self)
        Clock.schedule_once(place)
        
class LinkView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []

class LinkBox(MDTextField):     
    def errormet(self, *args):
        self.error = True

class WindowManager(ScreenManager):
    pass

class MainScreen(MDScreen):
    def text_update(self, new_data: list, *args):
        dictdata = [{'linktext': str(x)} for x in new_data] # remove by id help next time
        if any(x in dictdata for x in self.ids.fv.data):
            raise Exception(f'URL already exists')
        
        self.ids.fv.data.extend(dictdata)
        self.ids.fv.refresh_from_data()
    
    def text_reset(self, *args):
        self.ids.fv.data = []
        self.ids.fv.refresh_from_data()
            
    def text_button(self, *args):
        textinput = self.ids.fb
        output = textinput.text
        if not output:
            return
        output = (list(OrderedDict.fromkeys([y for y in (x.strip() for x in output.splitlines()) if y])))
        for n, x in enumerate(output):
            if '//' not in x:
                x = '%s%s' % ('http://', x)
                output[n] = x
        self.ids.fv.refresh_from_data()
        try:
            Validator.validate(*output)
            self.text_update(output)
            self.ids.fb.text = ''
        except Exception:
            self.ids.fb.errormet()
            
    

class MainApp(MDApp):
    
    def build(self):
        self.font = font
        
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Gray'
        self.theme_cls.primary_hue = '900'
        
        kv = Builder.load_file('ui_kv.kv')
        sm = WindowManager()
        
        screens = [MainScreen(name='main')]
        for screen in screens:
            sm.add_widget(screen)
        
        sm.current = 'main'
        
        return sm


if __name__ == '__main__':
    MainApp().run()