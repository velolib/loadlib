from kivy.clock import Clock
from kivy.properties import (ColorProperty, ListProperty, ObjectProperty,
                             StringProperty, BooleanProperty, NumericProperty)
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineAvatarListItem
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.slider import MDSlider
from loadlib.config import YAML
from kivymd.uix.dropdownitem import MDDropDownItem
from loadlib.const import Resolutions
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp
from loguru import logger

from loadlib.exceptions import UIException


class ConfigSlider(MDSlider):
    """
    Screen: SettingsScreen
    Usage: Slider class that updates config from key_path, int values only

    Args:
        key_path (list | tuple): Dictionary path to config value
        force_int (bool): Whether to floor the float or not. Defaults to True
    """

    key_path = ListProperty()
    force_int = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.init)

    def init(self, *_):
        self.value = YAML.get(self.key_path)

    def on_touch_up(self, *_):
        return YAML.set(self.key_path, int(self.value))


class ConfigTextField(MDTextField):
    """
    Screen: SettingsScreen
    Usage: Text box class that updates config from key_path

    Args:
        key_path (list | tuple): Dictionary path to config value
    """

    key_path = ListProperty()
    max_length = NumericProperty()
    validator = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.init)

    def init(self, *_):
        new = YAML.get(list(self.key_path))
        self.text = new

    def on_text(self, instance_text_field, focus: bool) -> None:
        super().on_focus(instance_text_field, focus)
        val = self.text
        YAML.set(key_path=self.key_path, value=val)

    def insert_text(self, substring, from_undo=False):
        if len(self.text) <= self.max_length:
            return super().insert_text(substring, from_undo=from_undo)


class ConfigDropdown(MDDropDownItem):
    """
    Screen: SettingsScreen
    Usage: Dropdown class that updates config from key_path

    Args:
        key_path (list | tuple): Dictionary path to config value
    """
    cfg_value = None
    key_path = ListProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Clock.schedule_once(self.init)

    def init(self, *_):
        menu_items = [
            {
                'viewclass': 'OneLineListItem',
                'text': f'{i.value}',
                'height': dp(56),
                'on_release': lambda x=f'{i}': self.update_value(x),
            } for i in Resolutions
        ]
        self.menu = MDDropdownMenu(
            caller=self,
            items=menu_items,
            position='center',
            width_mult=4,
        )
        self.menu.bind()
        self.cfg_value = YAML.get(self.key_path)
        self.text = self.cfg_value

    def update_value(self, value, *_):
        self.set_item(value)
        self.menu.dismiss()
        YAML.set(self.key_path, value)

    def on_release(self):
        self.menu.open()


class Item(OneLineAvatarListItem):
    """
    Screen: DownloadScreen, Dialog
    Usage: Shows files that failed to download
    """
    divider = None
    source = StringProperty()


class LinkView(MDRecycleView):
    """
    Screen: DownloadScreen
    Usage: RecycleView class
    """

    data = ObjectProperty([])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LinkCell(MDCard):
    """
    Screen: DownloadScreen
    Usage: RecycleView viewclass
    """
    obj = ObjectProperty()
    title = StringProperty('')
    logo = StringProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
