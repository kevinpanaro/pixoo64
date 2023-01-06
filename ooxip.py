from pixoo import Pixoo
from qrpixoo import QRCode

if __name__=="__main__":
    pixoo = Pixoo("192.168.0.154")
    qr = QRCode("shortcuts://run-shortcut?name=Travel")
    buffer = qr.export_buffer()
    pixoo.buffer_set(buffer)
    pixoo.send_image()