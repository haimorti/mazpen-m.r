#!/usr/bin/env python3
"""Render the written guide — the same material as the video, laid out to be read.

Two page sizes come out of one source: a phone-shaped page whose text fits a
handset at "fit to width", and an A4 page for a desktop screen or a printer.
Text and screenshots come from build/scenes.json, so the guide and the video
cannot drift apart.

Usage: python3 build/make_guide.py [--chrome /path/to/chrome]
Output: build/out/מדריך מצפן זכויות איבה - מובייל.pdf, ... - דסקטופ.pdf
"""
import base64, io, json, os, subprocess, sys, shutil, html

import segno

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'out')
SHOTS = os.path.join(ROOT, 'source', 'screenshots')
FONTS = os.path.join(ROOT, 'build', 'fonts')

chrome = None
if '--chrome' in sys.argv:
    chrome = sys.argv[sys.argv.index('--chrome') + 1]
else:
    for c in ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome', shutil.which('chromium'),
              shutil.which('chromium-browser'), shutil.which('google-chrome')]:
        if c and os.path.exists(c):
            chrome = c; break
if not chrome:
    sys.exit('chromium not found; pass --chrome /path/to/chrome')

from PIL import Image

scenes = json.load(open(os.path.join(ROOT, 'build', 'scenes.json'), encoding='utf-8'))
inv = json.load(open(os.path.join(ROOT, 'build', 'scenes-invoice.json'), encoding='utf-8'))
inv_by = {s['img']: s for s in inv if s.get('img')}
inv_zones = next(s for s in inv if s['type'] == 'zones')
inv_fork = next(s for s in inv if s['type'] == 'fork')
inv_walks = [s for s in inv if s['type'] == 'walk']
by_img = {s['img']: s for s in scenes if s.get('img')}
zone_frames = [s for s in scenes if s['type'] == 'zones' and s.get('active')]
main_zones = zone_frames[0]
statuses = next(s for s in scenes if s['type'] == 'statuslist')
walk = next(s for s in scenes if s['type'] == 'walk')
fork = next(s for s in scenes if s['type'] == 'fork')
esc = html.escape


def font_face(family, weight, filename):
    with open(os.path.join(FONTS, filename), 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


FONT_CSS = ''.join([font_face('Assistant', 400, 'AssistantRegular.ttf'),
                    font_face('Assistant', 600, 'AssistantSemiBold.ttf'),
                    font_face('Assistant', 700, 'AssistantBold.ttf'),
                    font_face('Rubik', 600, 'RubikSemiBold.ttf'),
                    font_face('Rubik', 700, 'RubikBold.ttf')])


def load(name, bg='white'):
    im = Image.open(os.path.join(SHOTS, name))
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        flat = Image.new('RGB', im.size, bg)
        flat.paste(im, mask=im.split()[-1])
        return flat
    return im.convert('RGB')


def uri(im, width=1500):
    """Data URI, capped in width — print resolution without a 40 MB file."""
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'WEBP', quality=90, method=5)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()


def ink_bbox(im, thr=246, pad=8):
    dark = im.convert('L').point(lambda v: 255 if v < thr else 0)
    bb = dark.getbbox()
    if not bb:
        return (0, 0, im.width, im.height)
    return (max(0, bb[0] - pad), max(0, bb[1] - pad),
            min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))


def shot(name, keep=None, keepx=None, trim=False):
    im = load(name)
    if trim:
        im = im.crop(ink_bbox(im))
    if keep or keepx:
        im = im.crop((0, 0, int(im.width * (keepx or 1.0)), int(im.height * (keep or 1.0))))
    return im


MOBILE = False          # set per build; a phone page needs the region, not the whole page


def overlay(boxes, zoom=None):
    """The video's boxes, in per cent of whatever is on the page.

    A box is placed from the right edge, so cropping to a region means measuring
    it against the region's right edge instead of the screenshot's."""
    x0, y0 = (zoom.get('x', 0), zoom['y']) if zoom else (0, 0)
    cw, ch = (zoom.get('w', 1), zoom['h']) if zoom else (1, 1)
    out = []
    for b in boxes:
        x, y, w, h = (b['box'][k] for k in 'xywh')
        out.append(
            f"<span class='bx' style='--c:{b['color']};"
            f"right:{(x / 100 - 1 + x0 + cw) / cw * 100:.2f}%;"
            f"top:{(y / 100 - y0) / ch * 100:.2f}%;"
            f"width:{w / cw:.2f}%;height:{h / ch:.2f}%'>"
            + (f"<i>{b['n']}</i>" if b.get('n') else '') + "</span>")
    return ''.join(out)


