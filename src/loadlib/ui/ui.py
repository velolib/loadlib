# Run via main.py!

import multiprocessing
from time import sleep
from typing import Callable, List

from loadlib.downloader.download import LinkFactory, Task

multiprocessing.freeze_support()

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
from time import perf_counter
from spotipy import SpotifyClientCredentials, SpotifyException
from kivy import Config
import pathlib as ptl
import os

Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '600')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.clock import Clock, mainthread
from kivy.loader import Loader
from kivy.metrics import dp
from kivy.properties import (ColorProperty, ListProperty, ObjectProperty,
                             StringProperty)
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from loadlib.config import YAML
from loadlib.const import LOADLIB, Resolutions
from loadlib.downloader.download import DownloadReturn
from loadlib.exceptions import DownloaderException
from loadlib.ui.components import widgets
from loadlib.utils import get_duplicates
from loguru import logger
from pytube.exceptions import PytubeError

Loader.loading_image = Loader.image('./assets/loading.png')


def download_runner(func):
    return func()


class SettingsScreen(MDScreen):

    dialog = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass

    def reset_config(self, *_):

        def close_dialog(*_):
            self.dialog.dismiss(force=True)

        def regen(*_):
            YAML.regen()
            MDApp.get_running_app().stop()

        if not self.dialog:
            self.dialog = MDDialog(
                title='Are you sure you want to reset the settings?',
                type='simple',
                buttons=[
                    MDFlatButton(text='YES', on_release=regen),
                    MDFlatButton(text='NO', on_release=close_dialog)
                ]
            )
        self.dialog.open()

    def open_log(self, *_):
        os.startfile(LOADLIB)


class LoadingScreen(MDScreen):
    progress_text = StringProperty('')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update_text(self, num, out_of):
        self.progress_text = f'{num} out of {out_of}'
        self.ids.prog.value = int(100 * (num / out_of))


