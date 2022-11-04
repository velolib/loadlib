
import json
import pathlib as ptl
from functools import reduce

from loguru import logger
from ruamel.yaml import YAML
from schema import And, Or, Schema, SchemaError

from loadlib.const import LOADLIB, Resolutions
from loadlib.utils import get_by_path, set_by_path

default = {
    'settings': {
        'max_res': '1080p',
        'threads': 1,
        'sp_appid': '',
        'sp_secret': ''
    },
    'debug': False
}

config_schema = Schema(
    {
        'settings': {
            'max_res': Or(*[i.value for i in Resolutions]),
            'threads': And(int, lambda n: 0 < n <= 5),
            'sp_appid': Or(str, None),
            'sp_secret': Or(str, None)
        },
        'debug': bool
    }
)


CFG_PATH: ptl.Path = (LOADLIB / 'config').with_suffix('.yaml')


class CONFIG(YAML):
    """Global singleton yaml class"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.path = CFG_PATH
        if self.path.exists():
            try:
                datadict = self.load(self.path)
                config_schema.validate(datadict)
            except SchemaError:
                logger.error('Config file deprecated. Generating new config file')
                self.regen()
        else:
            logger.error('Config file does not exist. Generating new config file')
            self.regen()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({json.dumps(self.load(self.path))})'

    def regen(self):
        """
        Regenerates the configuration file
        """
        with self.path.open(mode='w+') as file:
            self.dump(default, file)

    def get(self, key_path: list | tuple | None = None) -> str:
        """
        Get config value by key path

        Args:
            key_path (list | tuple | None, optional): Dictionary key path in form of list. Defaults to None.

        Returns:
            str: Returns value of key, if key_path is none returns whole dictionary
        """
        load = self.load(self.path)
        if not key_path:
            return load
        return get_by_path(load, key_path)

    def set(self, key_path: list | tuple, value: str | int | bool | float):
        """
        Set config value by key path

        Args:
            key_path (list | tuple): Dictionary key path in form of list or tuple
            value (str): Value
        """
        load = self.load(self.path)
        set_by_path(load, key_path, value)
        self.dump(load, self.path)


YAML = CONFIG(typ='rt')


def main():
    print(YAML.get(['settings', 'sp_appid']))


if __name__ == '__main__':
    main()
