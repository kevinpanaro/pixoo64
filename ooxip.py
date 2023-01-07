from pixoo import Pixoo64
from qrpixoo import QRCode
import requests
from io import BytesIO
from haspotify import HASpotify


from PIL import Image, ImageOps
import matplotlib.pyplot as plt

if __name__=="__main__":
    pixoo = Pixoo64("192.168.0.154")
    sp = HASpotify()
    sp_url = sp.album_cover_url()
    pixoo.send_url_image(sp_url)

    # qr = QRCode()
    # buffer = qr.add_string("Hello World")
    # pixoo.buffer_set(buffer)
    # pixoo.send_image()