class DownloadScreen(MDScreen):
    dialog = None
    path = StringProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager_open = False
        self.file_manager = MDFileManager(
            exit_manager=self.fm_exit,
            select_path=self.fm_out,
            show_hidden_files=True,
            selector='folder',
            search='dirs',
            preview=False
        )

    def add_links(self, *_):
        """
        Add links in a different thread
        """
        if not self.ids.tf.text:
            return

        self.ids.spin.active = True
        self.ids.add.disabled = True
        self.ids.tf.disabled = True
        text = list(filter(bool, map(lambda x: x.strip(), self.ids.tf.text.split('\n'))))

        # add links in different thread so as to not freeze the UI
        Thread(target=self.process_links, daemon=True, args=(text, self.ids.lv.data)).start()

    def process_links(self, text: list[str], curr: list[dict], *_):
        """
        Processes links and adds them to the recycleview

        Args:
            text (list): Links to be added
            curr (list): Current links list
        """
        #
        if len(text) > 50:
            return self.add_links_err()

        # check for duplicates
        if get_duplicates(text):
            return self.add_links_err()

        try:
            objects = [LinkFactory(url=i, sp_appid=YAML.get(('settings', 'sp_appid')), sp_secret=YAML.get(('settings', 'sp_secret'))) for i in text]
        except DownloaderException as e:
            if str(e) == 'Invalid spotify credentials':
                Clock.schedule_once(lambda x: toast('Invalid spotify credentials'))
            return self.add_links_err()
        else:
            # TODO: Fix this
            if not objects[0]:  # weird edge case where objects == [None]
                return self.add_links_err()
            to_add = [{'obj': obj, 'title': obj.title, 'logo': obj.logo_path} for obj in objects]

        if len(to_add) != len(text):
            return self.add_links_err()

        to_add_urls = [x['obj'].url for x in to_add]
        curr_urls = [x['obj'].url for x in curr]

        # check for duplicates within dummy
        if get_duplicates(to_add_urls):
            return self.add_links_err()

        # check for intersection between dummy and current list
        if [x for x in to_add_urls if x in curr_urls]:
            return self.add_links_err()

        # check for duplicates with title
        # reason: so no files get overwritten
        if get_duplicates([x['title'] for x in to_add]):
            self.add_links_err()
            return

        self.add_links_success(to_add)

    @mainthread
    def add_links_success(self, data: list[dict], *_):
        """
        Success! Disables the spinner and checks if ready to download

        Args:
            data (list): Validated links
        """
        self.ids.tf.text = ''
        self.ids.lv.data.extend(data)
        self.ids.lv.refresh_from_data()

        self.ids.spin.active = False
        self.ids.add.disabled = False
        self.ids.tf.disabled = False
        self.check_ready()

    @mainthread
    def add_links_err(self, *_):
        """
        Just turns the text field red.
        """
        self.ids.tf.error = True

        self.ids.spin.active = False
        self.ids.add.disabled = False
        self.ids.tf.disabled = False
        self.check_ready()

    def clear_links(self, *_):
        """
        Clears the recycle view
        """
        self.ids.lv.data = []
        self.ids.lv.refresh_from_data()
        self.check_ready()

    def start_download(self, *_):
        """
        Downloads all inputted URLs in another thread
        """
        rsm = MDApp.get_running_app().root
        rsm.ids.loading.ids.prog.value = 0
        rsm.transition.direction = 'down'
        rsm.current = 'loading'

        launch_args = {
            'output': ptl.Path(self.path),
            'max_res': Resolutions(YAML.get(('settings', 'max_res')))
        }

        def helper(tsk: List[Task], cb_progress: Callable, max_threads: int):
            """
            Thread helper function

            Args:
                tsk (list): List of tasks
                cb_progress (Callable): Callback progress function
                threads (int): # of threads to start, > 5 gets weird
            """
            tsk_len = len(tsk)
            cb_progress(0, tsk_len)
            results = []
            with ThreadPoolExecutor(max_workers=min(max_threads, len(tsk))) as pool:
                logger.info(f'Queue starting with {min(max_threads, len(tsk))} threads')
                start_time = perf_counter()
                for i, out in enumerate(as_completed([pool.submit(download_runner, task)
                                                      for task in tsk]), start=1):
                    results.append(out.result())
                    cb_progress(i, tsk_len)
                logger.info(f'Queue finished in {perf_counter() - start_time} with {min(max_threads, len(tsk))} threads')
            sleep(1)  # Stop after progress bar has finished
            self.stop_download(results)

        Thread(target=helper, args=([task for dic in self.ids.lv.data for task in dic['obj'].task(
            **launch_args)], rsm.ids.loading.update_text, YAML.get(('settings', 'threads'))), daemon=True).start()

    @mainthread
    def stop_download(self, results: list[DownloadReturn], *_):
        """
        1. Clear set path from file manager
        2. Switch to root screen
        3. Check for errors, if so raise dialog

        Args:
            results (list): Results list
        """
        self.clear_links()
        self.path = ''

        rsm = MDApp.get_running_app().root
        rsm.transition.direction = 'up'
        rsm.current = 'mainroot'

        def close_dialog(*_):
            self.dialog.dismiss(force=True)

        errors = [i for i in results if not i.result.code]
        if errors:
            if not self.dialog:
                self.dialog = MDDialog(
                    title='Some items failed to download',
                    text='Inspect the .log file for more details',
                    type='simple',
                    items=[widgets.Item(text=i.result.title, source=i.result.self.logo_path) for i in errors],
                    buttons=[
                        MDFlatButton(text="OK", on_release=close_dialog)
                    ]
                )
            self.dialog.open()

    def sel_dir(self):
        """
        Shows the file manager
        """
        self.path = ''
        self.file_manager.show_disks()
        self.manager_open = True

    def fm_out(self, path: str):
        """
        Runs when user has selected a directory, exits the file manager and sets instance variable

        Args:
            path (str): File directory
        """
        self.fm_exit()
        self.path = path
        toast(path)

        self.check_ready()

    def fm_exit(self, *_):
        """
        Runs when the user wants to exit
        """
        self.manager_open = False
        self.file_manager.close()

        self.check_ready()

    def check_ready(self, *_):
        """
        Checks if downloader is ready to start.
        """
        if not self.path:
            self.ids.down.disabled = True
            return
        if not self.ids.lv.data:
            self.ids.down.disabled = True
            return
        self.ids.down.disabled = False


class RSM(MDScreenManager):
    pass


class UIApp(MDApp):
    bg_darker = ColorProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Teal'
        self.theme_cls.primary_hue = 'A400'
        self.theme_cls.material_style = 'M3'
        self.card_color = [1, 1, 1, 0.02]
        self.bg_darker = [0.06, 0.06, 0.06, 1]

    def build(self):
        from kivy.lang import Builder
        self.title = 'Loadlib'

        try:
            Builder.load_file('./ui_kv.kv')
        except FileNotFoundError:
            Builder.load_file('./src/loadlib/ui/ui_kv.kv')

        sm = RSM()
        return sm
