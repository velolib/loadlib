'''
Loadlib entry point referenced by pyinstaller
What runs on start:
1. Creates .loadlib directory at the user's home directory
2. Removes all temporary folders created by Loadlib
3. Starts the program
'''
import os
from multiprocessing import current_process

os.environ['KIVY_NO_FILELOG'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'

if current_process().name == 'MainProcess':  # TODO: Find out if this is necessary
    import pathlib as ptl
    import tempfile
    from sys import stderr

    from loguru import logger

    from loadlib.const import LOADLIB
    from loadlib.ui.ui import UIApp

    logger.remove()
    logger.add(stderr, level='INFO')
    logger.add(LOADLIB / '{time:YYYY_MM_DD}.log', level='DEBUG', retention=5, backtrace=True, diagnose=True, enqueue=True)

    if not LOADLIB.exists():
        LOADLIB.mkdir()

    def rmtree(root: ptl.Path):
        for p in root.iterdir():
            if p.is_dir():
                rmtree(p)
            else:
                p.unlink()
        root.rmdir()

    try:
        ll_temp = ptl.Path(tempfile.gettempdir()).glob('ll_*/')
        for tempo in ll_temp:
            rmtree(tempo)
    except PermissionError as pr:
        logger.critical('Could not clear temp directory')
        logger.exception(pr)

    try:
        UIApp().run()
    except Exception as e:
        logger.error('An exception has occured that has stopped the application')
        logger.exception(e)
        raise e
