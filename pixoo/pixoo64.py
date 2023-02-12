from pixoo import Pixoo64
from qrpixoo import QRCode
from haspotify import HASpotify


def pixoo64():
    # create Pixoo object
    pixoo = Pixoo64("192.168.0.154")

    # Home Assistant Spotify Example
    haspotify = HASpotify()
    img_url = haspotify.album_cover_url()
    pixoo.send_url_image(img_url)

    # QR Code Example
    qrcode = QRCode()
    buffer = qrcode.add_string("Hello World")
    pixoo.set_buffer(buffer)
    pixoo.send_image()


if __name__ == "__main__":
    pixoo64()