def figure(name, keep=None, keepx=None, boxes=(), caption=None, width=1500,
           mzoom=None, msplit=False, trim=False):
    """A screenshot with the same overlay boxes the video draws, plus a caption.

    On the phone page a full screen shrinks to the point of being useless, so a
    figure may name the region worth showing (mzoom) or ask to be cut in two
    (msplit). Neither applies on the A4 page, where the whole screen fits."""
    cap = f"<figcaption>{caption}</figcaption>" if caption else ''
    if MOBILE and (mzoom or msplit):
        im = shot(name, keep, keepx, trim)
        if msplit:
            parts = [im.crop((0, 0, im.width, int(im.height * 0.53))),
                     im.crop((0, int(im.height * 0.47), im.width, im.height))]
        else:
            w, h = im.size
            parts = [im.crop((int(mzoom.get('x', 0) * w), int(mzoom['y'] * h),
                              int((mzoom.get('x', 0) + mzoom.get('w', 1)) * w),
                              int((mzoom['y'] + mzoom['h']) * h)))]
        inner = overlay(boxes, mzoom) if boxes and mzoom and not msplit else ''
        return ('<figure>'
                + ''.join(f"<div class='shotwrap'><img src='{uri(pt, width)}' alt=''>{inner}</div>"
                          for pt in parts) + cap + '</figure>')
    ov = overlay(boxes)
    return (f"<figure><div class='shotwrap'><img src='{uri(shot(name, keep, keepx, trim), width)}' alt=''>"
            f"{ov}</div>{cap}</figure>")


def crop_box(name, box, width=900):
    """One region of a screenshot, blown up — for pointing at a single button."""
    im = load(name)
    w, h = im.size
    im = im.crop((int(box['x'] * w), int(box['y'] * h),
                  int((box['x'] + box['w']) * w), int((box['y'] + box['h']) * h)))
    return uri(im, width)


LOGO = uri(load('logo-rehab-division.png', bg='#FFFFFF'), 900)

PORTAL = 'https://ps.btl.gov.il/'


def qr_uri(data, scale=12):
    """A code to scan, for whoever is holding the guide on paper."""
    buf = io.BytesIO()
    segno.make(data, error='m').save(buf, kind='png', scale=scale, border=2,
                                     dark='#14477E', light='#FFFFFF')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

