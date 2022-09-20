# Not supposed to run from '__main__'. run from loadlib.py instead
from src.validator import Validator
from src.download import tempo, Downloader, Found, Downloader_inst, get_title
from src.consts import ALLOWED, LOADLIB
if __name__ == '__main__':
    raise Exception('Run from loadlib.py instead')
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivymd.uix.recycleview import RecycleView
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.properties import DictProperty, ColorProperty, StringProperty, ObjectProperty
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivy.uix.screenmanager import FadeTransition
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.button import MDFlatButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton, ToggleButtonBehavior
from kivymd.uix.chip import MDChip
from kivy.animation import Animation
from kivymd.toast import toast
from kivy.uix.image import Image
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.config import Config
from kivy.loader import Loader
from kivy.uix.image import AsyncImage
from kivy.network.urlrequest import UrlRequest
from collections import OrderedDict
from typing import Callable
import threading
import io
import logging as lg
import randfacts
import webbrowser
import pathlib as ptl
from time import sleep
from functools import partial
import multiprocessing
multiprocessing.freeze_support()

# Local imports

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Loader.loading_image = str((LOADLIB / 'assets' / 'loading').with_suffix('.png'))
Window.size = (800, 600)
Window.minimum_width, Window.minimum_height = Window.size
font = 'Roboto'


class LinkCard(MDCard):
    linktext = StringProperty()
    puretext = StringProperty()
    logo = StringProperty()
    type = StringProperty()

    def delete(self, *args):
        def thing():
            props = {
                'puretext': self.puretext,
                'linktext': self.linktext,
                'type': self.type,
                'logo': self.logo
            }
            self.parent.parent.data.remove(props)
            self.parent.parent.parent.parent.parent.parent.parent.parent.download_state()  # How do you select the app/screen.
            self.parent.remove_widget(self)
        Clock.schedule_once(lambda th: thing())


class LinkView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []


class LinkBox(MDTextField):
    def errormet(self, *args):
        self.error = True


class LoadingScreen(MDScreen):  # todo: fun fact request test # last type

    def on_pre_enter(self, *args):
        self.ids.fun.text = f'Fun Fact:\n{randfacts.get_fact()}'

    def on_touch_down(self, touch):  # Deactivate touch_down event
        if self.collide_point(*touch.pos):
            return True


class WelcomeScreen(MDScreen):

    def on_touch_down(self, touch):
        self.manager.transition.direction = 'up'  # type: ignore
        self.manager.current = 'root_screen'  # type: ignore


class MainScreen(MDScreen):
    path = StringProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            show_hidden_files=True,
            selector='folder',
            search='dirs',
            preview=False
        )

    def text_update(self, new_data: list, *args):

        dictdata = []
        for data in new_data:
            data_props = {}

            data_props['puretext'] = str(data)

            data_props['linktext'] = ''

            logo = ''

            try:
                for k, v in ALLOWED.items():
                    for i in v:
                        if i in str(data):
                            if 'yt' in k:
                                logo = str((LOADLIB / 'assets' / 'youtube').with_suffix('.png'))
                                data_props['type'] = 'yt'
                            elif 'sp' in k:
                                logo = str((LOADLIB / 'assets' / 'spotify').with_suffix('.png'))
                                data_props['type'] = 'sp'
                            raise Found
            except Found:
                pass

            data_props['logo'] = logo

            dictdata.append(data_props)

        if any(x in dictdata for x in self.ids.fv.data):
            raise Exception('URL already exists')

        self.ids.fv.data = dictdata + self.ids.fv.data
        self.ids.fv.refresh_from_data()

    def text_reset(self, *args):
        self.ids.fv.data = []
        self.ids.fv.refresh_from_data()
        self.download_state()

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
            print(self.ids.fb.text)
            print(output)
            Validator.validate(*output)
            self.text_update(output)
            self.ids.fb.text = ''
            self.download_state()
            threading.Thread(target=self.namereq, daemon=True, args=(self.ids.fv.data,)).start()
        except Exception:
            self.ids.fb.errormet()

    def namereq(self, data):
        for n, d in enumerate(data):
            d['linktext'] = get_title(d['puretext'], d['type'])
            data[n] = d
        self.namereq_end(data)

    @mainthread
    def namereq_end(self, data):
        self.ids.fv.data = data
        self.ids.fv.refresh_from_data()

    def file_manager_open(self):
        self.path = ''
        self.file_manager.show_disks()  # output manager to the screen
        self.manager_open = True
        self.download_state()

    def select_path(self, path):
        """Called when the catalog selection button is clicked."""

        self.manager_open = False
        self.file_manager.close()
        toast(path)
        self.path = path
        self.download_state()

    def exit_manager(self, *args):
        """Called when the user reaches the root of the directory tree."""

        self.manager_open = False
        self.file_manager.close()
        self.download_state()
        toast('Unselected output directory')

    def download_state(self):
        if self.path:
            if self.ids.fv.data:
                self.ids.download.disabled = False
                return
        self.ids.download.disabled = True


class RootScreenManager(MDScreenManager):
    pass


class MainApp(MDApp):  # type: ignore
    def build(self):
        self.font = font

        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.primary_hue = 'A400'

        kv = Builder.load_file(str((LOADLIB / 'src' / 'main_ui').with_suffix('.kv')))

        return RootScreenManager()

    def on_start(self):
        super().on_start()
        self.root.current = 'welcome'  # type: ignore
        self.root.ids.main_screen.ids.download.bind(on_release=partial(self.launch, self.down_start))  # type: ignore

    # kivy threading magic start

    def launch(self, func, w=None):
        self.root.transition.direction = 'down'  # type: ignore
        self.root.current = 'loading'  # type: ignore
        threading.Thread(target=self.thread, args=(func,), daemon=True).start()

    def down_start(self):
        Downloader_inst.start(*[x['puretext'] for x in self.root.ids.main_screen.ids.fv.data],  # type: ignore
                              out=self.root.ids.main_screen.path)  # type: ignore

    def thread(self, func):
        func()
        self.down_end()

    @mainthread
    def down_end(self):
        self.root.transition.direction = 'up'  # type: ignore
        self.root.current = 'root_screen'  # type: ignore
        self.root.ids.main_screen.text_reset()  # type: ignore
        self.root.ids.path = ''  # type: ignore
    # kivy threading magic end
