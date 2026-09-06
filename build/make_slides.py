#!/usr/bin/env python3
"""Render the video scenes (build/scenes.json) into 3840x2160 PNG slides,
an ffmpeg concat list, and an SRT subtitle file.

Slides render at 2x device scale so all text is crisp when the video is
downscaled to 1080p, or when a slide is viewed full-screen.

Usage: python3 build/make_slides.py [--chrome /path/to/chrome]
Output: build/out/slides/NN.png, build/out/concat.txt, build/out/subtitles.srt
"""
import base64, io, json, os, subprocess, sys, shutil, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES_FILE = 'scenes.json'                    # a second guide lives in its own scenes file
if '--scenes' in sys.argv:
    SCENES_FILE = sys.argv[sys.argv.index('--scenes') + 1]
NAME = os.path.splitext(os.path.basename(SCENES_FILE))[0]
OUT = os.path.join(ROOT, 'build', 'out')
if NAME != 'scenes':
    OUT = os.path.join(OUT, NAME)
SLIDES = os.path.join(OUT, 'slides')
SHOTS = os.path.join(ROOT, 'source', 'screenshots')
FONTS = os.path.join(ROOT, 'build', 'fonts')
SCALE = 2                      # device pixel ratio; slides come out 3840x2160
W, H = 1920, 1080              # logical slide size
os.makedirs(SLIDES, exist_ok=True)

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


def font_face(family, weight, filename):
    """@font-face with the .ttf inlined, so slides render identically offline."""
    with open(os.path.join(FONTS, filename), 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


FONT_CSS = ''.join([
    font_face('Assistant', 400, 'AssistantRegular.ttf'),
    font_face('Assistant', 600, 'AssistantSemiBold.ttf'),
    font_face('Assistant', 700, 'AssistantBold.ttf'),
    font_face('Rubik', 500, 'RubikMedium.ttf'),
    font_face('Rubik', 600, 'RubikSemiBold.ttf'),
    font_face('Rubik', 700, 'RubikBold.ttf'),
])


def load_shot(name, bg='white'):
    """Open a screenshot, flattening transparency onto white (a plain convert('RGB')
    turns transparent pixels black, which is how the logo came out on a black card)."""
    im = Image.open(os.path.join(SHOTS, name))
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        flat = Image.new('RGB', im.size, bg)
        flat.paste(im, mask=im.split()[-1])
        return flat
    return im.convert('RGB')


def to_uri(im):
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def spotlight(im, band, dim=0.45, blur=6):
    """Full screenshot with everything outside the band blurred and dimmed, so the
    band the narration is talking about reads as lifted out of the page."""
    from PIL import ImageFilter, ImageEnhance
    w, h = im.size
    y0, y1 = int(band['y'] * h), int((band['y'] + band['h']) * h)
    back = im.filter(ImageFilter.GaussianBlur(blur))
    back = ImageEnhance.Brightness(back).enhance(1 - dim)
    back = ImageEnhance.Color(back).enhance(0.45)
    out = back.copy()
    out.paste(im.crop((0, y0, w, y1)), (0, y0))
    return out


MAX_W, MAX_H, MAX_UPSCALE = 1792, 700, 1.25
BIG_H, BIG_UPSCALE = 750, 1.45          # scenes marked "big": slim caption, taller stage


def fit(im, big=False):
    """Display size for a screenshot: fits the stage, and never enlarges the source
    by more than a quarter, so nothing looks stretched or soft. A "big" scene trades
    caption height for stage height, so a dense screen reads at close to 1:1."""
    mh, mu = (BIG_H, BIG_UPSCALE) if big else (MAX_H, MAX_UPSCALE)
    w = min(MAX_W, im.width * mu, im.width * mh / im.height)
    return round(w), round(w * im.height / im.width)


def cursor_track(scene, waypoints, big=False):
    """Fractional waypoints on the screenshot -> pixels on the 1920x1080 slide."""
    im = shot_im(scene)
    dw, dh = fit(im, big)                      # same size the slide renders it at
    left, top = (1920 - dw) / 2, 132 + ((762 if big else stage_h(scene)) - dh) / 2
    return {'cursor': [{'t': w['t'], 'x': round(left + w['x'] * dw),
                        'y': round(top + w['y'] * dh), 'click': bool(w.get('click'))}
                       for w in waypoints]}


def stage_h(scene):
    """Logical height of the stage box, which the cursor track has to agree with."""
    return 762 if scene.get('big') else 712


def ink_bbox(im, thr=246, pad=8):
    """Bounding box of everything that isn't page background, with a small margin."""
    dark = im.convert('L').point(lambda v: 255 if v < thr else 0)
    bb = dark.getbbox()
    if not bb:
        return (0, 0, im.width, im.height)
    return (max(0, bb[0] - pad), max(0, bb[1] - pad),
            min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))


