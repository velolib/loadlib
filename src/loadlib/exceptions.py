

class LoadlibException(Exception):
    """
    Custom Loadlib exception class
    """
    pass


class DownloaderException(LoadlibException):
    """
    Custom Loadlib exception class for the downloader module
    """
    pass


class UIException(LoadlibException):
    """
    Custom Loadlib exception class for the UI
    """
    pass
