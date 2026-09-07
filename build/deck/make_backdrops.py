#!/usr/bin/env python3
"""Backdrops for the slides: a few soft lights over a ground colour.

Nothing here is a stock photograph. Each backdrop is a handful of wide radial
sources blended over a base, blurred and dithered so no banding shows on a
projector.
"""
import os

import numpy as np
from PIL import Image, ImageFilter

W, H = 2666, 1500
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
os.makedirs(DEST, exist_ok=True)


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def backdrop(base, lights, vignette=0.0):
    """base: hex ground. lights: (hex, cx, cy, radius, strength) in slide fractions."""
    y, x = np.mgrid[0:H, 0:W]
    x = x / W
    y = y / H
    out = np.repeat(np.repeat(rgb(base)[None, None, :], H, 0), W, 1)
    for colour, cx, cy, r, k in lights:
        d = np.sqrt(((x - cx) * (W / H)) ** 2 + (y - cy) ** 2) / r
        w = np.clip(1 - d, 0, 1) ** 2.2 * k
        out = out * (1 - w[..., None]) + rgb(colour)[None, None, :] * w[..., None]
    if vignette:
        d = np.sqrt(((x - .5) * (W / H)) ** 2 + (y - .5) ** 2) / 0.75
        out *= (1 - np.clip(d, 0, 1) ** 2 * vignette)[..., None]
    out += np.random.default_rng(7).normal(0, 1.1, out.shape)   # break up the banding
    im = Image.fromarray(np.clip(out, 0, 255).astype('uint8'))
    return im.filter(ImageFilter.GaussianBlur(1.2))


RECIPES = {
    # light and warm: the one that reads most welcoming
    'dawn': ('FDF8F3', [('F8E6D4', 0.82, 0.02, 1.05, 0.85),
                        ('EDF2F9', 0.06, 1.02, 0.95, 0.75),
                        ('FFFFFF', 0.45, 0.45, 0.55, 0.45)], 0.0),
    # airy blue, closest to the institute's own colour
    'sky': ('F5FAFF', [('D9E9F9', 0.86, 0.04, 1.0, 0.95),
                       ('FFFFFF', 0.30, 0.75, 0.85, 0.9),
                       ('E7F0F8', 0.02, 1.0, 0.8, 0.6)], 0.0),
    # ivory, quiet, prints well
    'sand': ('FBF6EE', [('F1E7D8', 0.18, 0.05, 1.0, 0.9),
                        ('FFFDF9', 0.70, 0.60, 0.8, 0.7),
                        ('E9EEF2', 0.95, 1.02, 0.7, 0.55)], 0.0),
    # green, calm rather than clinical
    'sage': ('F4F8F4', [('E0EDE4', 0.84, 0.03, 1.0, 0.9),
                        ('FFFFFF', 0.35, 0.65, 0.8, 0.8),
                        ('EAF1EC', 0.05, 1.0, 0.8, 0.5)], 0.0),
    # the dark twin of sage, for the section breaks
    'forest': ('16302A', [('27584A', 0.84, 0.0, 1.05, 0.8),
                          ('14384A', 0.05, 1.0, 0.95, 0.55),
                          ('1D4038', 0.5, 0.45, 0.7, 0.45)], 0.16),
    # dark, but warmer than the first try
    'dusk': ('132743', [('3A3560', 0.84, 0.0, 1.05, 0.85),
                        ('134A5E', 0.05, 1.0, 0.95, 0.6),
                        ('1B3A5E', 0.5, 0.45, 0.7, 0.5)], 0.18),
}

if __name__ == '__main__':
    for name, (base, lights, vig) in RECIPES.items():
        backdrop(base, lights, vig).save(os.path.join(DEST, f'bg_{name}.png'))
        print('wrote', name)
