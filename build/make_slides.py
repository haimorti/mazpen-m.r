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
OUT = os.path.join(ROOT, 'build', 'out')
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


def shot_uri(name, crop=None, zoom=None):
    """Screenshot as a data URI. `crop` keeps the top/bottom 55%; `zoom` takes a
    fractional {x,y,w,h} box and upscales it with LANCZOS for the sharpest result."""
    im = Image.open(os.path.join(SHOTS, name)).convert('RGB')
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
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), im.size


LOGO, _ = shot_uri('logo-rehab-division.png')

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
.shot{position:relative;display:inline-block;line-height:0}
.shot.fill{width:1792px}
.shot.fill img{width:100%;max-width:none;height:auto}
.hl{position:absolute;border:5px solid #DC2626;border-radius:10px;
  box-shadow:0 0 0 5px rgba(220,38,38,.16)}
.cap{position:absolute;right:64px;left:64px;bottom:60px;min-height:120px;background:#16202B;color:#fff;
  border-radius:16px;padding:24px 40px;font-size:38px;line-height:1.4;display:flex;flex-direction:column;
  justify-content:center;gap:8px}
.cap .ct{font-family:'Rubik';font-weight:600;font-size:32px;color:#9EC5EE}
.cap .bul{display:flex;gap:18px;align-items:flex-start}
.cap .bul::before{content:'\\2022';color:#9EC5EE;flex:none}

.center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:40px;padding:0 200px;text-align:center}
.center img{height:140px}
.center h1{font-family:'Rubik';font-weight:700;font-size:100px;margin:0;color:#14477E;line-height:1.1;letter-spacing:-.02em}
.center .sub{font-size:44px;color:#4A5C70;font-weight:600}

.body{position:absolute;top:132px;right:120px;left:120px;bottom:80px;display:flex;flex-direction:column;justify-content:center}
.lead{font-size:46px;font-weight:600;color:#14477E;margin-bottom:38px;line-height:1.3}
.pt{display:flex;align-items:flex-start;gap:28px;font-size:42px;line-height:1.35;margin-bottom:30px}
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


def render(scene, total):
    n = scene['n']
    k = f"<span class='k'>{n} / {total}</span>"
    t = scene['type']
    head = f"<div class='top'><span class='t'>{esc(scene.get('title',''))}</span>{k}</div>"

    if t == 'title':
        body = (f"<div class='center'><img src='{LOGO}' alt=''>"
                f"<h1>{esc(scene['title'])}</h1><div class='sub'>{esc(scene['sub'])}</div></div>")
    elif t == 'points':
        lead = f"<div class='lead'>{esc(scene['lead'])}</div>" if scene.get('lead') else ''
        pts = ''.join(f"<div class='pt'><i>{i+1}</i><span>{esc(p)}</span></div>"
                      for i, p in enumerate(scene['points']))
        body = head + f"<div class='body'>{lead}{pts}</div>"
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
    else:  # shot
        src, _ = shot_uri(scene['img'], scene.get('crop'), scene.get('zoom'))
        hl = scene.get('highlight')
        hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;"
                  f"width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
        fill = ' fill' if scene.get('fill') or scene.get('zoom') else ''
        img = f"<div class='shot{fill}'><img src='{src}' alt=''>{hl_div}</div>"
        cap = esc(scene['cap'])
        if scene.get('cap_title'):
            cap = f"<div class='ct'>{esc(scene['cap_title'])}:</div><div class='bul'><span>{cap}</span></div>"
        body = head + f"<div class='stage'><div class='frame'>{img}</div></div><div class='cap'>{cap}</div>"

    hpath = os.path.join(SLIDES, f"{n:02d}.html")
    ppath = os.path.join(SLIDES, f"{n:02d}.png")
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


scenes = json.load(open(os.path.join(ROOT, 'build', 'scenes.json'), encoding='utf-8'))
total = len(scenes)
concat, srt, t = [], [], 0.0
for idx, s in enumerate(scenes):
    s['n'] = idx + 1
    p = render(s, total)
    print('rendered', os.path.basename(p))
    concat.append(f"file '{p}'\nduration {s['dur']}")
    srt.append(f"{s['n']}\n{srt_time(t + 0.3)} --> {srt_time(t + s['dur'] - 0.3)}\n{s['vo']}\n")
    t += s['dur']
concat.append(f"file '{p}'")  # repeat last frame so its duration is honored
open(os.path.join(OUT, 'concat.txt'), 'w', encoding='utf-8').write('\n'.join(concat) + '\n')
open(os.path.join(OUT, 'subtitles.srt'), 'w', encoding='utf-8').write('\n'.join(srt))
print(f'total {t:.0f}s, {total} slides at {W*SCALE}x{H*SCALE}')
