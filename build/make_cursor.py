#!/usr/bin/env python3
"""Draw the pointer and click-ring sprites the video overlays for the click-through scene."""
import os
from PIL import Image, ImageDraw
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'sprites')
os.makedirs(OUT, exist_ok=True)

# pointer: the usual arrow, white fill with a dark outline so it reads on any background
W, H = 44, 62
cur = Image.new('RGBA', (W * 4, H * 4), (0, 0, 0, 0))
d = ImageDraw.Draw(cur)
arrow = [(6, 4), (6, 152), (44, 116), (68, 176), (96, 164), (72, 106), (124, 104)]
d.polygon([(x, y) for x, y in arrow], fill=(255, 255, 255, 255), outline=(22, 32, 43, 255))
d.line([(x, y) for x, y in arrow] + [arrow[0]], fill=(22, 32, 43, 255), width=7, joint='curve')
cur = cur.resize((W, H), Image.LANCZOS)
cur.save(os.path.join(OUT, 'cursor.png'))

# click ring: a red halo that flashes at the moment of the click
R = 120
ring = Image.new('RGBA', (R * 4, R * 4), (0, 0, 0, 0))
d = ImageDraw.Draw(ring)
d.ellipse((20, 20, R * 4 - 20, R * 4 - 20), outline=(220, 38, 38, 235), width=26)
d.ellipse((100, 100, R * 4 - 100, R * 4 - 100), fill=(220, 38, 38, 60))
ring = ring.resize((R, R), Image.LANCZOS)
ring.save(os.path.join(OUT, 'ring.png'))
print('wrote', OUT)
