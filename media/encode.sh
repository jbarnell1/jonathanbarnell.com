#!/usr/bin/env bash
# Re-encodes source films into small muted web clips: VP9 WebM, H.264 MP4 and a WebP poster each.
# Run from Git Bash: bash media/encode.sh   (needs ffmpeg on PATH)
set -euo pipefail
cd "$(dirname "$0")"

enc() { # name, source, scale filter, poster time, vp9 crf, x264 crf, [extra input args]
  local name="$1" src="$2" scale="$3" at="$4" vcrf="$5" hcrf="$6"; shift 6
  ffmpeg -hide_banner -loglevel error -y "$@" -i "$src" -an -vf "$scale,fps=30" \
    -c:v libvpx-vp9 -crf "$vcrf" -b:v 0 -row-mt 1 -cpu-used 2 -pix_fmt yuv420p "$name.webm"
  ffmpeg -hide_banner -loglevel error -y "$@" -i "$src" -an -vf "$scale,fps=30" \
    -c:v libx264 -crf "$hcrf" -preset slow -profile:v high -pix_fmt yuv420p -movflags +faststart "$name.mp4"
  ffmpeg -hide_banner -loglevel error -y -ss "$at" "$@" -i "$src" -frames:v 1 -vf "$scale" -c:v libwebp -quality 80 "$name.webp"
  ls -la "$name".* | awk '{print $5, $9}'
}

BUOY="/c/BuoyAI resources/clips/_motion"
enc buoy-film  "$BUOY/highlights-short-01.mp4" "scale=1280:-2" 1.0 38 28
enc buoy-phone "$BUOY/budget-01.mp4"           "scale=540:-2"  6.0 38 28
enc scripture  "/c/yt_scripture_generator/data/raw_files/PSA.117/PSA.117_short_0.mp4" "scale=540:-2" 4.0 38 28
