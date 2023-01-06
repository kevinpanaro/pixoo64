import qrcode
from PIL import Image, ImageOps

class QRCode():
    def __init__(self, data):
        self.data = data
        self.buffer = []
    
    def generate_image(self):
        qr = qrcode.QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=3,
        )
        qr.add_data(self.data)
        qr.make(fit=True)

        self.img = qr.make_image(fill_color="black", back_color="white")
        print(self.img.size)
    
    def export_buffer(self):
        self.generate_image()
        self.buffer = []
        for x in range(64):
            for y in range(64):
                try:
                    val = self.img.getpixel((x, y))
                except:
                    val = 255
                self.buffer.append(val)
                self.buffer.append(val)
                self.buffer.append(val)
        return self.buffer                      

if __name__ == "__main__":
    qr = QRCode("Hello World")
    qr.generate_image()
    qr.export_buffer()
