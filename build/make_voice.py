#!/usr/bin/env python3
"""Speak the narration with ElevenLabs and lay it under the video.

The silent cut is never touched: this writes a second file with " - עם קריינות"
appended. Runs in four steps, any of which can be repeated on its own:

  synth   one clip per narration line, saved under build/out/voice/
  fit     stretch each frame in scenes.json to hold the clip that plays over it,
          so picture and voice stay in step (then rebuild the video)
  mux     pad every clip out to its frame, join them, lay the track under the cut

  python3 build/make_voice.py --voice <voice-id>              # synth + report
  python3 build/make_voice.py --voice <id> --fit --rebuild    # ...and re-cut
  python3 build/make_voice.py --mux                           # lay the track down

Clips made elsewhere work too: drop one mp3 per line in build/out/voice as
01.mp3 … NN.mp3 and run --fit --rebuild --mux; no key is needed for that.

The key comes from ELEVENLABS_API_KEY (or --key). Pick a voice with
--list-voices; the model defaults to one that speaks Hebrew, override with
--model if your account has a newer one.
"""
import json, os, subprocess, sys, shutil, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import narration
from narration import ROOT, tc

API = 'https://api.elevenlabs.io/v1'
SCENES = sys.argv[sys.argv.index('--scenes') + 1] if '--scenes' in sys.argv else 'scenes.json'
STEM = os.path.splitext(SCENES)[0]
OUT = os.path.join(ROOT, 'build', 'out') if STEM == 'scenes' \
    else os.path.join(ROOT, 'build', 'out', STEM)
VOICE_DIR = os.path.join(OUT, 'voice')
KEY = (sys.argv[sys.argv.index('--key') + 1] if '--key' in sys.argv
       else os.environ.get('ELEVENLABS_API_KEY', ''))
VOICE = sys.argv[sys.argv.index('--voice') + 1] if '--voice' in sys.argv else ''
MODEL = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv \
    else 'eleven_multilingual_v2'
FFMPEG = (shutil.which('ffmpeg')
          or subprocess.run([sys.executable, '-c',
                             'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'],
                            capture_output=True, text=True).stdout.strip())


