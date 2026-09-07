#!/usr/bin/env python3
"""Cut the screenshots the conference deck needs, and draw the boxes on them.

Same crops the video uses, read from build/scenes.json, so the deck cannot show
a screen the film does not.
"""
import json
import os

import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, 'source', 'screenshots')
DEST = os.path.join(ROOT, 'build', 'deck', 'assets')
FONTS = os.path.join(ROOT, 'build', 'fonts')
os.makedirs(DEST, exist_ok=True)

scenes = json.load(open(os.path.join(ROOT, 'build', 'scenes.json'), encoding='utf-8'))
inv = json.load(open(os.path.join(ROOT, 'build', 'scenes-invoice.json'), encoding='utf-8'))
by = {s['img']: s for s in scenes + inv if s.get('img')}


def load(name):
    im = Image.open(os.path.join(SHOTS, name))
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        flat = Image.new('RGB', im.size, 'white')
        flat.paste(im, mask=im.split()[-1])
        return flat
    return im.convert('RGB')


def ink_bbox(im, thr=246, pad=8):
    dark = im.convert('L').point(lambda v: 255 if v < thr else 0)
    bb = dark.getbbox() or (0, 0, im.width, im.height)
    return (max(0, bb[0] - pad), max(0, bb[1] - pad),
            min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))


# the capture came from the test environment and carries its case number
WIPE = {'28-form-step1.png': (155, 24, 296, 53)}


def cut(name, keep=None, keepx=None, trim=False, scale=2):
    im = load(name)
    if name in WIPE:
        ImageDraw.Draw(im).rectangle(WIPE[name], fill='white')
    if trim:
        im = im.crop(ink_bbox(im))
    if keep or keepx:
        im = im.crop((0, 0, int(im.width * (keepx or 1)), int(im.height * (keep or 1))))
    return im.resize((im.width * scale, im.height * scale), Image.LANCZOS)


def frame(im, radius=18, border='#D3DDE7'):
    """A white card edge, so the screenshot does not float on the slide."""
    out = Image.new('RGB', (im.width + 8, im.height + 8), 'white')
    out.paste(im, (4, 4))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([0, 0, out.width - 1, out.height - 1], radius, outline=border, width=4)
    return out


def boxes(im, marks, width=8, from_left=True, numbers=True):
    """The video's boxes, drawn on. `from_left` matches how the film measures them."""
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(os.path.join(FONTS, 'RubikBold.ttf'), 46)
    except OSError:
        font = ImageFont.load_default()
    w, h = im.size
    for m in marks:
        b, c, n = m['box'], m['color'], m.get('n')
        x = b['x'] / 100 * w if from_left else (100 - b['x'] - b['w']) / 100 * w
        y, bw, bh = b['y'] / 100 * h, b['w'] / 100 * w, b['h'] / 100 * h
        d.rounded_rectangle([x, y, x + bw, y + bh], 12, outline=c, width=width)
        if numbers and n:
            r = 34
            cx, cy = x + bw + r * 0.2, y + bh / 2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='white', outline=c, width=width)
            d.text((cx, cy), str(n), font=font, fill=c, anchor='mm')
    return im


# ------------------------------------------------------------------ the pictures
JOBS = {
    'entry': dict(name='09-entry-page-clean.png'),
    'main': dict(name='27-main-screen-rm.png', keep=0.928),
    'benefit': dict(name='03-benefit-page-statuses.png', keep=0.90),
    'details': dict(name='25-benefit-details-rg.png', trim=True),
    'potential': dict(name='26-potential-tor.png', keep=0.47, keepx=0.835),
    'form1': dict(name='28-form-step1.png', trim=True),
    'form2': dict(name='30-form-step2-filled.png', trim=True),
    'form3': dict(name='31-form-step3.png', trim=True),
    'sent': dict(name='32-invoice-confirmation.png', trim=True),
    'upload': dict(name='33-upload-documents.png'),
    'zones': dict(name='11-main-screen-zones.png'),
}
# the entry page is nearly square; the slide wants a band, so keep only the page body
BANDS = {'entry_wide': ('09-entry-page-clean.png', 0.03, 0.82)}
for key, job in JOBS.items():
    im = cut(**job)
    if key == 'zones':
        z = next(s for s in scenes if s['type'] == 'zones')['zones']
        im = boxes(im, z)
    if key == 'upload':
        im = boxes(im, [{'box': h, 'color': h.get('c', '#14477E'), 'n': i + 1}
                        for i, h in enumerate(by['33-upload-documents.png']['highlights'])])
    frame(im).save(os.path.join(DEST, key + '.png'))
    print(key, im.size)

for key, (name, y0, y1) in BANDS.items():
    im = cut(name)
    im = im.crop((0, int(im.height * y0), im.width, int(im.height * y1)))
    frame(im).save(os.path.join(DEST, key + '.png'))
    print(key, im.size)

# the two buttons, cut out of the cards they sit on
for key, col in zip(('btn_request', 'btn_inquiry'),
                    next(s for s in scenes if s['type'] == 'fork')['cols']):
    im = load(col['img'])
    b = col['btn_box']
    im = im.crop((int(b['x'] * im.width), int(b['y'] * im.height),
                  int((b['x'] + b['w']) * im.width), int((b['y'] + b['h']) * im.height)))
    im.resize((im.width * 4, im.height * 4), Image.LANCZOS).save(os.path.join(DEST, key + '.png'))
    print(key, im.size)

load('logo-rehab-division.png').save(os.path.join(DEST, 'logo.png'))
buf = os.path.join(DEST, 'qr.png')
segno.make('https://ps.btl.gov.il/', error='m').save(
    buf, scale=14, border=2, dark='#14477E', light='#FFFFFF')
print('logo, qr')
