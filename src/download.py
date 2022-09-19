# Critical
from threading import Thread  # kivy no freeze
from time import sleep  # debug only for mainloop
import multiprocessing as mp  # multiprocessing

# Processing dependencies
from pytube import YouTube, Playlist  # $ pip install pytube
from pytube.exceptions import PytubeError  # ^
import spotipy  # $ pip install spotipy
from spotipy.oauth2 import SpotifyClientCredentials  # ^
from youtube_search import YoutubeSearch  # $ pip install youtube_search
import ffmpeg  # $ pip install ffmpeg-python

# Vanilla imports
import subprocess  # ffmpeg
import glob  # temp removal
import pathlib as ptl  # pathlib utils (no os path join)
import os  # os
import requests as rq  # request cover art
from time import perf_counter  # performance logging
from typing import Callable  # type hints

# Local imports
try:  # run from root
    from src.consts import LOADLIB, ALLOWED, config_get, LOADLONG  # constants
    from src.logs import Jou  # logs
except ImportError:  # run from main
    from consts import LOADLIB, ALLOWED, config_get, LOADLONG  # constants
    from logs import Jou  # logs

AUTH_MANAGER = SpotifyClientCredentials('36890a0a09594f38894f8d2f48bfc087', config_get(['spotify_secret']))
SPOTIFY = spotipy.Spotify(auth_manager=AUTH_MANAGER)

tempo = ptl.Path(LOADLIB / '.tmp')


class Worker(mp.Process):
    """Worker class for multiprocessing"""

    def __init__(self, task_queue):
        super().__init__()
        self.task_queue = task_queue

    def run(self):
        for (function, *args) in iter(self.task_queue.get, None):
            # Run the provided function with its parameters in child process
            function(*args)

            self.task_queue.task_done()  # <-- Notify queue that task is complete


def tmp():
    if not ptl.Path(tempo).is_dir():
        os.mkdir(tempo)
    for path in glob.glob((str(tempo) + '/*')):
        if ptl.Path(path).is_file():
            os.remove(path)
        else:
            os.rmdir(path)


class Found(Exception):
    pass


