from pixoo import Pixoo
from qrpixoo import QRCode
import requests
from io import BytesIO
from haspotify import HASpotify


from PIL import Image, ImageOps
import matplotlib.pyplot as plt

if __name__=="__main__":
    pixoo = Pixoo("192.168.0.154")
    sp = HASpotify(token=None)
    sp_url = sp.album_cover_url()
    pixoo.send_url_image(sp_url)
