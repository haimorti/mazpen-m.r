#!/usr/bin/env python3
"""Produce guide/dist/index.html: the guide with every image inlined as a data URI,
so the single file can be emailed, uploaded or published as-is."""
import base64, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, 'guide', 'index.html')
dst_dir = os.path.join(ROOT, 'guide', 'dist'); os.makedirs(dst_dir, exist_ok=True)
html = open(src, encoding='utf-8').read()
def repl(m):
    p = os.path.join(ROOT, 'guide', m.group(1))
    b = base64.b64encode(open(p, 'rb').read()).decode()
    return f'src="data:image/png;base64,{b}"'
html = re.sub(r'src="(img/[^"]+\.png)"', repl, html)
open(os.path.join(dst_dir, 'index.html'), 'w', encoding='utf-8').write(html)
print('wrote guide/dist/index.html', len(html) // 1024, 'KB')
