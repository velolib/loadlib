import io
try:  # run from root
    from src.logs import Jou
except ImportError:  # run from main
    from logs import Jou
import os
import pathlib as ptl
import sys
import ruamel.yaml as rym
from functools import reduce
from operator import getitem

ALLOWED = {
    'yt_playlist': ['youtube.com/playlist'],
    'yt_video': ['youtube.com/watch', 'youtu.be/'],
    'sp_song': ['open.spotify.com/track'],
    'sp_album': ['open.spotify.com/album'],
    'sp_playlist': ['open.spotify.com/playlist']
}

DATASET = [
    'https://www.youtube.com/watch?v=u3MX-rUtS6M',
    'https://www.youtube.com/playlist?list=PLiIiNXduj3VCT5H6Y8Ks2gCLUx0ZlG8Cj',
    'https://open.spotify.com/playlist/2HhBAqvtxeLmdJBlOlx18l?si=cbea0aa82b274487',
    'https://open.spotify.com/track/3Vkyy6CB4UDEvFncUBc53z?si=4db5473b9a3d492c',
    'https://open.spotify.com/album/2d2QJv4OPOLS80tXaTCDsB?si=dLhjUHgWQL-p3MowXQiXJw'
]

DATASET_STR = '''
    https://www.youtube.com/watch?v=u3MX-rUtS6M
    https://www.youtube.com/playlist?list=PLiIiNXduj3VCT5H6Y8Ks2gCLUx0ZlG8Cj
    https://open.spotify.com/playlist/2HhBAqvtxeLmdJBlOlx18l?si=cbea0aa82b274487
    https://open.spotify.com/track/3Vkyy6CB4UDEvFncUBc53z?si=4db5473b9a3d492c
    https://open.spotify.com/album/2d2QJv4OPOLS80tXaTCDsB?si=dLhjUHgWQL-p3MowXQiXJw
'''

CONSTS = ptl.Path(__file__).resolve()  # consts path
LOADLIB = CONSTS.parents[1]  # loadlib root path
os.chdir(LOADLIB)  # cwd
LOADLONG = '[Loadlib     ]'


# config

CFG_PATH = (LOADLIB / 'config').with_suffix('.yaml')


class Yaml(rym.YAML):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.path = CFG_PATH

        if not self.path.exists():
            with open(self.path, mode='x', encoding='UTF-8') as file:
                default = {
                    'sp_appid': '',
                    'sp_secret': '',
                    'settings': {
                        'max_res': ''
                    }
                }
                self.dump(default, self.path)


CFG = Yaml(typ='rt')
