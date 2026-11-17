import sys
from PIL import Image
# usage: stitch.py out.jpg total_h tile1.png tile2.png ...
out, total_h, tiles = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(t).convert("RGB") for t in tiles]
w, th = ims[0].size
canvas = Image.new("RGB", (w, total_h))
for i, im in enumerate(ims):
    canvas.paste(im, (0, i * th))
canvas = canvas.crop((0, 0, w, total_h))
canvas.save(out, quality=88, optimize=True)
print(out, canvas.size)