def shot_im(scene):
    """The screenshot exactly as the slide shows it: cropped, but not yet spotlit."""
    im = load_shot(scene['img'])
    if scene.get('trim'):                  # a capture with wide empty margins
        im = im.crop(ink_bbox(im))
    if scene.get('keep') or scene.get('keepx'):
        im = im.crop((0, 0, int(im.width * scene.get('keepx', 1.0)),
                      int(im.height * scene.get('keep', 1.0))))
    elif scene.get('crop'):
        k = int(im.height * 0.55)
        im = im.crop((0, 0, im.width, k) if scene['crop'] == 'top' else (0, im.height - k, im.width, im.height))
    return im


def shot_uri(name, crop=None, zoom=None):
    """Screenshot as a data URI. `crop` keeps the top/bottom 55%; `zoom` takes a
    fractional {x,y,w,h} box and upscales it with LANCZOS for the sharpest result."""
    im = load_shot(name)
    w, h = im.size
    if zoom:
        box = (int(zoom.get('x', 0) * w), int(zoom['y'] * h),
               int((zoom.get('x', 0) + zoom.get('w', 1)) * w), int((zoom['y'] + zoom['h']) * h))
        im = im.crop(box)
        target = 1700 * SCALE
        if im.width < target:
            im = im.resize((target, round(im.height * target / im.width)), Image.LANCZOS)
    elif crop:
        keep = int(h * 0.55)
        im = im.crop((0, 0, w, keep) if crop == 'top' else (0, h - keep, w, h))
    return to_uri(im), im.size


LOGO = to_uri(load_shot('logo-rehab-division.png', bg='#F2F6FA'))   # match the slide ground