class Downloader():
    ALLOWED = ALLOWED

    @classmethod
    def sanitize(cls, string: str, sanitizer: str = ''):
        """File export name sanitizer with fun names

        Args:
            string (str): Input string
            sanitizer (str, optional): What to replace with. Defaults to empty.

        Returns:
            str: Result string

        Special:
            Chars to replace: ['\\', '/', ':', '*', '?', '\'', '<', '>', '|', '\0', '$']
        """
        bacterium = ['\\', '/', ':', '*', '?', '\'', '<', '>', '|', '\0', '$']
        for bacteria in bacterium:
            string = string.replace(bacteria, sanitizer)
        return string

    def start(self, *urls: str, out: str, callme: Callable | None = None):
        """Identifies the inputted URLS as inputs for the processing functions

        Args:
            out (str): Output path

        Raises:
            ValueError: Invalid URL
        """

        dict_q = {k: [] for k in self.ALLOWED.keys()}  # Initialize dictionary

        for url in urls:
            try:  # Little trick that uses exceptions to break out of 2 loops
                for func, v in self.ALLOWED.items():
                    for l in v:
                        if l in url:
                            if '//' not in url:
                                url = f'http://{url}'
                            dict_q[func].append(url)
                            raise Found
                raise ValueError(f'Invalid URL: {url}')
            except Found:
                continue
        MAX_PROC = mp.cpu_count() - 1
        start = perf_counter()
        Jou.info(f'{LOADLONG} Running with {MAX_PROC} processes'
                 )  # last

        workers = []
        manager = mp.Manager()
        task_queue = manager.Queue()

        for _ in range(MAX_PROC):
            worker = Worker(task_queue)
            workers.append(worker)
            worker.start()

        for func, v in dict_q.items():
            for argument in v:
                task_queue.put((getattr(self, func), out, argument, task_queue))

        task_queue.join()

        for _ in workers:
            task_queue.put(None)

        for worker in workers:
            worker.join()

        Jou.info('%s Queue has been processed in %s seconds' % (LOADLONG, (perf_counter() - start),))

        if callme:
            callme()

    @classmethod
    def sp_album(cls, out: str, playlist: str, queue, *args):
        """Adds spotify songs from the specified album to the queue

        Args:
            out (str): Output path
            playlist (str): Playlist URL
            queue (multiprocessing.Queue): Multiprocessing queue
        """
        def get_tracks(url):
            results = SPOTIFY.album_tracks(url)
            tracks = results['items']  # type: ignore
            while results['next']:  # type: ignore
                results = SPOTIFY.next(results)
                tracks.extend(results['items'])  # type: ignore
            return tracks

        for uri in ((song_data['id']) for song_data in get_tracks(playlist)):
            queue.put((cls.sp_song, out, uri, queue))

    @classmethod
    def sp_playlist(cls, out: str, playlist: str, queue, *args):
        """Adds spotify songs from the specified playlist to the queue

        Args:
            out (str): Output path
            playlist (str): Playlist URL
            queue (multiprocessing.Queue): Multiprocessing queue
        """
        def get_tracks(url):
            results = SPOTIFY.playlist_tracks(url)
            tracks = results['items']  # type: ignore
            while results['next']:  # type: ignore
                results = SPOTIFY.next(results)
                tracks.extend(results['items'])  # type: ignore
            return tracks

        for uri in ((song_data['track']['id']) for song_data in get_tracks(playlist)):
            queue.put((cls.sp_song, out, uri, queue))

    @classmethod
    def sp_song(cls, out: str, song: str, *args):
        """Downloads spotify songs via web scraping from youtube

        Args:
            out (str): Output path
            song (str): Spotify song URL/URI

        Raises:
            Exception: General exception
        """
        pid = str(os.getpid())

        try:
            if '/' not in song:
                uri = song.split('/')[-1].split('?')[0]

                # Get spotify track metadata
                track = SPOTIFY.track(uri)
            else:
                track = SPOTIFY.track(song)

            metadata = {
                'track_name': track['name'].replace("'", "").replace('"', ""),  # type: ignore
                'artists': [v['name'].replace("'", "").replace('"', "") for v in track['artists']],  # type: ignore
                'album': track['album']['name'].replace("'", "").replace('"', ""),  # type: ignore
                'release': track['album']['release_date'].replace("'", "").replace('"', ""),  # type: ignore
                'cover': track['album']['images'][0]['url']  # type: ignore
            }

            # Search youtube for song
            Jou.info('%s Loaded song with metadata %s' % (LOADLONG, metadata,))
            query = YoutubeSearch(f'{metadata["artists"][0]} - {metadata["track_name"]}').to_dict()
            Jou.info('%s Found spotify -> YouTube ID %s' % (LOADLONG, query[0]['id']))  # type: ignore
            url = 'https://youtu.be/' + query[0]['id']  # type: ignore
            Jou.info('%s Downloading song %s' % (LOADLONG, metadata['track_name'],))
            cls.yt_video(str(tempo), url, name=pid, sp=True)
            Jou.info('%s Finished downloading song %s' % (LOADLONG, metadata['track_name'],))

            # Cover art processing (probably broken)
            cover_data = rq.get(metadata['cover'], timeout=20).content
            if not cover_data:
                raise Exception('Failed to download cover data')

            with open(str((tempo / pid).with_suffix('.jpeg')), 'wb') as handler:
                handler.write(cover_data)

            # Constants
            output_path = (ptl.Path(out) / cls.sanitize(metadata["artists"]
                           [0] + ' - ' + metadata["track_name"])).with_suffix('.mp3')
            video_input = (tempo / pid).with_suffix('.webm')
            audio_input = (tempo / pid).with_suffix('.mp3')
            cover_input = (tempo / pid).with_suffix('.jpeg')

            # Process 1: MP4 -> MP3
            Jou.info('%s Processing song %s' % (LOADLONG, metadata['track_name'],))
            ffargs_1 = (
                ffmpeg
                .input(filename=video_input, vn=None)
                .output(filename=audio_input, vn=None)
                .overwrite_output()
                .get_args()
            )
            with subprocess.Popen(['ffmpeg'] + ffargs_1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True):
                pass

            # Process 2: MP3 -> MP3 + Metadata
            ffargs_2 = "ffmpeg -i " + '"' + str(audio_input) + '"'
            ffargs_2 += (  # no idea what any of this means
                " -i "
                + '"' + str(cover_input) + '"'
                + ' -map 0:0 -map 1:0  -c copy -id3v2_version 3 -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (front)" -metadata title="'
                + metadata['track_name']
                + '" -metadata artist="'
                + metadata['artists'][0]
                + '" -metadata album="'
                + metadata['album']
                + '" -metadata date="'
                + metadata['release']
                + '"'
                + ' -b:a 320k -vn -y '
                + '"' + str(output_path) + '"'
            )
            with subprocess.Popen(ffargs_2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True):
                pass

            Jou.info('%s Finished processing song %s' % (LOADLONG, metadata['track_name'],))

        except Exception:
            Jou.error('%s Skipped downloading song %s' % (LOADLONG, song,))
        finally:
            for ext in ['.webm', '.jpeg', '.mp3', '.jpeg']:
                if ((tempo / pid).with_suffix(ext)).is_file():
                    os.remove(((tempo / pid).with_suffix(ext)))

    @classmethod
    def yt_playlist(cls, out: str, url: str, queue, *args):
        """Processes youtube playlists into .webm

        Args:
            out (str): Output path
        """
        pl = Playlist(url)
        for x in pl:
            queue.put((cls.yt_video, out, x, queue))
        Jou.info('%s Added yt_playlist %s to queue' % (LOADLONG, pl.title,))

    @classmethod
    def yt_video(cls, out: str, url: str, *args, name: str = '', sp: bool =False):
        """Processes youtube videos into .webm

        Args:
            out (str): Output path
        """
        pid = str(os.getpid())
        try:
            yt = YouTube(url)

            Jou.info('%s Downloading yt_video %s' % (LOADLONG, yt.title,))
            if sp:
                stream = yt.streams.filter(only_audio=True, mime_type='audio/webm').order_by('abr').desc().first()
                if name:
                    stream.download(out, (name + '.webm'))  # type: ignore
                else:
                    stream.download(out, (cls.sanitize(yt.title) + '.mp4'))  # type: ignore
            else:
                stream_vid = yt.streams.filter(adaptive=True, file_extension='mp4',
                                               res='1080p').order_by('fps').desc().first()
                if not stream_vid:
                    stream_vid = yt.streams.filter(adaptive=True, file_extension='mp4',
                                                   res='720p').order_by('fps').desc().first()
                    if not stream_vid:
                        stream_vid = yt.streams.filter(adaptive=True, file_extension='mp4',
                                                       res='480p').order_by('fps').desc().first()
                        if not stream_vid:
                            stream_vid = yt.streams.filter(adaptive=True, file_extension='mp4',
                                                           res='360p').order_by('fps').desc().first()
                        else:
                            raise PytubeError
                stream_aud = yt.streams.filter(adaptive=True, mime_type='audio/mp4').order_by('abr').desc().first()

                stream_vid.download(tempo, (pid + '_vid' + '.mp4'))  # type: ignore
                stream_aud.download(tempo, (pid + '_aud' + '.mp4'))  # type: ignore

                Jou.info('%s Finished downloading yt_video %s' % (LOADLONG, yt.title,))

                ffargs = ('ffmpeg -an -i "'
                          + str(ptl.Path(tempo / (pid + '_vid')).with_suffix('.mp4'))
                          + '" -vn -i "' + str(ptl.Path(tempo / (pid + '_aud')).with_suffix('.mp4'))
                          + '" -acodec copy -vcodec copy -y "'
                          + str(ptl.Path(ptl.Path(out) / cls.sanitize(yt.title)).with_suffix('.mp4'))
                          + '"')

                Jou.info('%s Processing yt_video %s' % (LOADLONG, yt.title,))
                with subprocess.Popen(ffargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True):
                    pass

            Jou.info('%s Finished processing yt_video %s' % (LOADLONG, yt.title,))
        except Exception as e:
            Jou.error('%s Skipped downloading url %s, %s' % (LOADLONG, url, e))

        finally:
            if ptl.Path(tempo / (pid + '_vid')).with_suffix('.mp4').exists():
                os.remove(str(ptl.Path(tempo / (pid + '_vid')).with_suffix('.mp4')))
            if ptl.Path(tempo / (pid + '_aud')).with_suffix('.mp4').exists():
                os.remove(str(ptl.Path(tempo / (pid + '_aud')).with_suffix('.mp4')))


Downloader_inst = Downloader()


if __name__ == '__main__':
    dataset = (
        'https://www.youtube.com/watch?v=-zsV0_QrfTw',
        'https://open.spotify.com/track/4cIPLtg1avt2Jm3ne9S1zy?si=1ee47f420aaf4ae1',
    )
    download = Downloader()
    download.start(*dataset, out='D:/Downloads')
    sleep(1000)