CSS_COMMON = FONT_CSS + """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#fff;color:#16202B;direction:rtl;text-align:right;
  font-family:'Assistant','DejaVu Sans',sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
h1{font-family:'Rubik';font-weight:700;color:#14477E;margin:0}
h2{font-family:'Rubik';font-weight:700;color:#14477E;margin:0 0 .35em;
  display:flex;align-items:baseline;gap:.5em;break-after:avoid}
h2 .num{font-variant-numeric:tabular-nums;color:#7C93AC;font-weight:600}
h3{font-family:'Rubik';font-weight:600;color:#16202B;margin:1.1em 0 .3em;break-after:avoid}
p{margin:0 0 .7em;line-height:1.65}
section{break-inside:avoid-page;margin-bottom:1.6em}
figure{margin:.7em 0 .5em;break-inside:avoid}
figure .shotwrap + .shotwrap{margin-top:.4em}
.shotwrap{position:relative;line-height:0;border:1px solid #D3DDE7;border-radius:6px;overflow:hidden}
.shotwrap img{display:block;width:100%}
.bx{position:absolute;border:3px solid var(--c);border-radius:6px;
  box-shadow:0 0 0 2px rgba(255,255,255,.6)}
.bx i{position:absolute;top:50%;right:-13px;transform:translate(50%,-50%);
  width:22px;height:22px;border-radius:50%;background:#fff;border:3px solid var(--c);
  color:var(--c);font-family:'Rubik';font-weight:700;font-style:normal;
  display:grid;place-items:center;line-height:1}
figcaption{color:#4E6076;line-height:1.5;margin-top:.4em}
ol.steps{margin:0 0 .8em;padding:0;list-style:none;counter-reset:s}
ol.steps li{counter-increment:s;position:relative;padding-inline-start:2em;
  margin-bottom:.5em;line-height:1.55}
ol.steps li::before{content:counter(s);position:absolute;inset-inline-start:0;top:.05em;
  width:1.45em;height:1.45em;border-radius:50%;background:#E2ECF7;color:#14477E;
  font-family:'Rubik';font-weight:700;display:grid;place-items:center}
ul.pts{margin:0 0 .8em;padding:0;list-style:none}
ul.pts li{position:relative;padding-inline-start:1.1em;margin-bottom:.4em;line-height:1.55}
ul.pts li::before{content:'';position:absolute;inset-inline-start:0;top:.62em;
  width:.42em;height:.42em;border-radius:50%;background:#DC7B1E}
table.st{width:100%;border-collapse:collapse;margin:.5em 0 .8em}
table.st td{border-bottom:1px solid #E4EAF1;padding:.55em .2em;vertical-align:top;line-height:1.5}
table.st td:first-child{width:1%;white-space:nowrap;padding-inline-start:0}
.pill{display:inline-block;border-radius:999px;padding:.15em .8em;font-weight:700;
  font-family:'Rubik';color:var(--c);background:var(--b)}
.note{background:#F4F8FC;border-inline-start:4px solid #14477E;border-radius:0 6px 6px 0;
  padding:.7em .9em;margin:.7em 0}
.note b{color:#14477E}
dl.faq{margin:0 0 1.1em}
dl.faq dt{font-weight:700;color:#16202B;line-height:1.45;margin-top:.85em;
  break-after:avoid}
dl.faq dt:first-of-type{margin-top:.2em}
dl.faq dd{margin:.2em 0 0;padding-bottom:.7em;border-bottom:1px solid #E4EAF1;
  color:#3E5164;line-height:1.55;break-inside:avoid}
dl.faq dd:last-of-type{border-bottom:none}
.routes{display:flex;flex-direction:column;gap:.8em}
.route{display:flex;align-items:center;gap:1em;border:1px solid #D3DDE7;
  border-inline-start:5px solid var(--c);border-radius:0 8px 8px 0;padding:.55em .8em}
.route img{display:block;flex:none;width:30%;max-width:135px;
  border:1px solid #E4EAF1;border-radius:5px}
.route p{margin:0}
.route b{color:var(--c)}
.cover{display:flex;flex-direction:column;justify-content:center;min-height:94vh;gap:.5em;
  break-after:page}
.cover img{width:52%;max-width:250px;margin-bottom:2em}
.cover .sub{color:#4E6076}
.cover .qr{margin-top:auto;display:flex;align-items:center;gap:1em;
  border:1px solid #D3DDE7;border-radius:8px;padding:.8em .9em}
.cover .qr img{width:26%;max-width:110px;margin:0;flex:none}
.cover .qr b{display:block;color:#14477E;font-family:'Rubik';line-height:1.35}
.cover .qr .url{display:block;margin-top:.15em;font-family:'Rubik';font-weight:600;
  color:#16202B;unicode-bidi:isolate;word-break:break-all}
.cover .qr .hint{display:block;margin-top:.3em;color:#4E6076;line-height:1.4}
.cover .foot{margin-top:1.2em;color:#7C93AC}
"""

SIZES = {
    'mobile': ("@page{size:100mm 2600mm;margin:9mm 8mm}"
               "body{font-size:9.6pt}h1{font-size:20pt}h2{font-size:13pt}h3{font-size:11pt}"
               "section{break-inside:auto;margin-bottom:3.2em}"
               ".cover{min-height:auto;break-after:auto;margin-bottom:2.6em;"
               "padding-bottom:1.6em;border-bottom:1px solid #D3DDE7}"
               ".cover img{margin-bottom:1.1em}.cover .qr{margin-top:1.2em}"
               ".cover .foot{margin-top:.9em}"
               "section.newpage{break-before:auto}"
               ".bx i{width:17px;height:17px;font-size:9px;right:-10px;border-width:2px}"
               ".bx{border-width:2px}figcaption{font-size:8.8pt}",
               'מובייל'),
    'desktop': ("@page{size:A4;margin:20mm 22mm}"
                "body{font-size:11.5pt}h1{font-size:30pt}h2{font-size:17pt}h3{font-size:13.5pt}"
                ".bx i{width:26px;height:26px;font-size:14px;right:-15px}"
                "section.newpage{break-before:page}"
                "figcaption{font-size:10.5pt}",
                'דסקטופ'),
}

