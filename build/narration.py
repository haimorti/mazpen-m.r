"""The narration lines of a guide video: one per frame, with when it starts.

Scenes that hold several frames — the statuses, the walk down a page, the two
buttons — are split per frame, so a line lands with the beat it describes.
Shared by make_narration.py (the script a person reads) and make_voice.py
(the one a voice engine reads).
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WPS = 2.6                       # Hebrew words a second, read calmly


def lines_for(s):
    """(text, seconds) per frame of one scene; seconds None = the whole scene."""
    t = s['type']
    if t == 'statuslist':
        out = []
        if s.get('intro'):
            out.append((s['intro']['cap'], s['intro']['dur']))
        share = (s['dur'] - sum(s[k]['dur'] for k in ('intro', 'outro') if s.get(k))) \
            / len(s['items'])
        out += [(it['note'], it.get('dur', share)) for it in s['items']]
        if s.get('outro'):
            out.append((s['outro']['cap'], s['outro']['dur']))
        return out
    if t == 'walk':
        return [(st['cap'], st['dur']) for st in s['steps']]
    if t == 'fork':
        c0, c1 = s['cols']
        d = [f['dur'] for f in s['frames']]
        strip = lambda x: x.replace('<b>', '').replace('</b>', '')
        return [(s['hint'] + ' ' + strip(c0['said']) + '.', d[0]),
                (c0['dest'] + '.', d[1]),
                (strip(c1['said']) + '.', d[2]),
                (c1['dest'] + '.', d[3])]
    return [(s.get('vo', ''), None)]


def rows(scenes_file='scenes.json'):
    """Every narration entry in order, with its start time and its slot."""
    scenes = json.load(open(os.path.join(ROOT, 'build', scenes_file), encoding='utf-8'))
    out, t = [], 0.0
    for i, s in enumerate(scenes):
        frames = lines_for(s)
        at = t
        for k, (text, dur) in enumerate(frames):
            d = s['dur'] if dur is None else dur
            est = len(text.split()) / WPS
            out.append({'n': i + 1, 'sub': k + 1 if len(frames) > 1 else 0,
                        'title': s.get('title', ''), 'at': at, 'dur': d, 'text': text,
                        'words': len(text.split()), 'est': est, 'tight': est > d - 0.3})
            at += d
        t += s['dur']
    return out, t, scenes


def tc(t):
    m, s = divmod(int(round(t)), 60)
    return f'{m}:{s:02d}'
