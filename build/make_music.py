#!/usr/bin/env python3
"""A quiet bed of music for the videos, written here rather than fetched.

There is no music library on this machine and no way to reach one, so the bed is
synthesised: slow chords over a soft bass, and depending on the style, single
notes struck above them. Nothing is sampled and nothing is licensed -- what comes
out belongs to whoever runs this.

  python3 build/make_music.py --demo                 four 40s samples to choose from
  python3 build/make_music.py --style pad --under "out/film.mp4"

Output: build/out/music/<style>.m4a, and "<film> - עם מוזיקה.mp4"
"""
import math
import os
import struct
import subprocess
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'build', 'out', 'music')
SR = 44100
FFMPEG = (__import__('shutil').which('ffmpeg')
          or subprocess.run([sys.executable, '-c',
                             'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                            capture_output=True, text=True).stdout.strip())

STEPS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def hz(name):
    """'A4' -> 440.0, 'Bb2' -> 116.54"""
    step = STEPS[name[0]]
    i = 1
    while name[i] in 'b#':
        step += 1 if name[i] == '#' else -1
        i += 1
    return 440.0 * 2 ** ((step - 9 + (int(name[i:]) - 4) * 12) / 12)


# four bars of eight seconds: warm, settled, and going nowhere in particular
CHORDS = [
    (['F3', 'A3', 'C4', 'E4', 'G4'], 'F2'),
    (['E3', 'G3', 'C4', 'D4'], 'C2'),
    (['D3', 'F3', 'A3', 'C4', 'E4'], 'D2'),
    (['Bb2', 'D3', 'F3', 'A3', 'C4'], 'Bb1'),
]
TOPS = [['A4', 'C5'], ['G4', 'D5'], ['F4', 'A4'], ['D5', 'F5']]
BAR = 8.0


def held(freq, n, harmonics):
    """A note that stays: additive, two layers a hair apart so it moves a little."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for detune in (-0.0009, 0.0009):
        for k, amp in enumerate(harmonics, start=1):
            if freq * k > 15000:
                break
            out += amp * np.sin(2 * np.pi * freq * k * (1 + detune) * t
                                + k * freq % 6.283)
    return out / (2 * sum(harmonics))


def struck(freq, n, harmonics, decay, ratios=None):
    """A note that is hit and then dies away, the high partials going first."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, amp in enumerate(harmonics, start=1):
        f = freq * (ratios[k - 1] if ratios else k)
        if f > 15000:
            break
        out += amp * np.sin(2 * np.pi * f * t) * np.exp(-t / (decay / (1 + 0.55 * (k - 1))))
    return out / sum(harmonics)


def swell(n, attack, release):
    """Fade a note in and out of the bar it belongs to."""
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    e[:a] = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    e[n - r:] = np.sin(np.linspace(np.pi / 2, 0, r)) ** 2
    return e


def halo(x, taps=((0.093, .34), (0.157, .24), (0.211, .17), (0.283, .12),
                  (0.367, .08), (0.451, .05))):
    """A soft room around the sound: a handful of quiet, late copies."""
    wet = np.zeros_like(x)
    for delay, gain in taps:
        d = int(delay * SR)
        wet[d:] += gain * x[:len(x) - d]
    return x + 0.55 * wet


STYLES = {
    'pad':     'אקורדים בלבד — הכי שקט וניטרלי',
    'piano':   'פסנתר רך מעל האקורדים',
    'bells':   'פעמונים — נגיעות בודדות, בהיר יותר',
    'strings': 'מיתרים — נשימות ארוכות, בלי מלודיה',
}


def bed(style, seconds):
    n = int(seconds * SR)
    pad = np.zeros(n + SR * 4)
    top = np.zeros(n + SR * 4)

    pad_h = {'pad': [1, .40, .16, .07, .03],
             'piano': [1, .34, .12, .05],
             'bells': [1, .30, .11, .04],
             'strings': [1, .55, .30, .18, .10, .06, .03]}[style]
    pad_gain = {'pad': 1.0, 'piano': .55, 'bells': .55, 'strings': 1.0}[style]

    bar = int(BAR * SR)
    over = int(2.6 * SR)                       # bars overlap, so nothing ever restarts
    for i in range(int(seconds / BAR) + 1):
        notes, root = CHORDS[i % len(CHORDS)]
        start = i * bar
        ln = bar + over
        if start + ln > len(pad):
            ln = len(pad) - start
        if ln <= 0:
            break
        env = swell(ln, 2.6, 2.6)
        if style == 'strings':                 # a slow breath across the bar
            env = env * (0.78 + 0.22 * np.sin(np.linspace(0, np.pi, ln)))
        voice = sum(held(hz(p), ln, pad_h) for p in notes) / len(notes)
        voice += 0.5 * held(hz(root), ln, [1, .22, .06])
        pad[start:start + ln] += voice * env * pad_gain

        if style in ('piano', 'bells'):
            for j, name in enumerate(TOPS[i % len(TOPS)]):
                at = start + int((1.0 + j * 4.0) * SR)
                if at >= len(top):
                    break
                ln2 = min(int(5.0 * SR), len(top) - at)
                if style == 'piano':
                    v = struck(hz(name), ln2, [1, .48, .22, .10, .05], 2.6)
                else:
                    v = struck(hz(name), ln2, [1, .38, .22, .12], 4.2,
                               ratios=[1, 2.76, 5.40, 8.93])
                top[at:at + ln2] += v * (0.42 if style == 'piano' else 0.30)

    mix = pad + top
    mix = halo(mix)[:n]
    mix *= swell(n, 3.0, 4.0)                  # in at the start, out at the end

    right = np.zeros(n)                        # a little width: one ear a touch later
    d = int(0.011 * SR)
    right[d:] = mix[:n - d]
    stereo = np.stack([mix, 0.75 * mix + 0.25 * right], axis=1)
    peak = np.max(np.abs(stereo)) or 1.0
    return stereo / peak * 10 ** (-18 / 20)    # quiet: -18 dBFS at the loudest


def write_wav(path, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())


def encode(wav, dest):
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', wav,
                    '-c:a', 'aac', '-b:a', '192k', dest], check=True)
    os.remove(wav)


def video_seconds(path):
    err = subprocess.run([FFMPEG, '-i', path, '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    for line in reversed(err.splitlines()):
        if 'time=' in line:
            h, m, s = line.split('time=')[1].split()[0].split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError('could not read the length of ' + path)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    argv = sys.argv

    if '--demo' in argv:
        for style, what in STYLES.items():
            wav = os.path.join(OUT, style + '.wav')
            write_wav(wav, bed(style, 40))
            encode(wav, os.path.join(OUT, style + '.m4a'))
            print(f'{style:8s} {what}')
        sys.exit()

    style = argv[argv.index('--style') + 1] if '--style' in argv else 'pad'
    if '--under' not in argv:
        sys.exit('pass --demo, or --style <name> --under <film.mp4>')
    film = argv[argv.index('--under') + 1]
    gain = float(argv[argv.index('--gain') + 1]) if '--gain' in argv else 1.0

    secs = video_seconds(film)
    wav = os.path.join(OUT, f'{style}-{int(secs)}.wav')
    write_wav(wav, bed(style, secs) * gain)
    stem, ext = os.path.splitext(film)
    dest = f'{stem} - עם מוזיקה{ext}'
    has_audio = 'Audio:' in subprocess.run([FFMPEG, '-i', film], capture_output=True,
                                           text=True).stderr
    if has_audio:                              # keep the voice on top, music underneath
        cmd = [FFMPEG, '-y', '-loglevel', 'error', '-i', film, '-i', wav,
               '-filter_complex', '[1:a]volume=0.5[m];[0:a][m]amix=inputs=2:duration=first[a]',
               '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', dest]
    else:
        cmd = [FFMPEG, '-y', '-loglevel', 'error', '-i', film, '-i', wav,
               '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
               '-b:a', '192k', '-shortest', dest]
    subprocess.run(cmd, check=True)
    os.remove(wav)
    print('wrote', os.path.relpath(dest, ROOT))