points = next(s for s in scenes if s['type'] == 'points' and s.get('reveal'))
after = [s for s in scenes if s['type'] == 'points'][-1]
tor = by_img['26-potential-tor.png']
confirm = by_img['05-form-confirmation.png']
inv_sent = inv_by['32-invoice-confirmation.png']
# the same boxes the video draws on the upload page, numbered in the order they are
# used. The video measures a highlight from the left edge; the guide places it from
# the right, so the two disagree unless the box is flipped on the way in.
upload_boxes = [{'color': h.get('c', '#14477E'), 'n': i + 1,
                 'box': dict(h, x=round(100 - h['x'] - h['w'], 1))}
                for i, h in enumerate(inv_by['33-upload-documents.png']['highlights'])]


_faq = []


def faq(group, *qa):
    """Register questions under a heading. They are printed together at the end,
    where people go looking for them, in the order the guide raised them."""
    _faq.append((group, qa))
    return ''


def faq_section(num):
    if not _faq:
        return ''
    blocks = ("<dl class='faq'>"
              + ''.join(f"<dt>{esc(q)}</dt><dd>{a}</dd>"
                        for _, qa in _faq for q, a in qa) + "</dl>")
    return (f"<section><h2><span class='num'>{num}</span> שאלות נפוצות</h2>"
            f"{blocks}</section>")


def routes(f):
    return ''.join(
        f"<div class='route' style='--c:{c['color']}'>"
        f"<img src='{crop_box(c['img'], c['btn_box'])}' alt=''>"
        f"<p>{c['said']}. {esc(c['dest'])}.</p></div>" for c in f['cols'])


def cover(title, sub):
    return (f"<div class='cover'><img src='{LOGO}' alt='הביטוח הלאומי · אגף שיקום'>"
            f"<h1>{esc(title)}</h1><div class='sub'>{esc(sub)}</div>"
            f"<div class='qr'><img src='{qr_uri(PORTAL)}' alt='קוד לסריקה'>"
            "<div><b>לאזור האישי באתר הביטוח הלאומי</b>"
            f"<span class='url' dir='ltr'>{PORTAL}</span>"
            "<span class='hint'>סרקו את הקוד בטלפון, או הקלידו את הכתובת בדפדפן.</span>"
            "</div></div>"
            "<div class='foot'>הביטוח הלאומי · אגף שיקום</div></div>")


