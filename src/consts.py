import io
try:  # run from root
    from src.logs import Jou
except ImportError:  # run from main
    from logs import Jou
import os
import pathlib as ptl
import yaml
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

CONSTS = ptl.Path(__file__).resolve()
LOADLIB = CONSTS.parents[1]
PTL_LOADLIB = ptl.Path(LOADLIB)
os.chdir(LOADLIB)
CONFIG_PATH = (PTL_LOADLIB / 'config').with_suffix('.yaml')
STANDARD_CONFIG = {
    'spotify_secret': '',
    'settings':
        {
            'mode': 'dark',
        }
}
LOADLONG = '[Loadlib     ]'

if not os.path.exists(CONFIG_PATH):
    with io.open(CONFIG_PATH, 'w', encoding='UTF-8') as ymfile:
        Jou.info('%s')
        yaml.dump(STANDARD_CONFIG, ymfile, default_flow_style=False, allow_unicode=True, sort_keys=False)

with open(CONFIG_PATH, encoding='UTF-8') as config:
    CONFIG_DATA = yaml.safe_load(config)


def config_get(key_path: list[str] | None = None) -> str:
    """Reads the config.yaml file and returns the value from the path

    Args:
        key_path (list[str]): Dictionary key sequence, ex: ['settings', 'mode']

    Returns:
        str: Value of the specified key
    """
    if key_path:
        return reduce(getitem, key_path, CONFIG_DATA)
    return CONFIG_DATA
