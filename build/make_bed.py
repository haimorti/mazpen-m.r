#!/usr/bin/env python3
"""Stretch a short piece of music into a bed of any length, without an audible seam.

A minute of music has to sit under four minutes of film. Rather than fade out and
start again -- which everyone hears -- the piece is cut at the point where its end
best matches its own beginning, and joined to itself there with an equal-power
crossfade. Cut at the right place, the join lands on a bar line and passes unnoticed.

  python3 build/make_bed.py track.mp3 --seconds 245 --out bed.m4a
  python3 build/make_bed.py track.mp3 --under film.mp4  # a bed its exact length, laid under
  python3 build/make_bed.py track.mp3 --seam            # six seconds around one join
"""
import os
import subprocess
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
FFMPEG = (__import__('shutil').which('ffmpeg')
          or subprocess.run([sys.executable, '-c',
                             'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                            capture_output=True, text=True).stdout.strip())


def decode(path):
    raw = subprocess.run([FFMPEG, '-v', 'quiet', '-i', path, '-vn',
                          '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype='<f4').reshape(-1, 2).astype(np.float64)


def tempo_grid(m):
    """Half a bar, from the piece's own pulse -- so a cut lands where a bar does."""
    hop, win = 512, 2048
    frames = 1 + (len(m) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(frames)[:, None]
    spec = np.log1p(np.abs(np.fft.rfft(m[idx] * np.hanning(win)[None, :], axis=1)))
    flux = np.maximum(0, np.diff(spec, axis=0)).sum(axis=1)
    flux -= flux.mean()
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    fps = SR / hop
    lo, hi = int(fps * 0.3), int(fps * 1.2)          # 50 to 200 beats a minute
    beat = (lo + int(np.argmax(ac[lo:hi]))) / fps
    return beat * 2, beat                            # half a bar of four, and the beat


def profile(seg):
    """What the music sounds like over a window: log-spaced band levels.

    Magnitudes only, so two passages that share a harmony and a texture score
    alike even when their waveforms are nowhere near in phase.
    """
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freq = np.fft.rfftfreq(len(seg), 1 / SR)
    edges = np.geomspace(60, 10000, 33)
    band = np.array([spec[(freq >= a) & (freq < b)].mean() if ((freq >= a) & (freq < b)).any()
                     else 0.0 for a, b in zip(edges[:-1], edges[1:])])
    band = np.log1p(band)
    return band / (np.linalg.norm(band) or 1.0)


def loop_length(x, fade, lo=15.0, keep=0.9):
    """Where to cut, so the end of the loop meets its own beginning.

    Candidates sit on the piece's own bar grid. Each is scored on how closely the
    window before the cut matches the window at the very start, in both colour and
    level. Among everything close to the best, the longest wins: a good four-bar
    loop heard thirteen times is worse than a good twelve-bar loop heard four.
    """
    m = x.mean(axis=1)
    grid, beat = tempo_grid(m)
    head, head_rms = profile(m[:fade]), np.sqrt(np.mean(m[:fade] ** 2))
    found = []
    n = 1
    while grid * n < len(m) / SR - 0.2:
        L = grid * n
        n += 1
        if L < lo:
            continue
        s = int(L * SR)
        win = m[s - fade:s]
        rms = np.sqrt(np.mean(win ** 2))
        level = min(rms, head_rms) / (max(rms, head_rms) or 1.0)
        found.append((float(head @ profile(win)) * level, L))
    if not found:
        return len(x), 0.0, beat
    top = max(f[0] for f in found)
    good = [f for f in found if f[0] >= top * keep]
    score, L = max(good, key=lambda f: f[1])
    return int(L * SR), score, beat


def build(x, seconds, fade):
    """Repeat the loop into `seconds`, crossfading each join with equal power."""
    L, score, beat = loop_length(x, fade)
    body = x[:L]
    t = np.linspace(0, np.pi / 2, fade)[:, None]
    fade_in, fade_out = np.sin(t), np.cos(t)          # equal power: in^2 + out^2 = 1
    want = int(seconds * SR)

    out = body.copy()
    while len(out) < want + fade:
        tail = out[-fade:] * fade_out + body[:fade] * fade_in
        out = np.concatenate([out[:-fade], tail, body[fade:]])
    return out[:want], L / SR, score, beat


def shape(y, fade_in=3.0, fade_out=4.0):
    a, b = int(fade_in * SR), int(fade_out * SR)
    y = y.copy()
    y[:a] *= np.sin(np.linspace(0, np.pi / 2, a))[:, None] ** 2
    y[-b:] *= np.sin(np.linspace(np.pi / 2, 0, b))[:, None] ** 2
    return y


def write(path, y, peak_db=-18.0):
    y = y / (np.max(np.abs(y)) or 1.0) * 10 ** (peak_db / 20)
    data = (np.clip(y, -1, 1) * 32767).astype('<i2')
    wav = path + '.wav'
    with wave.open(wav, 'wb') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())
    if path.endswith('.wav'):
        os.replace(wav, path)
        return
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', wav,
                    '-c:a', 'aac', '-b:a', '192k', path], check=True)
    os.remove(wav)


def film_seconds(path):
    err = subprocess.run([FFMPEG, '-i', path, '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    for line in reversed(err.splitlines()):
        if 'time=' in line:
            h, m, sec = line.split('time=')[1].split()[0].split(':')
            return int(h) * 3600 + int(m) * 60 + float(sec)
    raise RuntimeError('could not read the length of ' + path)


if __name__ == '__main__':
    src = sys.argv[1]
    fade = int(float(sys.argv[sys.argv.index('--fade') + 1] if '--fade' in sys.argv else 2.0) * SR)
    x = decode(src)
    print(f'{src}: {len(x)/SR:.2f}s')

    if '--seam' in sys.argv:
        L, score, beat = loop_length(x, fade)
        print(f'{60/beat:.0f} BPM, loop at {L/SR:.2f}s, match {score:.3f}')
        y, _, _, _ = build(x, L / SR + 6.0, fade)
        a = int((L / SR - 3.0) * SR)
        write(os.path.join(ROOT, 'build', 'out', 'music', 'seam.m4a'), y[a:a + 6 * SR], -6.0)
        print('wrote build/out/music/seam.m4a — three seconds each side of the join')
        sys.exit()

    if '--under' in sys.argv:
        film = sys.argv[sys.argv.index('--under') + 1]
        seconds = film_seconds(film)
        stem, ext = os.path.splitext(film)
        dest = os.path.join(ROOT, 'build', 'out', 'music', 'bed.wav')
    else:
        seconds = float(sys.argv[sys.argv.index('--seconds') + 1])
        dest = sys.argv[sys.argv.index('--out') + 1]
    y, L, score, beat = build(x, seconds, fade)
    print(f'{60/beat:.0f} BPM, loop at {L:.2f}s, match {score:.3f}, '
          f'{seconds:.1f}s of bed ({seconds / L:.1f} passes)')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    write(dest, shape(y))
    if '--under' not in sys.argv:
        print('wrote', os.path.relpath(dest, ROOT))
        sys.exit()

    out = f'{stem} - עם מוזיקה{ext}'
    voiced = 'Audio:' in subprocess.run([FFMPEG, '-i', film], capture_output=True,
                                        text=True).stderr
    if voiced:                       # the voice stays on top, the music goes under it
        cmd = [FFMPEG, '-y', '-loglevel', 'error', '-i', film, '-i', dest,
               '-filter_complex', '[1:a]volume=0.55[m];[0:a][m]amix=inputs=2:duration=first[a]',
               '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', out]
    else:
        cmd = [FFMPEG, '-y', '-loglevel', 'error', '-i', film, '-i', dest,
               '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
               '-b:a', '192k', '-shortest', out]
    subprocess.run(cmd, check=True)
    os.remove(dest)
    print('wrote', os.path.relpath(out, ROOT))
