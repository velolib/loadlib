import pathlib as ptl
import subprocess
import tempfile as tmp
import requests
from urllib.parse import urlparse, unquote
from urllib.error import URLError
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from os import getpid
from typing import Any, Callable, Generator

import loadlib.downloader.objs as objs
import youtube_search as yt_search
from loadlib.const import Resolutions
from loadlib.exceptions import DownloaderException
from loadlib.utils import dot_path, get_valid_filename
from loguru import logger
from pytube import Playlist, YouTube
from pytube.exceptions import PytubeError
from pytube.streams import Stream
from spotipy import SpotifyException, SpotifyClientCredentials, SpotifyOauthError


class ImplementedURL(ABC):

    def __init__(self, url) -> None:
        self.url = url
        self.obj = None

    @abstractmethod
    def task(self):
        pass

    @abstractmethod
    def download(self):
        pass


@dataclass(slots=True)
class Task:
    """
    Function wrapper with defined kwargs, and kwargs only

    Args:
        func (Callable): Any callable
        kwargs (dict): Callable's arguments

    Returns:
        Any: Whatever the specified function returns
    """
    func: Callable
    kwargs: dict

    def __iter__(self):
        return iter((self.func, self.kwargs))

    def __call__(self) -> Any:
        result = self.func(**self.kwargs)
        return result


@dataclass(slots=True)
class DownloadReturn:
    """
    Download return class
    """

    @dataclass(slots=True)
    class Result:
        code: bool
        self: Any
        title: str

    key: Any
    result: dict

    def __post_init__(self):
        self.result = self.Result(**self.result)


class YoutubeVideo(ImplementedURL):
    """
    YouTube Video class
    """
    valid_url = ('youtube.com/', 'youtu.be')
    max = [e for e in Resolutions]
    logo_path = dot_path(ptl.Path('assets/youtube.png'))

    def __init__(self, url: str, **_) -> None:
        super().__init__(url)
        try:
            self.obj = YouTube(url)
            if not self.obj.length:
                raise DownloaderException('Video not available: Not allowed')
            self.title = self.obj.title

        except PytubeError as e:
            raise DownloaderException(f'Pytube video not available: {e}')
        except TypeError as e:
            if str(e) == 'int() argument must be a string, a bytes-like object or a real number, not \'NoneType\'':
                raise DownloaderException('Video not available: Not allowed')
            else:
                raise e

    def task(self, output: ptl.Path, max_res: Resolutions = Resolutions.unlimited, **_) -> Generator[Task, None, None]:
        """
        Returns a singular generator containing a Task object (for consistency)
        Args:
            url (str): Valid YouTube video URL
            output (pathlib.Path): Output path
            max_res (Resolutions, optional): Maximum resolution to download. Defaults to Unlimited.

        Returns:
            Generator[Task, None, None]: Generator containing a Task object
        """
        return (x for x in (Task(self.download, {'output': output, 'max_res': max_res}),))

    def download(self, output: ptl.Path, max_res: Resolutions = Resolutions.unlimited, **_) -> DownloadReturn:
        """
        Downloads a youtube video with specified settings

        Args:
            output (pathlib.Path): Output path
            max_res (Resolutions, optional): Maximum resolution to download. Defaults to Unlimited.

        Raises:
            DownloaderException: Exception when downloading

        Returns:
            TaskReturn: Task return object. See class definition
        """
        try:
            logger.info(f'Starting process for {self.title}')
            pid = str(getpid())  # unique-ish filename
            yt = self.obj

            match max_res:
                case Resolutions.unlimited:
                    stream_vid = (
                        yt
                        .streams
                        .filter(adaptive=True, file_extension='mp4')
                        .order_by('resolution')
                        .desc()
                        .first()
                    )
                case _:
                    stream_vid = self.get_vid_stream(yt, max_res)

            if stream_vid.filesize > 1e9:
                raise DownloaderException('Loadlib does not support video files larger than 1 GB')

            logger.info(f'Found youtube video stream for {self.title} {stream_vid}')

            stream_aud = (
                yt
                .streams
                .filter(adaptive=True, mime_type='audio/mp4')
                .order_by('abr')
                .desc()
                .first()
            )
            logger.info(f'Found youtube audio stream for {self.title} {stream_aud}')

            with tmp.TemporaryDirectory(prefix='ll_') as tmpdir:
                logger.info(f'Created temporary directory at {tmpdir}')
                logger.info(f'Downloading youtube video \'{self.title}\' at {tmpdir}')

                stream_aud.download(tmpdir, pid + '_aud.mp4', skip_existing=False)
                stream_vid.download(tmpdir, pid + '_vid.mp4', skip_existing=False)

                logger.info(f'Processing youtube video \'{self.title}\'')

                ffargs = ('ffmpeg -y -an -i '
                          + f'"{ptl.Path(tmpdir) / ptl.Path(pid + "_vid")}.mp4" '
                          + '-vn -i '
                          + f'"{ptl.Path(tmpdir) / ptl.Path(pid + "_aud")}.mp4" '
                          + '-acodec copy -vcodec copy -y '
                          + f'"{output / stream_vid.default_filename}"')

                with subprocess.Popen(ffargs, stderr=subprocess.PIPE, universal_newlines=True) as spr:
                    for line in spr.stderr:
                        logger.debug(line)

                logger.info(f'Processed youtube video \'{self.title}\' at {output}')
                return DownloadReturn(self.url, {'self': self, 'code': True, 'title': self.title})
        except (PytubeError, DownloaderException) as e:
            logger.exception(e)
            return DownloadReturn(self.url, {'self': self, 'code': False, 'title': self.title})

    def get_vid_stream(self, yt: YouTube, max_res: Resolutions) -> Stream:
        """
        Returns a video stream recursively to find the maximum resolution allowed to download

        Args:
            yt (YouTube): Pytube YouTube object
            max_res (Resolutions): Maximum video resolution

        Raises:
            DownloadError: No stream found

        Returns:
            Stream: Pytube stream object
        """
        stream = yt.streams.filter(adaptive=True, file_extension='mp4', res=max_res.value).order_by('fps').first()
        if stream:
            return stream
        else:
            try:
                ret = self.get_vid_stream(yt, self.max[self.max.index(max_res) + 1])
                return ret
            except IndexError:
                raise DownloaderException(f'No stream found for url {yt.watch_url}')


