import os
import pathlib as ptl
from enum import Enum

LOADLIB: ptl.Path = ptl.Path.home() / '.loadlib'  # loadlib path

class Resolutions(str, Enum):
    """
    Enum of valid resolutions
    """
    unlimited = 'Unlimited'
    p1080 = '1080p'
    p720 = '720p'
    p480 = '480p'
    p360 = '360p'
    p240 = '240p'
    p144 = '144p'

DATASET_ALL = ['https://www.youtube.com/watch?v=w4sLAQvEH-M&ab_channel=Veritasium', # Regular video
               'https://www.youtube.com/shorts/09xooQuwIlM', # Shorts video
               'https://www.youtube.com/playlist?list=PLiIiNXduj3VCT5H6Y8Ks2gCLUx0ZlG8Cj', # Playlist containing video and music video
               'https://open.spotify.com/track/1sGsgVBJSifmec6B7Y7bL6?si=ce58229c8d8b488b', # Singular track
               'https://open.spotify.com/playlist/2HhBAqvtxeLmdJBlOlx18l?si=a8afe67ba11c4a1b', # Test playlist
               'https://open.spotify.com/album/3imHE6OIlJzzmJEOZE8JsI?si=O72jKEb8Sja-jqdX4tzTlw', # Album
               'https://raw.githubusercontent.com/velolib/No-More-Games/main/assets/XMG_Logo-text.png', # Web image
               'https://www.gstatic.com/webp/gallery/4.webp' # webp
               ]

''' Copy this to link box to test
https://www.youtube.com/watch?v=w4sLAQvEH-M&ab_channel=Veritasium
https://www.youtube.com/shorts/09xooQuwIlM
https://www.youtube.com/playlist?list=PLiIiNXduj3VCT5H6Y8Ks2gCLUx0ZlG8Cj
https://open.spotify.com/track/1sGsgVBJSifmec6B7Y7bL6?si=ce58229c8d8b488b
https://open.spotify.com/playlist/2HhBAqvtxeLmdJBlOlx18l?si=a8afe67ba11c4a1b
https://open.spotify.com/album/3imHE6OIlJzzmJEOZE8JsI?si=O72jKEb8Sja-jqdX4tzTlw
https://raw.githubusercontent.com/velolib/No-More-Games/main/assets/XMG_Logo-text.png
https://www.gstatic.com/webp/gallery/4.webp
'''

DATASET_YYP = ['https://www.youtube.com/watch?v=jRlsS4-IXBo&ab_channel=MogulMail', 'https://www.youtube.com/watch?v=w4sLAQvEH-M&ab_channel=Veritasium',
               'https://www.youtube.com/playlist?list=PLiIiNXduj3VCT5H6Y8Ks2gCLUx0ZlG8Cj']
DATASET_YYY = ['https://www.youtube.com/watch?v=2ejbLVkCndI&ab_channel=ArjanCodes', 'https://www.youtube.com/watch?v=IKD2-MAkXyQ',
               'https://www.youtube.com/watch?v=-zsV0_QrfTw']