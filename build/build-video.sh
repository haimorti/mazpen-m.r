#!/usr/bin/env bash
# Builds the draft guide video (silent, captions baked in) from the scenes.
# Requires: python3, a chromium binary, ffmpeg (with libvpx for .webm; libx264 if present for .mp4).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Prefer a full ffmpeg (system, or the one bundled with the imageio-ffmpeg pip package).
FFMPEG="${FFMPEG:-$(command -v ffmpeg || python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || echo /opt/pw-browsers/ffmpeg-1011/ffmpeg-linux)}"
python3 "$ROOT/build/make_slides.py" "$@"
python3 "$ROOT/build/make_script.py"
cd "$ROOT/build/out"
if "$FFMPEG" -hide_banner -encoders 2>/dev/null | grep libx264 >/dev/null; then
  "$FFMPEG" -y -loglevel error -f concat -safe 0 -i concat.txt -vf "fps=25,scale=1920:1080:flags=lanczos,format=yuv420p" -c:v libx264 -crf 19 -preset slow mazpen-guide-draft.mp4
  echo "wrote build/out/mazpen-guide-draft.mp4"
else
  "$FFMPEG" -y -loglevel error -f concat -safe 0 -i concat.txt -vf "fps=25,scale=1920:1080:flags=lanczos,format=yuv420p" -c:v libvpx -b:v 2M -crf 10 mazpen-guide-draft.webm
  echo "wrote build/out/mazpen-guide-draft.webm (no libx264 in this ffmpeg; convert to mp4 elsewhere if needed)"
fi
