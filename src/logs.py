import logging
from pathlib import Path
from kivy.logger import Logger, LOG_LEVELS
import os

os.environ['KIVY_NO_FILELOG'] = '1'

Jou = Logger
Jou.setLevel(LOG_LEVELS['info'])