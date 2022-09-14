from threading import Thread
from time import sleep
from pytube import YouTube, Playlist
import logging as Jou
import multiprocessing as mp
from itertools import repeat
from logs import Jou
import spotipy
from os import environ

environ['SPOTIPY_CLIENT_ID'] = '36890a0a09594f38894f8d2f48bfc087'

ALLOWED = {
    'youtube.com/playlist': 'yt_playlist',
    'youtube.com/watch': 'yt_video',
    'youtu.be/': 'yt_video',
    'open.spotify.com/track': 'sp_song',
    'open.spotify.com/album': 'sp_album',
    'open.spotify.com/playlist': 'sp_playlist',
}


class Downloader():
    
    @classmethod
    def start(cls, *urls: str, out: str) -> None:
        """Starts the main download fybctuib ib a dufferebt thread

        Args:
            out (str): Output path
        """
        cls.DownThread = Thread(name='DownThread', daemon=True, target=lambda: cls._start(*urls, out=out))
        cls.DownThread.start()
        if cls.DownThread.is_alive():
            Jou.info(f'[Loadlib     ] Thread {cls.DownThread} initialized')
        else:
            Jou.critical(f'[Loadlib     ] Thread {cls.DownThread} failed to initialize')
    
    @classmethod
    def _start(cls, *urls: str, out: str):
        """Identifies the inputted URLS as inputs for the processing functions

        Args:
            out (str): Output path

        Raises:
            ValueError: Invalid URL
        """
        
        queue = {v: [] for v in ALLOWED.values()} # Initialize dictionary
        
        for url in urls:
            for k, v in ALLOWED.items():
                if k in url:
                    queue[v].append(url)
                    break
            else:
                raise ValueError(f'Invalid URL: {url}')
        else:
            with mp.Pool(processes=3) as pool:
                Jou.info(f'[Loadlib     ] Queue starting processing')
                yt_playlist = pool.starmap_async(cls.yt_playlist, zip(repeat(out, len(queue['yt_playlist'])), queue['yt_playlist']))
                yt_video = pool.starmap_async(cls.yt_video, zip(repeat(out, len(queue['yt_video'])), queue['yt_video']))
                yt_playlist.wait()
                yt_video.wait()
                Jou.info(f'[Loadlib     ] Queue has been processed')
    
    @classmethod
    def sp_song(cls, out: str, *urls: str):
        for song in urls:
            pass

    @classmethod
    def yt_playlist(cls, out: str, *urls: str):
        """Processes youtube playlists into .mp4

        Args:
            out (str): Output path
        """
        for url in urls:
            pl = Playlist(url)
            Jou.info(f'[Loadlib     ] Downloading yt_playlist {pl.title}')
            cls.yt_video(out, *pl)
            Jou.info(f'[Loadlib     ] Finished downloading yt_playlist {pl.title}')
    
    @classmethod
    def yt_video(cls, out: str, *urls: str):
        """Processes youtube videos into .mp4

        Args:
            out (str): Output path
        """
        for url in urls:
            yt = YouTube(url)
            Jou.info(f'[Loadlib     ] Downloading yt_video {yt.title}')
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            stream.download(out) # type: ignore
            Jou.info(f'[Loadlib     ] Finished downloading yt_video {yt.title}')

if __name__ == '__main__':
    Downloader.start('https://youtu.be/NrLkTZrPZA4', 'https://www.youtube.com/watch?v=1u28CwLtrW0', 'https://www.youtube.com/watch?v=Q6GpvdY4cN8&ab_channel=WetLeg', 'https://www.youtube.com/playlist?list=PLiIiNXduj3VCT5H6Y8Ks2gCLUx0ZlG8Cj', out='D:/Downloads')
    sleep(100)
