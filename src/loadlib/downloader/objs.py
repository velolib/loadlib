'''
Classes with the same title api as pytube for consistency.
'''

from dataclasses import dataclass

from loadlib.exceptions import DownloaderException
from spotipy import Spotify, SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOauthError


class SpotifyAPI:
    def __init__(self, url, auth_manager) -> None:
        sp = Spotify(auth_manager=auth_manager)
        self.track = sp.track(url)
        self.title = self.track['name']


class SpotifyPlaylistAPI:
    def __init__(self, url, auth_manager) -> None:
        sp = Spotify(auth_manager=auth_manager)
        results = sp.playlist(url, fields='tracks,items,name,uri')
        tracks = results['tracks']
        items = tracks['items']
        while tracks['next']:
            tracks = sp.next(tracks)
            items.extend(tracks['items'])
        self.tracks = items
        self.urls = [t['track']['external_urls']['spotify'] for t in self.tracks]
        self.title = results['name']


class SpotifyAlbumAPI:
    def __init__(self, url, auth_manager) -> None:
        sp = Spotify(auth_manager=auth_manager)
        results = sp.album(url)
        tracks = results['tracks']
        items = tracks['items']
        while tracks['next']:
            tracks = sp.next(tracks)
            items.extend(tracks['items'])
        self.tracks = items
        self.urls = [t['external_urls']['spotify'] for t in self.tracks]
        self.title = results['name']

class TikTokAPI:
    pass


def main():
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    test = SpotifyAlbumAPI('https://open.spotify.com/album/0ETFjACtuP2ADo6LFhL6HN?si=AL6OwFFCSP-qqajKHTMSbQ', SpotifyClientCredentials('a', 'a'))
    print(test.tracks)
    print(test.urls)
    print(test.title)


if __name__ == '__main__':
    main()