# ---------------------------------------------------------------- guide A: getting to know it
def general_html():
    _faq.clear()
    z = main_zones['zones']
    zone_rows = ''.join(
        f"<li><b style='color:{b['color']}'>{esc(f['cap_title'])}</b> — {esc(f['cap'])}</li>"
        for f, b in zip(zone_frames, z))
    st_rows = ''.join(
        f"<tr><td><span class='pill' style='--c:{i['color']};--b:{i['bg']}'>{esc(i['key'])}</span></td>"
        f"<td>{esc(i['note'].split(': ', 1)[1])}</td></tr>" for i in statuses['items'])
    walk_rows = ''.join(f"<li>{esc(s['cap'])}</li>" for s in walk['steps'][1:])

    return cover('מצפן זכויות איבה', 'הסבר כללי למבוטחים') + f"""
<section>
  <h2><span class="num">1</span> מה זה מצפן הזכויות</h2>
  <p>{esc(points['hero'])} — במקום אחד, לפי הנתונים האישיים שלך. מה אפשר לעשות בו:</p>
  <ul class="pts">{''.join(f'<li>{esc(p)}</li>' for p in points['points'])}</ul>
  {faq('כניסה ומי רואה מה',
       ('אני רואה את המצפן אבל אין בו הטבות. מה זה אומר?',
        'המצפן מציג הטבות מהשנתיים האחרונות בלבד. אם לא הגשתם בקשות בתקופה זו, '
        '"ההטבות שלי" יהיה ריק. בדקו את "ההטבות הפוטנציאליות שלי" כדי לראות מה ייתכן שמגיע לכם.'),
       ('הטבה שאני מקבל לא מופיעה במצפן. האם איבדתי אותה?',
        'לא. המצפן נבנה בהדרגה והטבות נוספות מתווספות אליו. '
        'הזכאות שלכם אינה תלויה במה שמוצג במצפן.'))}
</section>

<section>
  <h2><span class="num">2</span> איך נכנסים</h2>
  <ol class="steps">
    <li>נכנסים לאזור האישי באתר הביטוח הלאומי.</li>
    <li>בתפריט הצד בוחרים <b>מצפן הזכויות שלי</b>, ואז <b>כניסה למצפן הזכויות</b>.</li>
    <li>בעמוד שנפתח לוחצים על הכפתור הכחול <b>כניסה למצפן הזכויות</b>.</li>
  </ol>
  {figure('09-entry-page-clean.png', caption='עמוד הכניסה למצפן.')}
  {faq('כניסה ומי רואה מה',
       ('אני לא מוצא את "מצפן הזכויות שלי" בתפריט. למה?',
        'בשלב זה המצפן מוצג רק למשפחות שכולות. בהמשך הוא ייפתח לאוכלוסיות נוספות. '
        'אם אתם שייכים ועדיין לא רואים את המצפן — פנו אלינו.'))}
</section>

<section>
  <h2><span class="num">3</span> המסך הראשי</h2>
  <p>המצפן בנוי מארבעה אזורים, מלמעלה למטה. מהמסך הזה יוצאים לכל מקום, ואליו חוזרים.</p>
  {figure('11-main-screen-zones.png', boxes=z)}
  <ul class="pts">{zone_rows}</ul>
  {faq('המסך הראשי',
       ('איפה אני רואה את ההטבות של הילדים שלי?',
        'במסך הראשי, באזור "הצגת הטבות עבור", בוחרים את שם הילד. '
        'האזור הזה מופיע רק להורים שמקבלים הטבות עבור ילדים קטינים.'),
       ('איך חוזרים למסך הקודם?', 'בכפתור "חזור" בראש הדף.'))}
</section>

<section>
  <h2><span class="num">4</span> ההטבות שלי</h2>
  <p>אלה ההטבות שכבר ביקשת או שכבר אושרו לך. לחיצה על הטבה פותחת את הדף שלה.</p>
  {figure('27-main-screen-rm.png', keep=0.928, mzoom={'y': 0.28, 'h': 0.30, 'w': 0.90},
          caption='"ההטבות שלי" באמצע המסך. לכל מבוטח רשימה אחרת.')}
</section>

<section>
  <h2><span class="num">5</span> דף ההטבה והסטטוסים</h2>
  <p>{esc(statuses['intro']['cap'])}</p>
  {figure('03-benefit-page-statuses.png', keep=0.90, mzoom={'y': 0.48, 'h': 0.52},
          caption='דף ההטבה. בהטבה פעילה, "פרטים נוספים" פותח את התמונה המלאה.')}
  <table class="st">{st_rows}</table>
  {faq('סטטוסים',
       ('מה ההבדל בין "פעילה" ל"הסתיימה"?',
        '"פעילה" היא הטבה מאושרת שנשארה בה יתרה, ואפשר להגיש בה קבלות. '
        '"הסתיימה" היא הטבה שנוצלה במלואה, או שתקופת הזכאות שלה חלפה.'),
       ('הבקשה שלי בסטטוס "בטיפול" כבר הרבה זמן. מה עושים?',
        '"בטיפול" אומר שהבקשה התקבלה ועדיין לא התקבלה בה החלטה. אין צורך להגיש שוב.'),
       ('הבקשה שלי נדחתה. איפה רואים למה?',
        'סיבת הדחייה מופיעה על כרטיס ההטבה עצמו, בשורה "סיבת הדחייה".'),
       ('למה אותה הטבה מופיעה גם ב"ההטבות שלי" וגם ב"פוטנציאליות"?',
        'זה קורה כשאפשר להרחיב את ההטבה — למשל לבקש אותה לתקופה נוספת, '
        'או עבור בן משפחה נוסף.'))}
</section>

<section>
  <h2><span class="num">6</span> התמונה המלאה של ההטבה</h2>
  <p>{esc(walk['steps'][0]['cap'])}</p>
  {figure('21-benefit-details-rm.png', keep=0.845, keepx=0.79, msplit=True)}
  <ul class="pts">{walk_rows}</ul>
  {faq('מימוש ההטבה',
       ('איך אני יודע כמה עוד נשאר לי לנצל?',
        'בדף ההטבה, באזור "סיכום מימוש", מופיע פס עם הסכום ששולם, מה שנותר, '
        'והסכום הכולל.'))}
</section>

<section>
  <h2><span class="num">7</span> ההטבות הפוטנציאליות שלך</h2>
  <p>כל ההטבות להן אתה עשוי להיות זכאי ועדיין לא ביקשת. לחיצה על הטבה פותחת את הדף שלה.</p>
  {figure('26-potential-tor.png', keep=0.47, keepx=0.835,
          mzoom={'y': 0.36, 'h': 0.64, 'w': 0.80}, caption=esc(tor['cap']))}
</section>

<section>
  <h2><span class="num">8</span> שני הכפתורים</h2>
  <p>{esc(fork['hint'])}</p>
  <div class="routes">{routes(fork)}</div>
  <p>המערכת קובעת איזה כפתור יופיע, ואין מה לבחור.</p>
  {faq('בקשה להטבה חדשה',
       ('האם הגשת הבקשה מבטיחה שאקבל את ההטבה?',
        'לא. הגשת בקשה אינה מהווה אישור אוטומטי. הזכאות נבדקת לפי הקריטריונים '
        'שנקבעו בחוק ובהתאם למסמכים שהוגשו.'))}
</section>

<section>
  <h2><span class="num">9</span> אחרי שהגשת</h2>
  <p>{esc(after['lead'])}</p>
  <ul class="pts">{''.join(f'<li>{esc(p)}</li>' for p in after['points'])}</ul>
  {figure('05-form-confirmation.png', caption=esc(confirm['cap']))}
  {faq('בקשה להטבה חדשה',
       ('מה קורה אחרי ששלחתי?',
        'ההטבה עוברת ל"ההטבות שלי". משם נכנסים אליה ורואים את סטטוס הטיפול בבקשה.'))}
</section>
{faq_section(10)}
"""


