#!/usr/bin/env python3
"""דף אחד: איך שולחים מסמכים לעובד השיקום.

עומד בפני עצמו — נשלח במייל או מודפס ונמסר ביד. אינו מזכיר אוכלוסייה,
ואינו תלוי במצפן: זו הדרך הכללית לשלוח מסמך דרך האזור האישי.

Usage: python3 build/make_upload_sheet.py [--chrome /path/to/chrome]
Output: build/out/שליחת מסמכים לעובד השיקום.pdf
"""
import base64
import io
import json
import os
import shutil
import subprocess
import sys

import segno
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'out')
SHOTS = os.path.join(ROOT, 'source', 'screenshots')
FONTS = os.path.join(ROOT, 'build', 'fonts')
PORTAL = 'https://ps.btl.gov.il/'

chrome = None
if '--chrome' in sys.argv:
    chrome = sys.argv[sys.argv.index('--chrome') + 1]
else:
    for c in ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome', shutil.which('chromium'),
              shutil.which('chromium-browser'), shutil.which('google-chrome')]:
        if c and os.path.exists(c):
            chrome = c
            break
if not chrome:
    sys.exit('chromium not found; pass --chrome /path/to/chrome')


def font_face(family, weight, filename):
    with open(os.path.join(FONTS, filename), 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


FONT_CSS = ''.join([
    font_face('Assistant', 400, 'AssistantRegular.ttf'),
    font_face('Assistant', 600, 'AssistantSemiBold.ttf'),
    font_face('Assistant', 700, 'AssistantBold.ttf'),
    font_face('Rubik', 600, 'RubikSemiBold.ttf'),
    font_face('Rubik', 700, 'RubikBold.ttf'),
])


def load(name, bg='white'):
    im = Image.open(os.path.join(SHOTS, name))
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        flat = Image.new('RGB', im.size, bg)
        flat.paste(im, mask=im.split()[-1])
        return flat
    return im.convert('RGB')


def uri(im, fmt='PNG'):
    buf = io.BytesIO()
    im.save(buf, fmt)
    return f'data:image/{fmt.lower()};base64,' + base64.b64encode(buf.getvalue()).decode()


def numbered(name, marks, keep=1.0, scale=2):
    """The screenshot with the same boxes the video draws, numbered in step order."""
    im = load(name)
    im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(os.path.join(FONTS, 'RubikBold.ttf'), 44)
    except OSError:
        font = ImageFont.load_default()
    w, h = im.size
    for i, m in enumerate(marks, start=1):
        x, y = m['x'] / 100 * w, m['y'] / 100 * h
        bw, bh = m['w'] / 100 * w, m['h'] / 100 * h
        c = m.get('c', '#14477E')
        d.rounded_rectangle([x, y, x + bw, y + bh], 12, outline=c, width=8)
        r = 32
        cx, cy = x + bw + r * 0.2, y + bh / 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='white', outline=c, width=8)
        d.text((cx, cy), str(i), font=font, fill=c, anchor='mm')
    if keep < 1.0:                       # the page below the send bar is empty
        im = im.crop((0, 0, im.width, int(im.height * keep)))
    out = Image.new('RGB', (im.width + 8, im.height + 8), 'white')
    out.paste(im, (4, 4))
    ImageDraw.Draw(out).rounded_rectangle([0, 0, out.width - 1, out.height - 1],
                                          16, outline='#D3DDE7', width=4)
    return out


inv = json.load(open(os.path.join(ROOT, 'build', 'scenes-invoice.json'), encoding='utf-8'))
upload = next(s for s in inv if s.get('img') == '33-upload-documents.png')
SHOT = uri(numbered('33-upload-documents.png', upload['highlights'], keep=0.83))
LOGO = uri(load('logo-rehab-division.png'))

buf = io.BytesIO()
segno.make(PORTAL, error='m').save(buf, kind='png', scale=12, border=2,
                                   dark='#14477E', light='#FFFFFF')
QR = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

STEPS = [
    ('נכנסים ל"העלאת מסמכים"', 'באזור האישי, בתפריט <b>פעולות באתר</b>.'),
    ('נושא', 'בוחרים <b>שיקום</b>.'),
    ('קטגוריה', 'בוחרים <b>פניות</b>.'),
    ('מסמך', 'בוחרים <b>פנייה</b>.'),
    ('מצרפים את הקובץ', 'לוחצים <b>צרף קובץ</b>, או גוררים את הקובץ למסגרת.'),
    ('שולחים', 'מוודאים שכל השדות המסומנים מלאים, ולוחצים <b>שלח מסמך</b>.'),
]

steps_html = ''.join(
    f"<li><span class='n'>{i}</span><span class='t'><b>{t}</b><span>{d}</span></span></li>"
    for i, (t, d) in enumerate(STEPS, start=1))

