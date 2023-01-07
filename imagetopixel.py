from PIL import Image
import matplotlib.pyplot as plt

img = Image.open('album640.jpg')
small = img.resize((64,64), Image.BILINEAR)
small.getpixel((0,0))
print(dir(small))