CSS = FONT_CSS + """
*{box-sizing:border-box}
html{margin:0}
body{margin:0;position:relative;width:1920px;height:1080px;overflow:hidden;background:#F2F6FA;color:#16202B;
  font-family:'Assistant','DejaVu Sans',sans-serif;direction:rtl;text-align:right;
  -webkit-font-smoothing:antialiased}
.top{position:absolute;top:0;right:0;left:0;height:100px;background:#14477E;color:#fff;display:flex;
  align-items:center;justify-content:space-between;padding:0 64px}
.top .t{font-family:'Rubik';font-weight:600;font-size:40px;letter-spacing:-.01em}
.top .k{opacity:.75;font-variant-numeric:tabular-nums;direction:ltr;font-size:28px;font-weight:600}
.stage{position:absolute;top:132px;right:64px;left:64px;bottom:236px;display:flex;align-items:center;justify-content:center}
.frame{max-width:100%;max-height:100%;background:#fff;border-radius:16px;
  box-shadow:0 2px 4px rgba(20,34,54,.06),0 18px 50px rgba(20,34,54,.14);overflow:hidden;line-height:0}
.frame img{display:block;max-width:1792px;max-height:700px;width:auto;height:auto}
.zwrap{position:relative;line-height:0}
.zwrap img{display:block;width:100%;max-width:none;max-height:none;height:auto}
.zback.dim{filter:blur(7px) brightness(.55) saturate(.5)}
.zbox{position:absolute;border:5px solid var(--zc);border-radius:12px;box-shadow:0 0 0 4px rgba(255,255,255,.55)}
.zn{position:absolute;top:50%;right:-30px;transform:translate(50%,-50%);width:52px;height:52px;border-radius:50%;
  background:#fff;border:5px solid var(--zc);color:var(--zc);font-family:'Rubik';font-weight:700;font-size:28px;
  display:grid;place-items:center;line-height:1}
.zlab.out{left:auto;right:calc(100% + 14px);max-width:none;width:320px;font-size:21px}
.zlab.top{top:14px;transform:none}
.zlab{position:absolute;top:50%;left:12px;transform:translateY(-50%);max-width:42%;background:#fff;
  border:3px solid var(--zc);border-radius:10px;color:var(--zc);font-size:22px;font-weight:700;line-height:1.25;
  padding:8px 14px;text-align:right;white-space:normal}
.slist{position:absolute;top:116px;right:56px;left:56px;bottom:34px;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:18px}
.snote{font-size:29px;font-weight:700;color:#16202B;text-align:center;line-height:1.35;min-height:82px;max-width:1600px;display:flex;align-items:center;justify-content:center}
.scards{display:flex;gap:14px;width:100%}
.scard{flex:1;background:#fff;border-radius:14px;padding:14px 12px;display:flex;flex-direction:column;
  align-items:center;gap:8px;box-shadow:0 2px 10px rgba(20,34,54,.07);border:4px solid transparent}
.scard.dim{opacity:.4}
.scard.lit{border-color:#DC2626;box-shadow:0 8px 26px rgba(20,34,54,.16)}
.scard p{margin:0;font-size:24px;line-height:1.3;text-align:center;color:#3C4C60}
.split{position:absolute;top:126px;right:56px;left:56px;bottom:40px;display:flex;gap:40px;align-items:center}
.sleg{flex:1;display:flex;flex-direction:column;gap:12px}
.srow{background:#fff;border-radius:14px;padding:16px 20px;display:flex;gap:18px;align-items:flex-start;
  box-shadow:0 2px 10px rgba(20,34,54,.07)}
.srow.dim{opacity:.42}
.srow.lit{box-shadow:0 0 0 4px #14477E,0 10px 30px rgba(20,34,54,.18)}
.spill{flex:none;min-width:150px;text-align:center;background:var(--b);color:var(--c);border-radius:999px;
  padding:7px 16px;font-weight:700;font-size:27px}
.stxt p{margin:0;font-size:27px;line-height:1.35}
.stxt .sdo{color:#4A5C70;font-size:24px;margin-top:4px}
.stxt .sdo b{color:#16202B}
.fhint{position:absolute;top:118px;right:60px;left:60px;text-align:center;font-size:31px;font-weight:700}
.fcol{position:absolute;top:176px;bottom:34px;width:870px;display:flex;flex-direction:column;align-items:center;gap:0}
.fcol.right{right:60px}
.fcol.left{left:60px}
.fbtn{flex:none;width:420px;line-height:0;border-radius:12px;overflow:hidden;border:5px solid transparent}
.fbtn.on{border-color:#DC2626;box-shadow:0 0 0 5px rgba(220,38,38,.20)}
.fbtn img{display:block;width:100%}
.fsaid{flex:none;margin-top:12px;font-size:25px;color:#3C4C60;text-align:center;line-height:1.3;height:64px}
.fsaid b{color:var(--c)}
.fdrop{visibility:hidden;flex:1;min-height:0;width:100%;display:flex;flex-direction:column;align-items:center;gap:6px}
.fdrop.show{visibility:visible}
.farrow{color:var(--c);font-size:40px;font-weight:700;line-height:1}
.fdest{font-family:'Rubik';font-weight:600;font-size:28px;color:var(--c);text-align:center}
.fscr{margin-top:6px;flex:1;min-height:0;width:100%;line-height:0;
  display:flex;align-items:flex-start;justify-content:center}
.fscr img{display:block;max-width:100%;max-height:100%;width:auto;height:auto;
  box-sizing:border-box;border-radius:10px;border:3px solid var(--c);background:#fff}
.cmp{position:absolute;top:124px;right:60px;left:60px;bottom:40px;display:flex;flex-direction:column;gap:20px;
  justify-content:center}
.chint{font-size:32px;font-weight:700;color:#16202B;text-align:center}
.crow{border-radius:16px;border:3px solid var(--c);background:#fff;padding:16px 18px;display:flex;
  flex-direction:column;gap:10px;box-shadow:0 6px 22px rgba(20,34,54,.10)}
.chead{display:flex;align-items:baseline;gap:16px}
.cname{background:var(--c);color:#fff;border-radius:10px;padding:6px 18px;font-family:'Rubik';font-weight:600;font-size:28px}
.cgoes{color:var(--c);font-size:27px;font-weight:700}
.cshot{position:relative;line-height:0;border-radius:10px;overflow:hidden}
.cshot img{display:block;width:100%;max-width:none;max-height:none;height:auto}
.cnote{font-size:26px;color:#3C4C60;line-height:1.35}
.pair{position:absolute;top:132px;right:56px;left:56px;bottom:60px;display:flex;gap:44px;align-items:center}
.pcol{flex:1;display:flex;flex-direction:column;gap:18px;align-items:center}
.ptag{background:var(--c);color:#fff;border-radius:12px;padding:10px 30px;font-family:'Rubik';font-weight:600;font-size:34px}
.plead{color:var(--c);font-size:30px;font-weight:700;text-align:center;line-height:1.3}
.pcol .frame{width:100%}
.pcol .shot{width:100%}
.shot{position:relative;line-height:0}
.shot img{display:block;width:100%;max-width:none;max-height:none;height:auto}
.hl{position:absolute;border:5px solid #DC2626;border-radius:10px;
  box-shadow:0 0 0 5px rgba(220,38,38,.16)}
.stage.tall{bottom:186px}
.cap.slim{bottom:52px;min-height:106px;font-size:32px;padding:14px 34px}
.cap{position:absolute;right:64px;left:64px;bottom:60px;min-height:120px;background:#16202B;color:#fff;
  border-radius:16px;padding:24px 40px;font-size:38px;line-height:1.4;display:flex;flex-direction:column;
  justify-content:center;gap:8px}
.cap .ct{font-family:'Rubik';font-weight:600;font-size:32px;color:#9EC5EE}
.cap .bul{display:flex;gap:18px;align-items:flex-start}
.cap .bul::before{content:'\\2022';color:#9EC5EE;flex:none}

.center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:24px;padding:0 200px;text-align:center}
.mark{position:absolute;top:64px;right:80px;height:110px}
.center h1{font-family:'Rubik';font-weight:700;font-size:100px;margin:0;color:#14477E;line-height:1.1;letter-spacing:-.02em}
.center .sub{font-size:44px;color:#4A5C70;font-weight:600}

.body{position:absolute;top:132px;right:120px;left:120px;bottom:80px;display:flex;flex-direction:column;justify-content:center}
.hero{font-family:'Rubik';font-weight:700;font-size:76px;color:#14477E;text-align:center;margin:0 0 44px;
  line-height:1.15;letter-spacing:-.02em}
.lead{font-size:40px;font-weight:700;color:#16202B;margin-bottom:30px;line-height:1.3}
.pt{display:flex;align-items:flex-start;gap:28px;font-size:40px;line-height:1.35;margin-bottom:26px}
.pt{color:#4A5C70;border-radius:14px;padding:6px 14px;margin-right:-14px}
.pt.on{color:#16202B;font-weight:600;background:#E4EDF7}
.pt.on i{background:#DC7B1E}
.pt i{flex:none;width:56px;height:56px;border-radius:16px;background:#14477E;color:#fff;display:grid;
  place-items:center;font-style:normal;font-family:'Rubik';font-weight:600;font-size:30px;margin-top:4px}

.cards{display:flex;gap:36px;align-items:stretch;justify-content:center}
.card{flex:1;background:#fff;border-radius:20px;padding:36px 38px;
  box-shadow:0 2px 4px rgba(20,34,54,.05),0 14px 40px rgba(20,34,54,.10);border-top:8px solid var(--c,#14477E);
  display:flex;flex-direction:column;gap:18px}
.card h2{font-family:'Rubik';font-weight:600;font-size:38px;margin:0;color:var(--c,#14477E);line-height:1.2}
.card p{margin:0;font-size:32px;line-height:1.4;color:#3C4C60}
.card ul{margin:0;padding:0 26px 0 0;font-size:30px;line-height:1.45;color:#3C4C60}
.card li{margin-bottom:10px}
.btn{display:inline-flex;align-items:center;gap:12px;background:var(--c,#14477E);color:#fff;border-radius:12px;
  padding:12px 28px;font-size:30px;font-weight:700;align-self:flex-start}

.flow{display:flex;align-items:stretch;gap:0;justify-content:center}
.fstep{flex:1;background:#fff;border-radius:20px;padding:32px 34px;display:flex;flex-direction:column;gap:14px;
  box-shadow:0 2px 4px rgba(20,34,54,.05),0 14px 40px rgba(20,34,54,.10)}
.fstep .n{font-family:'Rubik';font-weight:600;font-size:26px;color:#fff;background:#14477E;width:48px;height:48px;
  border-radius:14px;display:grid;place-items:center}
.fstep h2{font-family:'Rubik';font-weight:600;font-size:36px;margin:0;color:#14477E}
.fstep p{margin:0;font-size:29px;line-height:1.4;color:#3C4C60}
.arrow{flex:none;width:70px;display:grid;place-items:center;color:#8FA6BE;font-size:56px}

.chips{display:flex;flex-wrap:wrap;gap:18px;justify-content:center;max-width:1600px;margin:0 auto}
.chip{background:#fff;border:2px solid #D9C7EE;color:#4A2E73;border-radius:14px;padding:14px 24px;font-size:30px;
  font-weight:600}
.fields{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.field{background:#fff;border-radius:14px;padding:18px 26px;font-size:30px;box-shadow:0 2px 10px rgba(20,34,54,.08);display:flex;flex-direction:column;justify-content:center;min-height:96px}
.field b{color:#14477E}
.field .req{color:#DC2626;font-weight:700}
.brand{position:absolute;bottom:26px;left:64px;font-size:22px;line-height:1;color:#7488A0;font-weight:600}
"""


