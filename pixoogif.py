from PIL import Image

with Image.open("meme.gif") as im:
    try:
        while True:
            im.seek(im.tell() + 1)
            small = im.resize((64,64), Image.Resampling.BILINEAR)
            print(small.size)
            print(small.getpixel((0,0)))
    except:
        pass