doc = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>
{FONT_CSS}
@page{{size:A4;margin:12mm 14mm}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{background:#fff;color:#1E2C24;direction:rtl;text-align:right;font-size:11pt;
  font-family:'Assistant','DejaVu Sans',sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
header{{display:flex;align-items:flex-start;justify-content:space-between;gap:10mm;
  border-bottom:1px solid #CFE0D5;padding-bottom:3mm}}
header img{{width:40mm;flex:none}}
h1{{font-family:'Rubik';font-weight:700;color:#14477E;font-size:20pt;margin:0;line-height:1.15}}
.lede{{color:#4A5C70;margin:1.5mm 0 0;font-size:11.5pt;line-height:1.4;max-width:120mm}}
.enter{{display:flex;align-items:center;gap:6mm;border:1px solid #CFE0D5;border-radius:3mm;
  padding:3mm 4.5mm;margin:3.5mm 0}}
.enter img{{width:17mm;flex:none}}
.enter .k{{font-family:'Rubik';font-weight:700;color:#2C7A5B;font-size:10pt;margin:0 0 1mm}}
.enter .u{{font-family:'Rubik';font-weight:700;color:#14477E;font-size:14pt;
  unicode-bidi:isolate;direction:ltr;display:inline-block}}
.enter p{{margin:1.5mm 0 0;color:#4A5C70;font-size:10.5pt;line-height:1.4}}
h2{{font-family:'Rubik';font-weight:700;color:#14477E;font-size:13pt;margin:4mm 0 2.5mm}}
ol.steps{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr;
  gap:2mm 7mm}}
ol.steps li{{display:flex;gap:3mm;align-items:flex-start}}
ol.steps .n{{flex:none;width:7mm;height:7mm;border-radius:50%;background:#14477E;color:#fff;
  font-family:'Rubik';font-weight:700;font-size:10pt;display:flex;align-items:center;
  justify-content:center;margin-top:.4mm}}
ol.steps .t{{display:flex;flex-direction:column;gap:.6mm;line-height:1.35}}
ol.steps .t b{{font-size:11.5pt;color:#1E2C24}}
ol.steps .t span{{font-size:10.5pt;color:#4A5C70}}
figure{{margin:3.5mm 0 0}}
figure img{{display:block;width:100%}}
figcaption{{color:#7A8B7F;font-size:9.5pt;margin-top:1.2mm;text-align:center}}
.note{{background:#F4F8F5;border-inline-start:4px solid #2C7A5B;border-radius:0 2mm 2mm 0;
  padding:2.8mm 4mm;margin:2.5mm 0 0;font-size:10.5pt;line-height:1.4}}
.note b{{color:#2C7A5B}}
.calm{{border:1px solid #2C7A5B;border-radius:3mm;padding:3mm 5mm;margin:2.5mm 0 0;
  background:#F1F7F3}}
.calm b{{font-family:'Rubik';font-weight:700;color:#2C7A5B;font-size:12.5pt;display:block;
  margin-bottom:1mm}}
.calm p{{margin:0;font-size:11pt;line-height:1.5;color:#1E2C24}}
footer{{margin-top:2.5mm;padding-top:0;color:#8FA396;font-size:9pt}}
</style></head><body>

<header>
  <div>
    <h1>שליחת מסמכים לעובד השיקום</h1>
    <p class="lede">אפשר לשלוח לנו מסמכים מהבית, דרך האזור האישי באתר הביטוח הלאומי —
       בלי להגיע לסניף ובלי לשלוח בדואר.</p>
  </div>
  <img src="{LOGO}" alt="הביטוח הלאומי · אגף שיקום">
</header>

<div class="enter">
  <img src="{QR}" alt="קוד לסריקה">
  <div>
    <p class="k">האזור האישי באתר הביטוח הלאומי</p>
    <span class="u">{PORTAL}</span>
    <p>סורקים את הקוד בטלפון, או מקלידים את הכתובת בדפדפן ומתחברים לאזור האישי.</p>
  </div>
</div>

<h2>שישה שלבים</h2>
<ol class="steps">{steps_html}</ol>

<figure>
  <img src="{SHOT}" alt="עמוד העלאת מסמכים באזור האישי">
  <figcaption>עמוד "העלאת מסמכים" באזור האישי. המספרים מסומנים לפי סדר השלבים.</figcaption>
</figure>

<div class="note">
  <b>לפני השליחה:</b> יש לשלוח מסמכים קריאים וברורים, שאינם דורשים סיסמה לפתיחתם.
</div>

<div class="calm">
  <b>המסמך מגיע אלינו ישירות</b>
  <p>אחרי השליחה מופיע אישור על המסך. המסמך נכנס לתיק שלכם ומגיע לטיפול —
     אין צורך לשלוח אותו שוב בדרך נוספת, ואין צורך להתקשר כדי לוודא שהתקבל.</p>
</div>

<footer>הביטוח הלאומי · אגף שיקום</footer>
</body></html>"""

os.makedirs(OUT, exist_ok=True)
stem = 'שליחת מסמכים לעובד השיקום'
hp = os.path.join(OUT, stem + '.html')
pdf = os.path.join(OUT, stem + '.pdf')
open(hp, 'w', encoding='utf-8').write(doc)
subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu',
                '--no-pdf-header-footer', f'--print-to-pdf={pdf}',
                '--virtual-time-budget=20000', 'file://' + hp], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print('wrote', os.path.relpath(pdf, ROOT), f'{os.path.getsize(pdf)/1e6:.1f} MB')
