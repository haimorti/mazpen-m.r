#!/usr/bin/env python3
"""Build the narration script for a guide video: one line per frame, with the
timecode it starts at and how long it has to be read in.

Usage: python3 build/make_narration.py [--scenes scenes.json]
Output: video/<name>-narration.md, and a print-ready PDF beside the guides.
"""
import json, os, subprocess, sys, shutil, html, base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration
from narration import ROOT, tc

SCENES = sys.argv[sys.argv.index('--scenes') + 1] if '--scenes' in sys.argv else 'scenes.json'
STEM = os.path.splitext(os.path.basename(SCENES))[0]
OUT = os.path.join(ROOT, 'build', 'out') if STEM == 'scenes' \
    else os.path.join(ROOT, 'build', 'out', STEM)
FONTS = os.path.join(ROOT, 'build', 'fonts')
esc = html.escape
rows, t, scenes = narration.rows(SCENES)

# ---------------------------------------------------------------- markdown
md = [f'# קריינות — {scenes[0]["title"]}', '',
      f'אורך הסרטון: {tc(t)}. {len(scenes)} שקפים, {len(rows)} כניסות קריינות.', '',
      'קצב הקריאה שלפיו חושבו ההערכות: 2.6 מילים בשנייה — קצב רגוע, מתאים לקהל.', '']
last = None
for r in rows:
    if r['n'] != last:
        md += ['', f'## {r["n"]}. {r["title"]}', '']
        last = r['n']
    tag = f'{tc(r["at"])} ({r["dur"]:g}ש)'
    warn = '  ⚠️ צפוף' if r['tight'] else ''
    md.append(f'**{tag}**{warn}  \n{r["text"]}')
    md.append('')
open(os.path.join(ROOT, 'video', f'{STEM}-narration.md'), 'w', encoding='utf-8')\
    .write('\n'.join(md) + '\n')

json.dump([{'i': i + 1, 'at': round(r['at'], 2), 'dur': r['dur'], 'text': r['text']}
           for i, r in enumerate(rows)],
          open(os.path.join(ROOT, 'video', f'{STEM}-narration.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- pdf
chrome = None
for c in ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome', shutil.which('chromium'),
          shutil.which('chromium-browser'), shutil.which('google-chrome')]:
    if c and os.path.exists(c):
        chrome = c; break


def font_face(family, weight, filename):
    with open(os.path.join(FONTS, filename), 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


CSS = ''.join([font_face('Assistant', 400, 'AssistantRegular.ttf'),
               font_face('Assistant', 600, 'AssistantSemiBold.ttf'),
               font_face('Assistant', 700, 'AssistantBold.ttf'),
               font_face('Rubik', 700, 'RubikBold.ttf')]) + """
@page{size:A4;margin:18mm 20mm}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:#16202B;direction:rtl;text-align:right;
  font-family:'Assistant',sans-serif;font-size:12pt;-webkit-print-color-adjust:exact}
h1{font-family:'Rubik';font-weight:700;font-size:24pt;color:#14477E;margin:0 0 .2em}
.meta{color:#4E6076;margin:0 0 1.6em;line-height:1.6}
h2{font-family:'Rubik';font-weight:700;font-size:13pt;color:#14477E;
  margin:1.4em 0 .5em;padding-bottom:.25em;border-bottom:1px solid #D3DDE7;break-after:avoid}
.row{display:grid;grid-template-columns:74px 1fr;gap:0 14px;margin-bottom:.75em;
  break-inside:avoid;align-items:baseline}
.at{font-family:'Rubik';font-weight:700;font-size:11pt;color:#14477E;
  font-variant-numeric:tabular-nums;unicode-bidi:isolate}
.len{display:block;font-family:'Assistant';font-weight:400;font-size:9pt;color:#7C8DA1}
.say{font-size:13pt;line-height:1.6}
.tight{color:#A55E0C;font-weight:700;font-size:9.5pt}
"""

body = [f"<h1>קריינות — {esc(scenes[0]['title'])}</h1>",
        f"<p class='meta'>אורך הסרטון <b dir='ltr'>{tc(t)}</b>. "
        f"{len(scenes)} שקפים, {len(rows)} כניסות קריינות.<br>"
        "העמודה הימנית היא הזמן שבו הכניסה מתחילה, ומתחתיו כמה שניות יש לה. "
        "כניסה המסומנת בכתום צפופה — קראו אותה מעט מהר יותר, או בקשו להאריך את השקף.</p>"]
last = None
for r in rows:
    if r['n'] != last:
        body.append(f"<h2>{r['n']}. {esc(r['title'])}</h2>")
        last = r['n']
    warn = "<span class='tight'> צפוף</span>" if r['tight'] else ''
    body.append(
        f"<div class='row'><div class='at' dir='ltr'>{tc(r['at'])}"
        f"<span class='len'>{r['dur']:g} שנ׳{warn}</span></div>"
        f"<div class='say'>{esc(r['text'])}</div></div>")

name = 'קריינות - הסבר כללי מצפן זכויות איבה' if STEM == 'scenes' \
    else 'קריינות - הגשת חשבונית או קבלה'
hp = os.path.join(OUT, f'{name}.html')
pdf = os.path.join(OUT, f'{name}.pdf')
os.makedirs(OUT, exist_ok=True)
open(hp, 'w', encoding='utf-8').write(
    "<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'>"
    f"<style>{CSS}</style></head><body>{''.join(body)}</body></html>")
if chrome:
    subprocess.run([chrome, '--headless', '--no-sandbox', '--disable-gpu',
                    '--no-pdf-header-footer', f'--print-to-pdf={pdf}',
                    '--virtual-time-budget=15000', 'file://' + hp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('wrote', os.path.relpath(pdf, ROOT))
print('wrote', f'video/{STEM}-narration.md', f'({len(rows)} lines, '
      f'{sum(r["tight"] for r in rows)} tight)')
