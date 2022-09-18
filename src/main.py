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
from kivymd.toast import toast
from kivy.uix.image import Image
from kivy.clock import Clock, mainthread
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.config import Config
from kivy.loader import Loader
from kivy.uix.image import AsyncImage
from collections import OrderedDict
from typing import Callable
import threading
import io
import yaml
import logging as lg
import webbrowser
import pathlib as ptl
from time import sleep
from functools import partial
import multiprocessing
multiprocessing.freeze_support()


# Dependencies
try:
    from src.validator import Validator
except:
    from validator import Validator

# Local imports
try:  # run from root
    from src.consts import ALLOWED, LOADLIB
    from src.download import tempo, Downloader, Found, Downloader_inst
except:  # run from main
    from consts import ALLOWED, LOADLIB
    from download import tempo, Downloader, Found, Downloader_inst

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Loader.loading_image = str((LOADLIB / 'assets' / 'loading').with_suffix('.png'))
Window.size = (800, 600)
Window.minimum_width, Window.minimum_height = Window.size
font = 'Roboto'

'hi'


class LinkCard(MDCard):
    linktext = StringProperty()
    puretext = StringProperty()
    logo = StringProperty()

    def open_url(self, *args):
        webbrowser.open(self.puretext)

    def delete(self, *args):
        def thing():
            props = {
                'linktext': self.linktext,
                'puretext': self.puretext,
                'logo': self.logo
            }
            self.parent.parent.data.remove(props)
            self.parent.parent.parent.parent.parent.parent.parent.parent.download_disable_update()  # wow
            self.parent.remove_widget(self)
        Clock.schedule_once(lambda th: thing())


class LinkView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []


class LinkBox(MDTextField):
    def errormet(self, *args):
        self.error = True


class WindowManager(MDScreenManager):
    pass


class LoadingLayout(MDScreen):
    def on_touch_down(self, touch):  # Deactivate touch_down event
        if self.collide_point(*touch.pos):
            return True


class NavBar(MDTopAppBar):
    pass


class MainScreen(MDScreen):
    path = None

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
        self.path = ''

    def text_update(self, new_data: list, *args):

        dictdata = []
        for data in new_data:
            data_props = {}

            data_props['linktext'] = ('[color=000000]' + str(data) + '[/color]')

            data_props['puretext'] = str(data)

            logo = ''

            try:
                for k, v in ALLOWED.items():
                    for i in v:
                        if i in str(data):
                            if 'yt' in k:
                                logo = 'https://raw.githubusercontent.com/velolib/loadlib/main/assets/youtube.png'
                            elif 'sp' in k:
                                logo = 'https://raw.githubusercontent.com/velolib/loadlib/main/assets/spotify.png'
                            raise Found
            except Found:
                pass

            data_props['logo'] = logo

            dictdata.append(data_props)

        if any(x in dictdata for x in self.ids.fv.data):
            raise Exception(f'URL already exists')

        self.ids.fv.data = dictdata + self.ids.fv.data
        self.ids.fv.refresh_from_data()

    def text_reset(self, *args):
        self.ids.fv.data = []
        self.ids.fv.refresh_from_data()
        self.download_disable_update()

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
            self.download_disable_update()
        except Exception as e:
            print(e)
            self.ids.fb.errormet()

    def file_manager_open(self):
        self.path = ''
        self.file_manager.show_disks()  # output manager to the screen
        self.manager_open = True
        self.download_disable_update()

    def select_path(self, path):
        """Called when the catalog selection button is clicked."""

        self.exit_manager()
        toast(path)
        self.path = path
        self.download_disable_update()

    def exit_manager(self, *args):
        """Called when the user reaches the root of the directory tree."""

        self.manager_open = False
        self.file_manager.close()
        self.download_disable_update()

    def download_disable_update(self):
        if self.path:
            if self.ids.fv.data:
                self.ids.download.disabled = False
                return
        self.ids.download.disabled = True


class RootScreenManager(MDScreenManager):
    pass


class MainApp(MDApp):  # type: ignore
    loading_layout = None

    def build(self):
        self.font = font

        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.primary_hue = 'A400'

        try:
            kv = Builder.load_file('ui.kv')
        except:
            Builder.unload_file('ui.kv')
            kv = Builder.load_file('src/ui.kv')

        return RootScreenManager()

    def on_start(self):
        super().on_start()
        self.root.current = 'root_screen'  # type: ignore
        self.loading_layout = LoadingLayout()
        self.root.add_widget(self.loading_layout)  # type: ignore
        self.root.ids.main_screen.ids.download.bind(on_release=partial(self.launch, self.start))  # type: ignore

    # kivy threading magic start

    def launch(self, func, w=None):
        self.root.current = 'loading'  # type: ignore
        threading.Thread(target=self.thread, args=(func,), daemon=True).start()

    def start(self):
        Downloader_inst.start(*[x['puretext'] for x in self.root.ids.main_screen.ids.fv.data],  # type: ignore
                            out=self.root.ids.main_screen.path, callme=None)  # type: ignore

    def thread(self, func):
        func()
        self.rem()

    @mainthread
    def rem(self):
        self.root.current = 'root_screen'  # type: ignore
    # kivy threading magic end