def page(body):
    return ("<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'>"
            f"<style>{CSS}</style></head><body>{body}"
            "<div class='brand'>הביטוח הלאומי · אגף שיקום</div></body></html>")


def esc(s):
    return html.escape(s)


def render(scene, total, step=None):
    n = scene['n']
    k = f"<span class='k'>{n} / {total}</span>"
    t = scene['type']
    head = f"<div class='top'><span class='t'>{esc(scene.get('title',''))}</span>{k}</div>"

    if t == 'title':
        body = (f"<img class='mark' src='{LOGO}' alt=''>"
                f"<div class='center'><h1>{esc(scene['title'])}</h1>"
                + (f"<div class='sub'>{esc(scene['sub'])}</div>" if scene.get('sub') else '')
                + "</div>")
    elif t == 'points':
        hero = f"<h1 class='hero'>{esc(scene['hero'])}</h1>" if scene.get('hero') else ''
        lead = f"<div class='lead'>{esc(scene['lead'])}</div>" if scene.get('lead') else ''
        shown = scene.get('_shown', len(scene['points']))     # how many bullets are out yet
        mark = (lambda i: '&#8226;') if scene.get('nonum') else (lambda i: str(i + 1))
        pts = ''.join(
            f"<div class='pt{' on' if i + 1 == shown else ''}'><i>{mark(i)}</i>"
            f"<span>{esc(p)}</span></div>"
            for i, p in enumerate(scene['points']))
        body = head + f"<div class='body'>{hero}{lead}{pts}</div>"
    elif t == 'cards':
        cards = ''.join(
            f"<div class='card' style='--c:{c.get('color','#14477E')}'><h2>{esc(c['title'])}</h2>"
            + (f"<div class='btn'>{esc(c['btn'])}</div>" if c.get('btn') else '')
            + ''.join(f"<p>{esc(p)}</p>" for p in c.get('text', []))
            + (('<ul>' + ''.join(f"<li>{esc(li)}</li>" for li in c['list']) + '</ul>') if c.get('list') else '')
            + "</div>" for c in scene['cards'])
        body = head + f"<div class='body'><div class='cards'>{cards}</div></div>"
    elif t == 'flow':
        parts = []
        for i, s in enumerate(scene['steps']):
            if i:
                parts.append("<div class='arrow'>&#8592;</div>")
            parts.append(f"<div class='fstep'><div class='n'>{i+1}</div><h2>{esc(s['title'])}</h2>"
                         + ''.join(f"<p>{esc(p)}</p>" for p in s['text']) + "</div>")
        body = head + f"<div class='body'><div class='flow'>{''.join(parts)}</div></div>"
    elif t == 'chips':
        lead = f"<div class='lead' style='text-align:center'>{esc(scene['lead'])}</div>" if scene.get('lead') else ''
        chips = ''.join(f"<span class='chip'>{esc(c)}</span>" for c in scene['chips'])
        body = head + f"<div class='body'>{lead}<div class='chips'>{chips}</div></div>"
    elif t == 'fields':
        lead = f"<div class='lead'>{esc(scene['lead'])}</div>" if scene.get('lead') else ''
        fl = ''.join(f"<div class='field'><b>{esc(f['name'])}</b>"
                     + ("<span class='req'> *</span>" if f.get('req') else '')
                     + (f"<div style='font-size:26px;color:#5A6C82'>{esc(f['hint'])}</div>" if f.get('hint') else '')
                     + "</div>" for f in scene['fields'])
        note = f"<div class='pt' style='margin-top:34px'><i>!</i><span>{esc(scene['note'])}</span></div>" if scene.get('note') else ''
        body = head + f"<div class='body'>{lead}<div class='fields'>{fl}</div>{note}</div>"
    elif t == 'fork':
        step = scene.get('_step', 0)
        cols = []
        for side, c in zip(('right', 'left'), scene['cols']):
            im = load_shot(c['img']); w, h = im.size
            b = c['btn_box']
            btn = im.crop((int(b['x'] * w), int(b['y'] * h),
                           int((b['x'] + b['w']) * w), int((b['y'] + b['h']) * h)))
            if btn.width < 840:
                btn = btn.resize((840, round(btn.height * 840 / btn.width)), Image.LANCZOS)
            scr = load_shot(c['screen'])
            sc_h = c.get('screen_keep', 1.0)
            scr = scr.crop((0, 0, scr.width, int(scr.height * sc_h)))
            open_now = step >= c['opens_at']
            marked = scene['mark'][step] == side
            cols.append(
                f"<div class='fcol {side}' style='--c:{c['color']}'>"
                f"<div class='fbtn{' on' if marked else ''}'><img src='{to_uri(btn)}' alt=''></div>"
                f"<div class='fsaid'>{c['said']}</div>"
                f"<div class='fdrop{' show' if open_now else ''}'>"
                f"<div class='farrow'>&#8595;</div><div class='fdest'>{esc(c['dest'])}</div>"
                f"<div class='fscr'><img src='{to_uri(scr)}' alt=''></div></div></div>")
        body = (head + f"<div class='fhint'>{esc(scene['hint'])}</div>" + ''.join(cols))
    elif t == 'compare':
        rows = []
        for r in scene['rows']:
            im = load_shot(r['img'])
            b = r['box']
            w, h = im.size
            im = im.crop((int(b['x'] * w), int(b['y'] * h),
                          int((b['x'] + b['w']) * w), int((b['y'] + b['h']) * h)))
            tw = 1690
            if im.width < tw:
                im = im.resize((tw, round(im.height * tw / im.width)), Image.LANCZOS)
            hl = r.get('highlight')
            hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;"
                      f"width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
            rows.append(
                f"<div class='crow' style='--c:{r['color']}'>"
                f"<div class='chead'><span class='cname'>{esc(r['title'])}</span>"
                f"<span class='cgoes'>{esc(r['leads'])}</span></div>"
                f"<div class='cshot'><img src='{to_uri(im)}' alt=''>{hl_div}</div>"
                f"<div class='cnote'>{esc(r['note'])}</div></div>")
        body = (head + f"<div class='cmp'><div class='chint'>{esc(scene['hint'])}</div>"
                + ''.join(rows) + "</div>")
    elif t == 'pair':
        cols = []
        for c in scene['cols']:
            im = load_shot(c['img'])
            hl = c.get('highlight')
            hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;"
                      f"width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
            cols.append(
                f"<div class='pcol'><div class='ptag' style='--c:{c.get('tagcolor', c['color'])}'>{esc(c['btn'])}</div>"
                f"<div class='frame'><div class='shot'><img src='{to_uri(im)}' alt=''>{hl_div}</div></div>"
                f"<div class='plead' style='--c:{c['color']}'>{esc(c['leads'])}</div></div>")
        body = head + f"<div class='pair'>{''.join(cols)}</div>"
    elif t == 'walk':
        st = scene['steps'][scene.get('_step', 0)]
        big = bool(scene.get('big'))
        im = shot_im(scene)
        if st.get('focus'):
            im = spotlight(im, st['focus'], dim=0.42, blur=6)
        sw, sh = fit(im, big)
        hl = st.get('highlight')
        hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;"
                  f"width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
        cap = esc(st['cap'])
        if st.get('cap_title'):
            cap = f"<div class='ct'>{esc(st['cap_title'])}:</div><div class='bul'><span>{cap}</span></div>"
        body = (head + f"<div class='stage{' tall' if big else ''}'><div class='frame'>"
                f"<div class='shot' style='width:{sw}px'>"
                f"<img src='{to_uri(im)}' alt=''>{hl_div}</div></div></div>"
                f"<div class='cap{' slim' if big else ''}'>{esc(st['cap'])}</div>")
    elif t == 'statuslist':
        im = shot_im(scene)
        phase = scene.get('_phase', 'cards')
        if phase != 'cards':
            sw, sh = fit(im, True)
            body = (head + "<div class='stage tall'><div class='frame'>"
                    f"<div class='shot' style='width:{sw}px'><img src='{to_uri(im)}' alt=''></div>"
                    f"</div></div><div class='cap slim'>{esc(scene[phase]['cap'])}</div>")
        else:
            act = scene.get('_lit')
            cur = scene['items'][act - 1]
            hl = cur.get('on_screen')
            hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;"
                      f"width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
            sw = round(min(MAX_W, im.width * 1.3, 650 * im.width / im.height))
            sh = round(sw * im.height / im.width)
            cards = ''.join(
                "<div class='scard" + (' lit' if act == i + 1 else ' dim') + "'>"
                f"<span class='spill' style='--c:{r['color']};--b:{r['bg']}'>{esc(r['key'])}</span>"
                f"<p>{esc(r['short'])}</p></div>"
                for i, r in enumerate(scene['items']))
            body = (head + "<div class='slist'>"
                    f"<div class='frame' style='width:{sw}px'><div class='shot' style='width:{sw}px'>"
                    f"<img src='{to_uri(im)}' alt=''>{hl_div}</div></div>"
                    f"<div class='snote'>{esc(cur['note'])}</div>"
                    f"<div class='scards'>{cards}</div></div>")
    elif t == 'zones':
        zim = shot_im(scene)
        act = scene.get('active')            # 1-based zone to spotlight; None = show them all
        if act:
            b = [z for z in scene['zones'] if z['n'] == act][0]['box']
            zim = spotlight(zim, {'y': max(0, b['y'] - 1.2) / 100,
                                  'h': min(100, b['h'] + 2.4) / 100}, dim=0.42, blur=6)
        zw, zh = fit(zim)
        src = to_uri(zim)
        boxes = ''.join(
            '' if act is not None and act != z['n'] else
            f"<div class='zbox' style='--zc:{z['color']};right:{z['box']['x']}%;top:{z['box']['y']}%;"
            f"width:{z['box']['w']}%;height:{z['box']['h']}%"
            + "'>"
            f"<span class='zn'>{z['n']}</span>"
            + ("<span class='zlab" + z.get('lab', '') + "'>" + esc(z['label']) + "</span>"
               if z.get('label') and (act is None or act == z['n']) else '')
            + "</div>" for z in scene['zones'])
        cap = esc(scene['cap'])
        if scene.get('cap_title'):
            cap = f"<div class='ct'>{esc(scene['cap_title'])}:</div><div class='bul'><span>{cap}</span></div>"
        body = (head + f"<div class='stage'><div class='frame zwrap' style='width:{zw}px'>"
                f"<img src='{src}' alt=''>{boxes}</div></div><div class='cap'>{cap}</div>")
    elif t == 'shot' and scene.get('focus'):
        im = load_shot(scene['img'])
        src = to_uri(spotlight(im, scene['focus']))
        cap = esc(scene['cap'])
        if scene.get('cap_title'):
            cap = f"<div class='ct'>{esc(scene['cap_title'])}:</div><div class='bul'><span>{cap}</span></div>"
        body = (head + f"<div class='stage'><div class='frame focus'><img src='{src}' alt=''></div></div>"
                f"<div class='cap'>{cap}</div>")
    else:  # shot
        big = bool(scene.get('big'))
        im = shot_im(scene)
        if scene.get('focus'):
            im = spotlight(im, scene['focus'])
        sw, sh = fit(im, big)
        hl = scene.get('highlight')
        hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;"
                  f"width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
        cap = esc(scene['cap'])
        if scene.get('cap_title'):
            cap = f"<div class='ct'>{esc(scene['cap_title'])}:</div><div class='bul'><span>{cap}</span></div>"
        body = (head + f"<div class='stage{' tall' if big else ''}'><div class='frame'>"
                f"<div class='shot' style='width:{sw}px'>"
                f"<img src='{to_uri(im)}' alt=''>{hl_div}</div></div></div>"
                f"<div class='cap{' slim' if big else ''}'>{cap}</div>")

    tag = f"{n:02d}" if step is None else f"{n:02d}{chr(97 + step)}"
    hpath = os.path.join(SLIDES, f"{tag}.html")
    ppath = os.path.join(SLIDES, f"{tag}.png")
    with open(hpath, 'w', encoding='utf-8') as f:
        f.write(page(body))
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                    f'--force-device-scale-factor={SCALE}', f'--window-size={W},{H+120}',
                    f'--screenshot={ppath}', 'file://' + hpath],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    im = Image.open(ppath)
    if im.size != (W * SCALE, H * SCALE):
        im.crop((0, 0, W * SCALE, H * SCALE)).save(ppath)
    os.remove(hpath)
    return ppath