def call(path, data=None, headers=None):
    req = urllib.request.Request(API + path, data=data,
                                 headers={'xi-api-key': KEY, **(headers or {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def audio_seconds(path):
    out = subprocess.run([FFMPEG, '-i', path, '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    for line in reversed(out.splitlines()):
        if 'time=' in line:
            h, m, s = line.split('time=')[1].split()[0].split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError('could not read the length of ' + path)


def synth(rows):
    os.makedirs(VOICE_DIR, exist_ok=True)
    for i, r in enumerate(rows):
        dest = os.path.join(VOICE_DIR, f'{i+1:02d}.mp3')
        body = json.dumps({'text': r['text'], 'model_id': MODEL,
                           'voice_settings': {'stability': 0.5,
                                              'similarity_boost': 0.75,
                                              'speed': 1.0}}).encode()
        open(dest, 'wb').write(
            call(f'/text-to-speech/{VOICE}', body,
                 {'Content-Type': 'application/json', 'Accept': 'audio/mpeg'}))
        print(f'  {i+1:02d}  {audio_seconds(dest):5.1f}s / {r["dur"]:4}s  {r["text"][:52]}')


def measured(rows):
    return [audio_seconds(os.path.join(VOICE_DIR, f'{i+1:02d}.mp3'))
            for i in range(len(rows))]


def fit(rows, secs, pad=0.5):
    """Give every frame room for the line spoken over it, plus a beat after."""
    scenes = json.load(open(os.path.join(ROOT, 'build', SCENES), encoding='utf-8'))
    need, k = {}, 0
    for i, s in enumerate(scenes):
        for j in range(len(narration.lines_for(s))):
            need[(i, j)] = max(rows[k]['dur'], round(secs[k] + pad, 1))
            k += 1
    for i, s in enumerate(scenes):
        frames = [need[(i, j)] for j in range(len(narration.lines_for(s)))]
        if s['type'] == 'walk':
            for st, d in zip(s['steps'], frames):
                st['dur'] = d
            s['dur'] = sum(frames)
        elif s['type'] == 'fork':
            for fr, d in zip(s['frames'], frames):
                scale = d / fr['dur']
                for w in fr['cursor']:
                    w['t'] = round(w['t'] * scale, 2)
                fr['dur'] = d
            s['dur'] = sum(frames)
        elif s['type'] == 'statuslist':
            if s.get('intro'):
                s['intro']['dur'] = frames[0]
            if s.get('outro'):
                s['outro']['dur'] = frames[-1]
            s['dur'] = sum(frames)
        else:
            s['dur'] = frames[0]
    json.dump(scenes, open(os.path.join(ROOT, 'build', SCENES), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(f'fitted: {sum(s["dur"] for s in scenes):.0f}s')


def mux(rows):
    """Pad each clip out to its frame, join them, and lay the result under the cut."""
    silent = [f for f in os.listdir(OUT)
              if f.endswith('.mp4') and 'קריינות' not in f][0]
    parts = []
    for i, r in enumerate(rows):
        src = os.path.join(VOICE_DIR, f'{i+1:02d}.mp3')
        dst = os.path.join(VOICE_DIR, f'p{i+1:02d}.wav')
        subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', src,
                        '-af', f'apad=whole_dur={r["dur"]}', '-t', str(r['dur']),
                        '-ar', '48000', '-ac', '2', dst], check=True)
        parts.append(dst)
    lst = os.path.join(VOICE_DIR, 'parts.txt')
    open(lst, 'w').write('\n'.join(f"file '{p}'" for p in parts) + '\n')
    track = os.path.join(VOICE_DIR, 'track.wav')
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', lst, '-c', 'copy', track], check=True)
    out = os.path.join(OUT, silent[:-4] + ' - עם קריינות.mp4')
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', os.path.join(OUT, silent),
                    '-i', track, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', out], check=True)
    print('wrote', os.path.relpath(out, ROOT))


rows, total, _ = narration.rows(SCENES)

if '--list-voices' in sys.argv:
    for v in json.loads(call('/voices'))['voices']:
        print(v['voice_id'], '|', v['name'], '|', ', '.join(v.get('labels', {}).values()))
    sys.exit()

# --- everything after synthesis works on clips that are already there, so a
# --- track made elsewhere can be fitted and laid down without a key
if '--mux' in sys.argv or ('--fit' in sys.argv and not KEY):
    if not os.path.isdir(VOICE_DIR):
        sys.exit(f'no clips in {os.path.relpath(VOICE_DIR, ROOT)} — '
                 'put one mp3 per narration line there, named 01.mp3 … '
                 f'{len(rows):02d}.mp3')
    missing = [i + 1 for i in range(len(rows))
               if not os.path.exists(os.path.join(VOICE_DIR, f'{i+1:02d}.mp3'))]
    if missing:
        sys.exit(f'missing clips: {missing}')
    if '--fit' in sys.argv:
        fit(rows, measured(rows))
        if '--rebuild' in sys.argv:
            subprocess.run(['bash', os.path.join(ROOT, 'build', 'build-video.sh'),
                            '--scenes', SCENES], check=True)
            rows = narration.rows(SCENES)[0]
    mux(rows)
    sys.exit()

if not KEY:
    sys.exit('no key: set ELEVENLABS_API_KEY, or pass --key')
if not VOICE:
    sys.exit('no voice: pass --voice <id>, or --list-voices to see what you have')

print(f'{len(rows)} lines, {tc(total)} of video')
synth(rows)
secs = measured(rows)
over = [(i + 1, s, rows[i]['dur']) for i, s in enumerate(secs) if s > rows[i]['dur'] - 0.2]
print(f'\n{len(over)} of {len(rows)} lines do not fit their frame'
      + (' — run again with --fit to make room' if over else ''))
if '--fit' in sys.argv:
    fit(rows, secs)
    if '--rebuild' in sys.argv:
        subprocess.run(['bash', os.path.join(ROOT, 'build', 'build-video.sh'),
                        '--scenes', SCENES], check=True)
        mux(narration.rows(SCENES)[0])
