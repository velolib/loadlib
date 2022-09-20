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
                raise Exception(
                    f'Exception when testing {url}, using Method 1')

            # Step 2: validators
            method_2 = vld.url(url)  # type: ignore
            if not method_2:
                raise Exception(
                    f'Exception when testing {url}, using Method 2')

            # Step 3: Allowed list
            for key, dom in (tuple([key, domain]) for key, domainlist in ALLOWED.items() for domain in domainlist):
                if dom in url:
                    match key:
                        case 'yt_video':
                            if YouTube(url):
                                continue
                            else:
                                raise PytubeError
                        case 'yt_playlist':
                            if Playlist(url):
                                continue
                            else:
                                raise PytubeError
                        case 'sp_song':
                            if SPOTIFY.track(url):
                                continue
                            else:
                                raise SpotifyException(None, None, None)
                        case 'sp_album':
                            if SPOTIFY.album_tracks(url):
                                continue
                            else:
                                raise SpotifyException(None, None, None)
                        case 'sp_playlist':
                            if SPOTIFY.playlist_tracks(url):
                                continue
                            else:
                                raise SpotifyException(None, None, None)


if __name__ == '__main__':
    from time import perf_counter
    for data in DATASET:
        curr = perf_counter()
        Validator.validate('https://open.spotify.com/playlist/2q24Rnws1dMyU7nP9DSouk?si=17e0b77e56d04d88&pt=b6bfccd967f3d2fa1f2a77ec2cf81240')
        print(f'{data} elapsed: {perf_counter() - curr}')
