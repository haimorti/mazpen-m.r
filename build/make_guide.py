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
        return ('<figure>'
                + ''.join(f"<div class='shotwrap'><img src='{uri(pt, width)}' alt=''></div>"
                          for pt in parts) + cap + '</figure>')
    ov = ''.join(
        f"<span class='bx' style='--c:{b['color']};right:{b['box']['x']}%;top:{b['box']['y']}%;"
        f"width:{b['box']['w']}%;height:{b['box']['h']}%'>"
        + (f"<i>{b['n']}</i>" if b.get('n') else '') + "</span>"
        for b in boxes)
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
.routes{display:flex;flex-direction:column;gap:.8em}
.route{border:1px solid #D3DDE7;border-inline-start:5px solid var(--c);border-radius:0 8px 8px 0;
  padding:.7em .9em}
.route img{display:block;width:58%;max-width:230px;margin-bottom:.5em;
  border:1px solid #E4EAF1;border-radius:5px}
.route b{color:var(--c)}
.cover{display:flex;flex-direction:column;justify-content:center;min-height:94vh;gap:.5em;
  break-after:page}
.cover img{width:52%;max-width:250px;margin-bottom:2em}
.cover .sub{color:#4E6076}
.cover .foot{margin-top:auto;color:#7C93AC}
"""

SIZES = {
    'mobile': ("@page{size:100mm 178mm;margin:9mm 8mm}"
               "body{font-size:9.6pt}h1{font-size:20pt}h2{font-size:13pt}h3{font-size:11pt}"
               "section{break-inside:auto;margin-bottom:1.3em}.bx i{width:17px;height:17px;font-size:9px;right:-10px;border-width:2px}"
               ".bx{border-width:2px}figcaption{font-size:8.8pt}",
               'מובייל'),
    'desktop': ("@page{size:A4;margin:20mm 22mm}"
                "body{font-size:11.5pt}h1{font-size:30pt}h2{font-size:17pt}h3{font-size:13.5pt}"
                ".bx i{width:26px;height:26px;font-size:14px;right:-15px}"
                "figcaption{font-size:10.5pt}",
                'דסקטופ'),
}

points = next(s for s in scenes if s['type'] == 'points' and s.get('reveal'))
after = [s for s in scenes if s['type'] == 'points'][-1]
entry = by_img['09-entry-page-clean.png']
main_zones = zone_frames[0]
hub = [s for s in scenes if s.get('img') == '27-main-screen-rm.png']
tor = by_img['26-potential-tor.png']
confirm = by_img['05-form-confirmation.png']


def body_html():
    z = main_zones['zones']
    zone_rows = ''.join(
        f"<li><b style='color:{b['color']}'>{esc(f['cap_title'])}</b> — {esc(f['cap'])}</li>"
        for f, b in zip(zone_frames, z))
    st_rows = ''.join(
        f"<tr><td><span class='pill' style='--c:{i['color']};--b:{i['bg']}'>{esc(i['key'])}</span></td>"
        f"<td>{esc(i['note'].split(': ', 1)[1])}</td></tr>" for i in statuses['items'])
    walk_rows = ''.join(f"<li>{esc(s['cap'])}</li>" for s in walk['steps'][1:])
    inv_routes = ''.join(
        f"<div class='route' style='--c:{c['color']}'>"
        f"<img src='{crop_box(c['img'], c['btn_box'])}' alt=''>"
        f"<p>{c['said']}. {esc(c['dest'])}.</p></div>" for c in inv_fork['cols'])
    routes = ''.join(
        f"<div class='route' style='--c:{c['color']}'>"
        f"<img src='{crop_box(c['img'], c['btn_box'])}' alt=''>"
        f"<p>{c['said']} — <b>{esc(c['dest'])}</b>.</p></div>" for c in fork['cols'])

    return f"""
<div class="cover">
  <img src="{LOGO}" alt="הביטוח הלאומי · אגף שיקום">
  <h1>מצפן זכויות איבה</h1>
  <div class="sub">הסבר כללי למבוטחים</div>
  <div class="foot">הביטוח הלאומי · אגף שיקום</div>
</div>

<section>
  <h2><span class="num">1</span> מה זה מצפן הזכויות</h2>
  <p>{esc(points['hero'])} — במקום אחד, לפי הנתונים האישיים שלך. מה אפשר לעשות בו:</p>
  <ul class="pts">{''.join(f'<li>{esc(p)}</li>' for p in points['points'])}</ul>
</section>

<section>
  <h2><span class="num">2</span> איך נכנסים</h2>
  <ol class="steps">
    <li>נכנסים לאזור האישי באתר הביטוח הלאומי.</li>
    <li>בתפריט הצד בוחרים <b>מצפן הזכויות שלי</b>, ואז <b>כניסה למצפן הזכויות</b>.</li>
    <li>בעמוד שנפתח לוחצים על הכפתור הכחול <b>כניסה למצפן הזכויות</b>.</li>
  </ol>
  {figure('09-entry-page-clean.png', caption='עמוד הכניסה למצפן.')}
</section>

<section>
  <h2><span class="num">3</span> המסך הראשי</h2>
  <p>המצפן בנוי מארבעה אזורים, מלמעלה למטה. מהמסך הזה יוצאים לכל מקום, ואליו חוזרים.</p>
  {figure('11-main-screen-zones.png', boxes=z)}
  <ul class="pts">{zone_rows}</ul>
</section>

<section>
  <h2><span class="num">4</span> ההטבות שלי</h2>
  <p>אלה ההטבות שכבר ביקשת או שכבר אושרו לך. לחיצה על הטבה פותחת את הדף שלה.</p>
  {figure('27-main-screen-rm.png', keep=0.928, mzoom={'y': 0.28, 'h': 0.30, 'w': 0.90},
          caption='"ההטבות שלי" באמצע המסך. לכל מבוטח רשימה אחרת.')}
</section>

<section>
  <h2><span class="num">5</span> דף ההטבה</h2>
  <p>{esc(statuses['intro']['cap'])}</p>
  {figure('03-benefit-page-statuses.png', keep=0.90, mzoom={'y': 0.48, 'h': 0.52},
          caption='דף ההטבה. בהטבה פעילה, "פרטים נוספים" פותח את התמונה המלאה.')}
  <h3>הסטטוסים ומה הם אומרים</h3>
  <table class="st">{st_rows}</table>
</section>

<section>
  <h2><span class="num">6</span> התמונה המלאה של ההטבה</h2>
  <p>{esc(walk['steps'][0]['cap'])}</p>
  {figure('21-benefit-details-rm.png', keep=0.845, keepx=0.79, msplit=True)}
  <ul class="pts">{walk_rows}</ul>
  <div class="note"><b>כאן בודקים אם קבלה שולמה.</b> בכל בקשה מופיע סטטוס הטיפול בה,
    הסכום שאושר לתשלום, ואפשרות לפתוח את הקבלה עצמה.</div>
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
  <div class="routes">{routes}</div>
  <p>המערכת קובעת איזה כפתור יופיע, ואין מה לבחור.</p>
</section>

<section>
  <h2><span class="num">9</span> איך מגישים חשבונית או קבלה</h2>
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
  {figure('25-benefit-details-rg.png', trim=True,
          mzoom={'y': 0.50, 'h': 0.28},
          caption='הכפתור הכחול יושב מעל "בקשות להחזר".')}
  <h3>אם ההטבה לא מופיעה ב"ההטבות שלי"</h3>
  <p>מחפשים אותה בהטבות הפוטנציאליות. {esc(inv_fork['hint'])}</p>
  <div class="routes">{inv_routes}</div>
</section>

<section>
  <h2><span class="num">10</span> שלושת שלבי הטופס</h2>
  <p>משתי הדרכים מגיעים לאותו טופס.</p>
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
  <div class="note"><b>הגשת בקשה אינה אישור אוטומטי לקבלת ההטבה.</b>
    הזכאות תיבדק לפי הקריטריונים שנקבעו בחוק ובהתאם למסמכים שהוגשו.</div>
</section>

<section>
  <h2><span class="num">11</span> אחרי שהגשת</h2>
  <p>{esc(after['lead'])}</p>
  <ul class="pts">{''.join(f'<li>{esc(p)}</li>' for p in after['points'])}</ul>
  {figure('05-form-confirmation.png', caption=esc(confirm['cap']))}
</section>
"""


os.makedirs(OUT, exist_ok=True)
for key, (size_css, label) in SIZES.items():
    MOBILE = key == 'mobile'
    doc = ("<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'>"
           f"<style>{CSS_COMMON}{size_css}</style></head><body>{body_html()}</body></html>")
    hp = os.path.join(OUT, f'guide-{key}.html')
    pdf = os.path.join(OUT, f'מדריך מצפן זכויות איבה - {label}.pdf')
    open(hp, 'w', encoding='utf-8').write(doc)
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu',
                    '--no-pdf-header-footer', f'--print-to-pdf={pdf}',
                    '--virtual-time-budget=20000', 'file://' + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('wrote', os.path.relpath(pdf, ROOT), f'{os.path.getsize(pdf)/1e6:.1f} MB')
