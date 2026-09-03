#!/usr/bin/env bash
# Builds the draft guide video from the scenes: one clip per slide, concatenated.
# Slides marked with "focus" get an animated push-in (the camera moves in on the
# band being narrated); every other slide is a still.
# Requires: python3, a chromium binary, ffmpeg with libx264.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FFMPEG="${FFMPEG:-$(command -v ffmpeg || python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || echo /opt/pw-browsers/ffmpeg-1011/ffmpeg-linux)}"
FPS=25

python3 "$ROOT/build/make_slides.py" "$@"
python3 "$ROOT/build/make_script.py"

cd "$ROOT/build/out"
rm -rf clips && mkdir -p clips

python3 - "$FFMPEG" "$FPS" <<'PY'
import json, os, subprocess, sys
ffmpeg, fps = sys.argv[1], int(sys.argv[2])
tl = json.load(open('timeline.json', encoding='utf-8'))
lines = []
for i, s in enumerate(tl):
    src = os.path.join('slides', s['slide'])
    out = os.path.join('clips', f"{i+1:02d}.mp4")
    frames = int(s['dur'] * fps)
    m = s.get('motion')
    if m:
        # ease-out push-in over the first 40% of the scene, then hold
        ramp = max(1, int(frames * 0.4))
        z = m['zoom']
        zexpr = (f"if(lte(on,{ramp}),1+({z}-1)*(1-pow(1-on/{ramp},3)),{z})")
        vf = (f"zoompan=z='{zexpr}'"
              f":x='{m['cx']}-(iw/zoom/2)':y='{m['cy']}-(ih/zoom/2)'"
              f":d={frames}:s=1920x1080:fps={fps},format=yuv420p")
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-loop', '1', '-i', src,
               '-vf', vf, '-frames:v', str(frames), '-c:v', 'libx264', '-crf', '19',
               '-preset', 'slow', '-pix_fmt', 'yuv420p', out]
    else:
        vf = f"scale=1920:1080:flags=lanczos,format=yuv420p"
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-loop', '1', '-i', src,
               '-vf', vf, '-r', str(fps), '-t', str(s['dur']), '-c:v', 'libx264', '-crf', '19',
               '-preset', 'slow', '-pix_fmt', 'yuv420p', out]
    subprocess.run(cmd, check=True)
    lines.append(f"file '{out}'")
    print('clip', s['slide'], 'motion' if m else 'still')
open('clips.txt', 'w').write('\n'.join(lines) + '\n')
PY

"$FFMPEG" -y -loglevel error -f concat -safe 0 -i clips.txt -c copy mazpen-guide-draft.mp4
echo "wrote build/out/mazpen-guide-draft.mp4"
