from urllib.parse import urlparse
from urllib.request import urlopen
import validators as vld
from spotipy import SpotifyException
from pytube import YouTube, Playlist
from pytube.exceptions import PytubeError
try:
    from src.consts import ALLOWED, DATASET
    from src.download import Found, AUTH_MANAGER, SPOTIFY
except:
    from consts import ALLOWED, DATASET
    from download import Found, AUTH_MANAGER, SPOTIFY


class Validator():
    """Probably over-engineered URL validator class"""
    @staticmethod
    def validate(*urls) -> None:
        for url in urls:

            if '//' not in url:
                url = '%s%s' % ('http://', url)

            # Step 1: urlparse
            method_1 = urlparse(url)
            if not all([method_1.scheme, method_1.netloc]):
                raise Exception(f'Exception when testing {url}, using Method 1')

            # Step 2: validators
            method_2 = vld.url(url)  # type: ignore
            if not method_2:
                raise Exception(f'Exception when testing {url}, using Method 2')

            # Step 3: Allowed list
            for key, dom in (tuple([key, domain]) for key, domainlist in ALLOWED.items() for domain in domainlist):
                if dom in url:
                    match key:
                        case 'yt_video':
                            try:
                                if YouTube(url):
                                    return
                                else:
                                    raise PytubeError
                            except PytubeError:
                                pass
                        case 'yt_playlist':
                            try:
                                if Playlist(url):
                                    return
                                else:
                                    raise PytubeError
                            except PytubeError:
                                pass
                        case 'sp_song':
                            try:
                                if SPOTIFY.track(url):
                                    return
                                else:
                                    raise SpotifyException(None, None, None)
                            except SpotifyException:
                                pass
                        case 'sp_album':
                            try:
                                if SPOTIFY.album_tracks(url):
                                    return
                                else:
                                    raise SpotifyException(None, None, None)
                            except SpotifyException:
                                pass
                        case 'sp_playlist':
                            try:
                                if SPOTIFY.playlist_tracks(url):
                                    return
                                else:
                                    raise SpotifyException(None, None, None)
                            except SpotifyException:
                                pass

            raise Exception(f'Invalid URL: {url}')


if __name__ == '__main__':
    from time import perf_counter
    for data in DATASET:
        curr = perf_counter()
        Validator.validate(data)
        print(f'{data} elapsed: {perf_counter() - curr}')
