#!/usr/bin/env python3
"""Render the video scenes (build/scenes.json) into 1920x1080 PNG slides,
an ffmpeg concat list, and an SRT subtitle file.

Usage: python3 build/make_slides.py [--chrome /path/to/chrome]
Output: build/out/slides/NN.png, build/out/concat.txt, build/out/subtitles.srt
"""
import base64, json, os, subprocess, sys, shutil, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'out')
SLIDES = os.path.join(OUT, 'slides')
SHOTS = os.path.join(ROOT, 'source', 'screenshots')
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

def data_uri(name, crop=None):
    """PNG as a data URI. crop='top'/'bottom' keeps the top/bottom 55% of the image (needs Pillow)."""
    path = os.path.join(SHOTS, name)
    if crop:
        from PIL import Image
        import io
        im = Image.open(path); w, h = im.size; keep = int(h * 0.55)
        box = (0, 0, w, keep) if crop == 'top' else (0, h - keep, w, h)
        buf = io.BytesIO(); im.crop(box).save(buf, 'PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    with open(path, 'rb') as f:
        return 'data:image/png;base64,' + base64.b64encode(f.read()).decode()

LOGO = data_uri('logo-rehab-division.png')

CSS = """
*{box-sizing:border-box}
html,body{margin:0;width:1920px;height:1080px;background:#F3F7FB;color:#1B2734;position:relative;
  font-family:'Heebo','DejaVu Sans','Arial',sans-serif;direction:rtl;text-align:right}
.top{position:absolute;top:0;right:0;left:0;height:96px;background:#1B4F8A;color:#fff;display:flex;align-items:center;
  justify-content:space-between;padding:0 64px;font-size:30px}
.top .t{font-weight:700;font-size:38px}
.top .k{opacity:.85;font-variant-numeric:tabular-nums;direction:ltr}
.stage{position:absolute;top:120px;right:64px;left:64px;bottom:230px;display:flex;align-items:center;justify-content:center}
.frame{max-width:100%;max-height:100%;background:#fff;border:1px solid #D3DEE9;border-radius:12px;
  box-shadow:0 12px 40px rgba(27,39,52,.14);overflow:hidden}
.frame img{display:block;max-width:1792px;max-height:730px;width:auto;height:auto}
.shot{position:relative;display:inline-block;line-height:0}
.shot.fill{width:1792px}
.shot.fill img{width:100%;max-width:none;height:auto}
.hl{position:absolute;border:6px solid #E0261F;border-radius:10px;box-shadow:0 0 0 4px rgba(224,38,31,.18),0 0 24px rgba(224,38,31,.35)}
.cap{position:absolute;right:64px;left:64px;bottom:56px;min-height:110px;background:#1B2734;color:#fff;border-radius:12px;
  padding:22px 40px;font-size:38px;line-height:1.4;display:flex;flex-direction:column;justify-content:center;gap:6px}
.cap .ct{font-weight:700;font-size:34px;color:#BFD7F0}
.cap .bul{display:flex;gap:18px;align-items:flex-start}
.cap .bul::before{content:'•';color:#BFD7F0;flex:none}
.center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:36px;padding:0 200px;text-align:center}
.center img{height:150px}
.center h1{font-family:'Frank Ruhl Libre','DejaVu Serif',serif;font-size:96px;margin:0;color:#1B4F8A;line-height:1.15}
.center .sub{font-size:44px;color:#4F6073}
.pts{position:absolute;top:120px;right:160px;left:160px;bottom:120px;display:flex;flex-direction:column;justify-content:center;gap:44px}
.pts h1{font-family:'Frank Ruhl Libre','DejaVu Serif',serif;font-size:80px;margin:0 0 20px;color:#1B4F8A}
.pt{display:flex;align-items:center;gap:32px;font-size:52px;line-height:1.3}
.pt i{flex:none;width:72px;height:72px;border-radius:50%;background:#1B4F8A;color:#fff;display:grid;place-items:center;font-style:normal;font-weight:700;font-size:40px}
.brand{position:absolute;bottom:20px;left:64px;font-size:22px;color:#4F6073}
"""

def page(body):
    return f"<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}<div class='brand'>הביטוח הלאומי · אגף שיקום</div></body></html>"

def render(scene, total):
    n = scene['n']; k = f"<span class='k'>{n} / {total}</span>"
    t = scene['type']
    if t == 'title':
        body = f"<div class='center'><img src='{LOGO}' alt=''><h1>{html.escape(scene['title'])}</h1><div class='sub'>{html.escape(scene['sub'])}</div></div>"
    elif t == 'points':
        pts = ''.join(f"<div class='pt'><i>{i+1}</i><span>{html.escape(p)}</span></div>" for i, p in enumerate(scene['points']))
        body = f"<div class='top'><span class='t'>{html.escape(scene['title'])}</span>{k}</div><div class='pts'>{pts}</div>"
    else:
        src = data_uri(scene['img'], scene.get('crop'))
        hl = scene.get('highlight')
        hl_div = (f"<div class='hl' style='left:{hl['x']}%;top:{hl['y']}%;width:{hl['w']}%;height:{hl['h']}%'></div>" if hl else '')
        fill = ' fill' if scene.get('fill') else ''
        img = f"<div class='shot{fill}'><img src='{src}' alt=''>{hl_div}</div>"
        cap = html.escape(scene['cap'])
        cap = (f"<div class='ct'>{html.escape(scene['cap_title'])}:</div><div class='bul'><span>{cap}</span></div>"
               if scene.get('cap_title') else cap)
        body = (f"<div class='top'><span class='t'>{html.escape(scene['title'])}</span>{k}</div>"
                f"<div class='stage'><div class='frame'>{img}</div></div>"
                f"<div class='cap'>{cap}</div>")
    hpath = os.path.join(SLIDES, f"{n:02d}.html")
    ppath = os.path.join(SLIDES, f"{n:02d}.png")
    with open(hpath, 'w', encoding='utf-8') as f:
        f.write(page(body))
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                    '--window-size=1920,1200', f'--screenshot={ppath}', 'file://' + hpath],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    # headless chromium's viewport is shorter than its window; crop to the exact 1920x1080 frame
    try:
        from PIL import Image
        im = Image.open(ppath); im.crop((0, 0, 1920, 1080)).save(ppath)
    except ImportError:
        pass
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
print(f'total {t:.0f}s, {total} slides')