# ---------------------------------------------------------------- guide B: submitting
def invoice_html():
    _faq.clear()
    inv_points = next(x for x in inv if x['type'] == 'points' and 'lead' in x
                      and 'המצפן' in x['lead'])
    inv_why = ''.join(f'<li>{esc(p)}</li>' for p in inv_points['points'])
    return cover('הגשת חשבונית או קבלה', 'במצפן זכויות איבה') + f"""
<section>
  <h2><span class="num">1</span> לפני שמתחילים</h2>
  <p>המדריך מראה איך מגישים חשבונית או קבלה להחזר דרך מצפן זכויות איבה —
     מהרגע שנכנסים ועד ההודעה שהבקשה נקלטה.</p>
  <h3>למה דווקא דרך המצפן</h3>
  <ul class="pts">{inv_why}</ul>
  <h3>איך נכנסים למצפן</h3>
  <ol class="steps">
    <li>נכנסים לאזור האישי באתר הביטוח הלאומי.</li>
    <li>בתפריט הצד: <b>מצפן הזכויות שלי</b> ← <b>כניסה למצפן הזכויות</b>.</li>
    <li>בעמוד שנפתח לוחצים על הכפתור הכחול.</li>
  </ol>
  <p>כדאי שיהיה מוכן מראש קובץ סרוק או מצולם של חשבונית המס או הקבלה שברשותך.</p>
</section>

<section class="newpage">
  <h2><span class="num">2</span> שתי דרכים להגיש</h2>
  <p>{esc(inv_zones['cap'])}</p>
  {figure('27-main-screen-rm.png', keep=0.928, boxes=inv_zones['zones'],
          caption='1 — הדרך המועדפת. 2 — רק אם ההטבה לא מופיעה למעלה.')}
  <h3>הדרך המועדפת: דרך "ההטבות שלי"</h3>
  <ol class="steps">
    <li>לוחצים על ההטבה שעבורה יש לך חשבונית.</li>
    <li>בדף ההטבה לוחצים על <b>פרטים נוספים</b>.</li>
    <li>בתמונה המלאה לוחצים על הכפתור הכחול
        <b>+ להגשת חשבונית / קבלה חדשה</b>.</li>
  </ol>
  {figure('25-benefit-details-rg.png', trim=True, mzoom={'y': 0.50, 'h': 0.28},
          caption='הכפתור הכחול יושב מעל "בקשות להחזר".')}
  {faq('מתי אפשר להגיש',
       ('למה אני לא רואה את הכפתור "להגשת חשבונית / קבלה חדשה"?',
        'הכפתור מופיע רק בהטבה בסטטוס "פעילה". בהטבה שהסתיימה או שנדחתה '
        'אי אפשר להגיש קבלות.'))}
</section>

<section class="newpage">
  <h2><span class="num">3</span> אם ההטבה לא מופיעה ב"ההטבות שלי"</h2>
  <p>מחפשים אותה בהטבות הפוטנציאליות. שימו לב: בשלב זה עדיין לא כל ההטבות
     הפוטנציאליות פתוחות להגשת חשבוניות דרך המצפן. {esc(inv_fork['hint'])}</p>
  <div class="routes">{routes(inv_fork)}</div>
  <h3>כשלא מופיע "הגשת בקשה"</h3>
  <p>במקרה כזה ההגשה אינה נעשית במצפן, אלא באמצעות <b>העלאת מסמכים</b> באזור האישי:</p>
  <ol class="steps">
    <li>בתפריט "פעולות באתר" בוחרים <b>העלאת מסמכים</b>.</li>
    <li>בשדה <b>נושא</b> בוחרים <b>שיקום</b>.</li>
    <li>בשדה <b>קטגוריה</b> בוחרים <b>פניות</b>.</li>
    <li>בשדה <b>מסמך</b> בוחרים <b>פנייה</b>.</li>
    <li>לוחצים <b>צרף קובץ</b> ומצרפים את החשבונית או הקבלה.</li>
    <li>לוחצים <b>שלח מסמך</b>.</li>
  </ol>
  {figure('33-upload-documents.png', boxes=upload_boxes,
          mzoom={'x': 0.0, 'y': 0.23, 'w': 0.80, 'h': 0.57},
          caption='עמוד "העלאת מסמכים" באזור האישי, לפי סדר השלבים.')}
</section>

<section>
  <h2><span class="num">4</span> שלושת שלבי הטופס</h2>
  <p>מצאתם את ההטבה ולחצתם על הכפתור — בין אם דרך "ההטבות שלי" ובין אם דרך ההטבות
     הפוטנציאליות. מכאן והלאה התהליך זהה בשתי הדרכים: נפתח אותו טופס, בן שלושה שלבים,
     ובסופו נשלחת החשבונית.</p>
  <h3>שלב 1 — פרטי ההטבה</h3>
  <p>רק בודקים שהפרטים נכונים ולוחצים <b>הבא</b>.</p>
  <h3>שלב 2 — צירוף החשבונית ופרטיה</h3>
  <p>גוררים את קובץ החשבונית לתוך המסגרת, או לוחצים <b>בחר קובץ</b>. אחר כך ממלאים
     לפי החשבונית: מספר, תאריך וסכום כולל מע״מ. מספר מזהה ספק, תקופה וכמות — לפי הצורך.</p>
  {figure('30-form-step2-filled.png', trim=True, mzoom={'y': 0.40, 'h': 0.45},
          caption='כך נראה השלב אחרי שהקובץ צורף והפרטים מולאו. '
                  '"+ הוסף חשבונית" מוסיף עוד חשבונית לאותה בקשה.')}
  <h3>שלב 3 — הצהרה וחתימה</h3>
  <p>{esc(inv_walks[1]['steps'][0]['cap'])} {esc(inv_walks[1]['steps'][1]['cap'])}</p>
  {figure('31-form-step3.png', trim=True, mzoom={'y': 0.60, 'h': 0.40},
          caption='החתימה נעשית בעכבר במחשב, או באצבע בטלפון.')}
  {faq('מילוי הטופס',
       ('אילו מסמכים צריך לצרף?',
        'זה משתנה מהטבה להטבה, לפי מה שהוגדר לכל אחת. יש הטבות שדורשות קבלה בלבד, '
        'ויש שדורשות גם קבלה וגם אישור מקופת חולים.'),
       ('על החשבונית שלי יש כמה טיפולים. מה ממלאים?',
        'ממלאים תקופה מתאריך עד תאריך, את הכמות, ואת סכום החשבונית הכולל.'),
       ('יש לי כמה חשבוניות לאותה בקשה.',
        'אחרי מילוי הפרטים של החשבונית הראשונה לוחצים על "+ הוסף חשבונית".'),
       ('עד מתי אחורה אפשר להגיש?', 'ניתן להגיש עד שנה אחורה.'),
       ('איך חותמים?', 'בעכבר במחשב, או באצבע על המסך במכשיר נייד.'))}
  <div class="note"><b>הגשת בקשה אינה אישור אוטומטי לקבלת ההטבה.</b>
    הזכאות תיבדק לפי הקריטריונים שנקבעו בחוק ובהתאם למסמכים שהוגשו.</div>
</section>

<section>
  <h2><span class="num">5</span> אחרי השליחה</h2>
  <p>{esc(inv_sent['cap'])}</p>
  {figure('32-invoice-confirmation.png', trim=True,
          caption='מסך האישור שמופיע בסוף התהליך.')}
  {faq('אחרי השליחה',
       ('הגשתי קבלה ולא קיבלתי הודעת אישור. האם הבקשה התקבלה?',
        'אחרי שליחה תקינה מופיעה ההודעה "תודה, פנייתך נקלטה להמשך טיפול". '
        'אם לא ראיתם אותה, היכנסו לדף ההטבה ובדקו אם הבקשה מופיעה ב"בקשות להחזר". '
        'אם היא לא שם — הגישו שוב.'),
       ('הגשתי קבלה ומופיע "בקשה זו הועברה לטיפול בהטבה אחרת". מה זה אומר?',
        'הקבלה הוגשה בהטבה לא מתאימה, והיא הועברה להטבה הנכונה. '
        'הבקשה ממשיכה להיות מטופלת שם. אין צורך להגיש שוב.'))}
</section>

<section>
  <h2><span class="num">6</span> איך עוקבים</h2>
  <p>הבקשה מופיעה בדף ההטבה תחת "בקשות להחזר", עם התאריך, הסכום, סטטוס הטיפול בה,
     ואפשרות לפתוח את הקבלה עצמה. כאן בודקים אם קבלה שולמה.</p>
  {figure('25-benefit-details-rg.png', trim=True, mzoom={'y': 0.58, 'h': 0.42},
          caption='אזור "בקשות להחזר" בדף ההטבה.')}
  {faq('אחרי השליחה',
       ('אפשר לראות את הקבלה שהגשתי?',
        'כן. באזור "בקשות להחזר", ליד כל חשבונית יש סמל הורדה.'))}
</section>
{faq_section(7)}
"""