class YoutubePlaylist(YoutubeVideo):
    """
    YouTube Playlist class
    """
    valid_url = ('youtube.com/playlist',)

    def __init__(self, url, **_) -> None:
        try:
            self.url = url
            self.obj = Playlist(url)
            self.title = self.obj.title
        except PytubeError as e:
            raise DownloaderException(f'Video not available: {e}')

    def task(self, output: ptl.Path, max_res: Resolutions = Resolutions.unlimited, **_) -> Generator[Task, None, None]:
        """
        Returns a generator of Task objects to download the videos of this playlist

        Args:
            url (str): Valid YouTube playlist URL
            output (pathlib.Path): Output path
            max_res (Resolutions, optional): Maximum resolution to download. Defaults to Unlimited.

        Returns:
            Generator[Task, None, None]: Generator of Task objects
        """
        try:
            ytp = Playlist(self.url)
            return (x for yt in ytp.video_urls for x in YoutubeVideo(yt).task(output=output, max_res=max_res))
        except PytubeError:
            raise DownloaderException(f'Invalid URL: {self.url}')


class SpotifySong(ImplementedURL):
    valid_url = ('open.spotify.com/track',)
    logo_path = dot_path(ptl.Path('assets/spotify.png'))

    def __init__(self, url: str, auth_manager, **_) -> None:
        try:
            self.url = url
            self.auth_manager = auth_manager
            self.obj = objs.SpotifyAPI(url, auth_manager)
            self.title = self.obj.title
        except SpotifyOauthError:
            raise DownloaderException('Invalid spotify credentials')
        except SpotifyException as e:
            raise DownloaderException(str(e))

    def task(self, output: ptl.Path, **_) -> Generator[Task, None, None]:
        """
        Returns a singular generator containing a Task object (for consistency)
        Args:
            url (str): Valid YouTube video URL
            output (pathlib.Path): Output path
            max_res (Resolutions, optional): Maximum resolution to download. Defaults to Unlimited.

        Returns:
            Generator[Task, None, None]: Generator containing a Task object
        """
        return (x for x in (Task(self.download, {'output': output}),))

    def download(self, output: ptl.Path, max_results: int = 3, **_) -> DownloadReturn:
        """
        Downloads this spotify song via youtube

        Args:
            output (pathlib.Path): Output path
            max_results (int, optional): Maximum results to account for in the youtube search. Defaults to 3. (You should not change this)

        Returns:
            TaskReturn: Task return object. See class definition
        """
        try:
            logger.info(f'Starting process for {self.title}')
            track = self.obj.track
            metadata = {
                'track_name': track['name'].replace("'", "").replace('"', ""),
                'artists': [v['name'].replace("'", "").replace('"', "") for v in track['artists']],
                'album': track['album']['name'].replace("'", "").replace('"', ""),
                'release': track['album']['release_date'].replace("'", "").replace('"', ""),
            }

            # TODO: Better search algorithm
            # 1. Prioritize 'Topic' channels
            # 2. Prioritize official channels
            # 3. Viewcount maybe?

            # Search youtube for song
            logger.info(f'Searching youtube for song {self.title}')
            search = f'{metadata["artists"][0]} - {metadata["track_name"]} {metadata["album"]} (Audio)'
            logger.debug(f'Searching youtube with key \'{search}\'')
            query = yt_search.YoutubeSearch(
                search, max_results=max_results).to_dict()

            # Filter: Length
            logger.info(f'Filtering results for song {self.title}')
            lengths = {YouTube(('https://youtu.be/' + x['id'])).length: x['id'] for x in query}
            filtered_id = lengths[(min(lengths, key=lambda x:abs(x - (track['duration_ms'] // 1000))))]

            url = 'https://youtu.be/' + filtered_id
            logger.info(f'Found spotify -> youtube URL for {self.title}: {url}')

            yt = YouTube(url)
            stream = (
                yt
                .streams
                .filter(adaptive=True, mime_type='audio/mp4')
                .order_by('abr')
                .desc()
                .first()
            )
            logger.info(f'Found spotify audio stream for {self.title} {stream}')

            with tmp.TemporaryDirectory(prefix='ll_') as tmpdir:
                logger.info(f'Created temporary directory at {tmpdir}')
                pid = str(getpid())

                logger.info(f'Downloading spotify song \'{self.title}\' at {tmpdir}')
                stream.download(tmpdir, f'{pid}_spotify.mp4', skip_existing=False)

                logger.info(f'Processing spotify song \'{self.title}\' at {output}')
                ffargs_convert = (
                    'ffmpeg '
                    + '-y -vn -i '
                    + f'"{ptl.Path(tmpdir) / f"{pid}_spotify.mp4"}" '
                    + f'"{ptl.Path(tmpdir) / f"{pid}_processed.mp3"}"'
                )

                with subprocess.Popen(ffargs_convert, stderr=subprocess.PIPE, universal_newlines=True) as spr:
                    for line in spr.stderr:
                        logger.debug(line)

                ffargs_metadata = (
                    'ffmpeg '
                    + '-y -i '
                    + f'"{ptl.Path(tmpdir) / f"{pid}_processed.mp3"}" '
                    + '-c copy '
                    + f'-metadata title="{metadata["track_name"]}" '
                    + f'-metadata artist="{metadata["artists"][0]}" '
                    + f'-metadata album="{metadata["album"]}" '
                    + f'-metadata date="{metadata["release"]}" '
                    + f'"{output / (get_valid_filename(self.title) + ".mp3")}"'
                )
                with subprocess.Popen(ffargs_metadata, stderr=subprocess.PIPE, universal_newlines=True) as spr:
                    for line in spr.stderr:
                        logger.debug(line)
                logger.info(f'Processed spotify song \'{self.title}\' at {output}')
            return DownloadReturn(self.url, {'self': self, 'code': True, 'title': self.title})
        except (PytubeError, SpotifyException, subprocess.SubprocessError) as e:
            logger.exception(e)
            return DownloadReturn(self.url, {'self': self, 'code': False, 'title': self.title})


class SpotifyPlaylist(SpotifySong):
    valid_url = ('open.spotify.com/playlist',)

    def __init__(self, url: str, auth_manager, **_) -> None:
        try:
            self.url = url
            self.auth_manager = auth_manager
            self.obj = objs.SpotifyPlaylistAPI(url, auth_manager)
            self.title = self.obj.title
        except SpotifyOauthError:
            raise DownloaderException('Invalid spotify credentials')
        except SpotifyException as e:
            raise DownloaderException(str(e))

    def task(self, output: ptl.Path, max_results: int = 3, **_) -> Generator[Task, None, None]:
        """
        Returns a generator of tasks to download this playlist's items

        Args:
            output (pathlib.Path): Output path
            max_results (int, optional): Maximum results to account for in the youtube search. Defaults to 3. (You should not change this)

        Returns:
            Generator[Task, None, None]: Generator of Task objects
        """
        try:
            return (x for sp in self.obj.urls for x in SpotifySong(sp, self.auth_manager).task(output=output, max_results=max_results))
        except SpotifyException:
            raise DownloaderException(f'Invalid URL: {self.url}')


class SpotifyAlbum(SpotifySong):
    valid_url = ('open.spotify.com/album',)

    def __init__(self, url: str, auth_manager, **_) -> None:
        try:
            self.url = url
            self.auth_manager = auth_manager
            self.obj = objs.SpotifyAlbumAPI(url, auth_manager)
            self.title = self.obj.title
        except SpotifyOauthError:
            raise DownloaderException('Invalid spotify credentials')
        except SpotifyException as e:
            raise DownloaderException(str(e))

    def task(self, output: ptl.Path, max_results: int = 3, **_):
        """
        Returns a generator of tasks to download this albums's items

        Args:
            output (pathlib.Path): Output path
            max_results (int, optional): Maximum results to account for in the youtube search. Defaults to 3. (You should not change this)

        Returns:
            Generator[Task, None, None]: Generator of Task objects
        """
        try:
            return (x for sp in self.obj.urls for x in SpotifySong(sp, self.auth_manager).task(output=output, max_results=max_results))
        except SpotifyException:
            raise DownloaderException(f'Invalid URL: {self.url}')


class RequestURL(ImplementedURL):
    logo_path = dot_path(ptl.Path('/assets/url.png'))

    def __init__(self, url, **_) -> None:
        self.url = url

        try:
            hdrs = {
                'User-Agent': 'github/velolib/loadlib'
            }
            response = requests.head(url, allow_redirects=False, headers=hdrs)
            if 'Content-Type' not in response.headers.keys():
                raise DownloaderException('Invalid URL')
            filename = ptl.Path(urlparse(url).path)
            self.title = unquote(filename.stem + filename.suffix)
        except (requests.exceptions.RequestException, URLError) as e:
            raise DownloaderException(e)

    def download(self, output: ptl.Path, **_):
        try:
            logger.info(f'Downloading {RequestURL.__name__} {self.url} at {output}')
            with requests.get(self.url, stream=True) as r:
                r.raise_for_status()
                with open(output / (get_valid_filename(self.title)), 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f'Downloaded {RequestURL.__name__} {self.url} at {output}')
            return DownloadReturn(self.url, {'self': self, 'code': True, 'title': self.title})
        except (requests.exceptions.RequestException, OSError) as e:
            logger.exception(e)
            (output / get_valid_filename(self.title)).unlink(missing_ok=True)
            return DownloadReturn(self.url, {'self': self, 'code': False, 'title': self.title})


    def task(self, output: ptl.Path, **_):
        return (x for x in (Task(self.download, {'output': output}),))


class ValidEnum(Enum):
    yt_playlist = YoutubePlaylist
    yt_video = YoutubeVideo
    sp_song = SpotifySong
    sp_album = SpotifyAlbum
    sp_playlist = SpotifyPlaylist


def LinkFactory(url: str, sp_appid=None, sp_secret=None, **_) -> ImplementedURL:
    if not sp_appid:
        sp_appid = 'placeholder'
    if not sp_secret:
        sp_secret = 'placeholder'

    try:
        auth_manager = SpotifyClientCredentials(sp_appid, sp_secret, cache_handler=False)
    except (SpotifyException, SpotifyOauthError):
        print(sp_appid, sp_secret)
        raise DownloaderException('Invalid spotify credentials')

    for link in ValidEnum:
        for valid_url in link.value.valid_url:
            if valid_url in url:
                ret = link.value(url=url, auth_manager=auth_manager)
                return ret
    return RequestURL(url)


def main():
    from loadlib.const import DATASET_ALL
    from spotipy import SpotifyClientCredentials, Spotify
    from os import environ
    yup = LinkFactory('https://cdn.modrinth.com/data/P7dR8mSH/versions/9nx74dYD/fabric-api-0.64.0%2B1.19.2.jar')
    rest = yup.download(ptl.Path('D:/Downloads'))
    print(rest)


if __name__ == '__main__':
    main()
