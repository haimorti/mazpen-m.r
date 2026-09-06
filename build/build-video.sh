#!/usr/bin/env bash
# Builds a guide video from a scenes file: one clip per slide, concatenated.
# Slides carrying "focus" get an animated push-in; slides carrying "cursor" get
# a pointer that travels between waypoints and flashes a ring where it clicks.
# Requires: python3, a chromium binary, ffmpeg with libx264.
#
#   build/build-video.sh                                  # the general guide
#   build/build-video.sh --scenes scenes-invoice.json --name "הגשת חשבונית"
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FFMPEG="${FFMPEG:-$(command -v ffmpeg || python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || echo /opt/pw-browsers/ffmpeg-1011/ffmpeg-linux)}"
FPS=25

SCENES=scenes.json
NAME="הסבר כללי מצפן זכויות איבה"
ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --scenes) SCENES="$2"; shift 2;;
    --name)   NAME="$2";   shift 2;;
    *)        ARGS+=("$1"); shift;;
  esac
done
STEM="${SCENES%.json}"
OUTDIR="$ROOT/build/out"; [ "$STEM" = scenes ] || OUTDIR="$OUTDIR/$STEM"

python3 "$ROOT/build/make_cursor.py"
python3 "$ROOT/build/make_slides.py" --scenes "$SCENES" ${ARGS[@]+"${ARGS[@]}"}
python3 "$ROOT/build/make_script.py" --scenes "$SCENES"

cd "$OUTDIR"
rm -rf clips && mkdir -p clips

python3 - "$FFMPEG" "$FPS" "$ROOT/build/out/sprites" <<'PY'
import json, os, subprocess, sys
ffmpeg, fps, sprites = sys.argv[1], int(sys.argv[2]), sys.argv[3]
tl = json.load(open('timeline.json', encoding='utf-8'))
lines = []
for i, s in enumerate(tl):
    src = os.path.join('slides', s['slide'])
    out = os.path.join('clips', f"{i+1:02d}.mp4")
    frames = int(s['dur'] * fps)
    m = s.get('motion')
    if m and 'cursor' in m:
        w = m['cursor']
        def track(axis):
            expr = str(w[0][axis])
            for a, b in zip(w, w[1:]):
                u = f"(t-{a['t']})/{b['t']-a['t']}"
                seg = f"{a[axis]}+({b[axis]-a[axis]})*(3*pow({u},2)-2*pow({u},3))"
                expr = f"if(lt(t,{a['t']}),{expr},if(lt(t,{b['t']}),{seg},{b[axis]}))"
            return expr
        clicks = [p for p in w if p.get('click')]
        rings = ''.join(
            f"[v{i}][2:v]overlay=x={p['x']}-60:y={p['y']}-60:"
            f"enable='between(t,{p['t']},{p['t']+0.45})'[v{i+1}];"
            for i, p in enumerate(clicks))
        fc = (f"[0:v]scale=1920:1080:flags=lanczos,format=yuv420p[bg];"
              f"[bg][1:v]overlay=x='{track('x')}':y='{track('y')}'[v0];"
              + rings.rstrip(';')).rstrip(';')
        last = f"[v{len(clicks)}]" if clicks else "[v0]"
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-loop', '1', '-i', src,
                        '-i', os.path.join(sprites, 'cursor.png'),
                        '-i', os.path.join(sprites, 'ring.png'),
                        '-filter_complex', fc, '-map', last, '-t', str(s['dur']),
                        '-r', str(fps), '-c:v', 'libx264', '-crf', '19', '-preset', 'slow',
                        '-pix_fmt', 'yuv420p', out], check=True)
        lines.append(f"file '{out}'")
        print('clip', s['slide'], 'cursor')
        continue
    if m:
        ramp = max(1, int(frames * 0.4))
        z = m['zoom']
        zexpr = f"if(lte(on,{ramp}),1+({z}-1)*(1-pow(1-on/{ramp},3)),{z})"
        vf = (f"zoompan=z='{zexpr}':x='{m['cx']}-(iw/zoom/2)':y='{m['cy']}-(ih/zoom/2)'"
              f":d={frames}:s=1920x1080:fps={fps},format=yuv420p")
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-loop', '1', '-i', src, '-vf', vf,
               '-frames:v', str(frames)]
    else:
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-loop', '1', '-i', src,
               '-vf', 'scale=1920:1080:flags=lanczos,format=yuv420p',
               '-r', str(fps), '-t', str(s['dur'])]
    subprocess.run(cmd + ['-c:v', 'libx264', '-crf', '19', '-preset', 'slow',
                          '-pix_fmt', 'yuv420p', out], check=True)
    lines.append(f"file '{out}'")
    print('clip', s['slide'], 'motion' if m else 'still')
open('clips.txt', 'w').write('\n'.join(lines) + '\n')
PY

"$FFMPEG" -y -loglevel error -f concat -safe 0 -i clips.txt -c copy "$NAME.mp4"
echo "wrote ${OUTDIR#$ROOT/}/$NAME.mp4"