def trim_tail(path, pad_mm=9):
    """The phone page is deliberately far taller than the guide, so that nothing
    is cut in half. Cut the empty tail back to where the last thing on it ends."""
    import pymupdf
    doc = pymupdf.open(path)
    page = doc[0]
    # a coarse render, read from the bottom up: the last row that is not paper
    dpi = 18
    pm = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    row = pm.width * pm.n
    bottom = 0
    for y in range(pm.height - 1, -1, -1):
        line = pm.samples[y * pm.stride:y * pm.stride + row]
        if min(line) < 245:
            bottom = (y + 1) * 72 / dpi
            break
    r = page.rect
    page.set_cropbox(pymupdf.Rect(0, 0, r.width,
                                  min(r.height, bottom + pad_mm * 72 / 25.4)))
    tmp = path + '.tmp'
    doc.save(tmp)
    doc.close()
    os.replace(tmp, path)


GUIDES = [('מדריך מצפן זכויות איבה', general_html),
          ('מדריך הגשת חשבונית או קבלה', invoice_html)]

os.makedirs(OUT, exist_ok=True)
for name, build in GUIDES:
    for key, (size_css, label) in SIZES.items():
        MOBILE = key == 'mobile'
        doc = ("<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'>"
               f"<style>{CSS_COMMON}{size_css}</style></head><body>{build()}</body></html>")
        stem = f'{name} - {label}'
        hp = os.path.join(OUT, f'{stem}.html')
        pdf = os.path.join(OUT, f'{stem}.pdf')
        open(hp, 'w', encoding='utf-8').write(doc)
        subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu',
                        '--no-pdf-header-footer', f'--print-to-pdf={pdf}',
                        '--virtual-time-budget=20000', 'file://' + hp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if MOBILE:
            trim_tail(pdf)
        print('wrote', os.path.relpath(pdf, ROOT), f'{os.path.getsize(pdf)/1e6:.1f} MB')