def srt_time(s):
    ms = int(round(s * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


scenes = json.load(open(os.path.join(ROOT, 'build', SCENES_FILE), encoding='utf-8'))
total = len(scenes)
concat, srt, frames, t = [], [], [], 0.0
for idx, s in enumerate(scenes):
    s['n'] = idx + 1
    if s['type'] == 'walk':
        for k, st in enumerate(s['steps']):
            s['_step'] = k
            fp = render(s, total, step=k)
            frames.append((fp, st['dur'], None))
        p = fp
    elif s['type'] == 'fork':
        for k, fr in enumerate(s['frames']):
            s['_step'] = k
            fp = render(s, total, step=k)
            frames.append((fp, fr['dur'], {'cursor': fr['cursor']}))
        p = fp
    elif s['type'] == 'statuslist':
        # wide opening frame, then one frame per status, then a wide frame with the click
        seq = [('intro', None, s['intro']['dur'])] if s.get('intro') else []
        wide = sum(s[k]['dur'] for k in ('intro', 'outro') if s.get(k))
        share = (s['dur'] - wide) / len(s['items'])
        seq += [('cards', i + 1, share) for i in range(len(s['items']))]
        if s.get('outro'):
            seq.append(('outro', None, s['outro']['dur']))
        for k, (phase, lit, d) in enumerate(seq):
            s['_phase'], s['_lit'] = phase, lit
            fp = render(s, total, step=k)
            frames.append((fp, d, cursor_track(s, s[phase]['cursor'], big=True)
                           if phase != 'cards' and s[phase].get('cursor') else None))
        p = fp
    elif s['type'] == 'points' and s.get('reveal'):
        # one frame per bullet: the list builds up as the narration reads it out
        n_steps = len(s['points'])
        share = s['dur'] / n_steps
        for k in range(n_steps):
            s['_shown'] = k + 1
            fp = render(s, total, step=k)
            frames.append((fp, share, None))
        p = fp
    else:
        p = render(s, total)
        frames.append((p, s['dur'], None))
    print('rendered', os.path.basename(p))
    m = None
    if s.get('cursor') and s.get('img'):
        m = cursor_track(s, s['cursor'], big=s.get('big'))
    elif s.get('focus') and not s.get('static'):
        im = load_shot(s['img'])
        disp_h = 1792 * im.height / im.width          # image height at the fixed focus layout
        top = 132 + (712 - disp_h) / 2                # stage box: top 132, height 712
        f = s['focus']
        cy = top + (f['y'] + f['h'] / 2) * disp_h     # band centre, logical px
        z = min(2.6, max(1.25, 712 / (f['h'] * disp_h)))
        m = {'slide': os.path.basename(p), 'dur': s['dur'], 'zoom': round(z, 3),
             'cx': round(960 * SCALE), 'cy': round(cy * SCALE)}
    if m:
        frames[-1] = (frames[-1][0], frames[-1][1], m)
    srt.append(f"{s['n']}\n{srt_time(t + 0.3)} --> {srt_time(t + s['dur'] - 0.3)}\n{s['vo']}\n")
    t += s['dur']
for fp, d, _ in frames:
    concat.append(f"file '{fp}'\nduration {d}")
concat.append(f"file '{frames[-1][0]}'")  # repeat last frame so its duration is honored
open(os.path.join(OUT, 'concat.txt'), 'w', encoding='utf-8').write('\n'.join(concat) + '\n')
open(os.path.join(OUT, 'subtitles.srt'), 'w', encoding='utf-8').write('\n'.join(srt))
tl = [{'slide': os.path.basename(fp), 'dur': d, **({'motion': m} if m else {})}
      for fp, d, m in frames]
json.dump(tl,
          open(os.path.join(OUT, 'timeline.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'total {t:.0f}s, {total} slides at {W*SCALE}x{H*SCALE}')
