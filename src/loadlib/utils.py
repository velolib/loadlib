import ntpath
import operator
import os
import posixpath
import re
from collections import Counter
from functools import reduce
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


def get_valid_filename(value: Any) -> str:
    """
    Returns a valid filename from any string-able type
    """
    s = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", value)
    if s in {'', '.', '..'}:
        raise Exception(f'Could not derive file name from \'{value}\'')
    return s


def get_duplicates(_list: list):
    c = Counter(_list)
    return [k for k in c if c[k] > 1]


def dot_path(pth):
    """
    Return path str that may start with '.' if relative.
    From https://stackoverflow.com/questions/62687193/how-to-create-a-pathlib-relative-path-with-a-dot-starting-point
    """
    if pth.is_absolute():
        return os.fsdecode(pth)
    if isinstance(pth, PureWindowsPath):
        return ntpath.join(".", pth)
    elif isinstance(pth, PurePosixPath):
        return posixpath.join(".", pth)
    else:
        return os.path.join(".", pth)


def get_by_path(root: list, key_path: list | tuple):
    """Access a nested object in root by key path sequence."""
    return reduce(operator.getitem, key_path, root)


def set_by_path(root: list, key_path: list | tuple, value):
    """Set a value in a nested object in root by key path sequence."""
    get_by_path(root, key_path[:-1])[key_path[-1]] = value


def main():
    print(type(dot_path(PureWindowsPath('assets/youtube.png'))))


if __name__ == '__main__':
    main()
