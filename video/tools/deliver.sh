#!/bin/bash
# Render every spot and write a delivery encode alongside the master.
#
# Remotion's own output is deliberately near-lossless so it can be recut or
# regraded; that file is 2-4x larger than anything worth uploading. The
# delivery encode is what goes to Drive and to the ad platforms, which re-encode
# on ingest anyway - CRF 23 survives that intact and is a third of the size.
set -euo pipefail
cd "$(dirname "$0")/.."

FF="npx remotion ffmpeg -hide_banner -loglevel error -y"
mkdir -p out out/delivery

render() { # composition, delivered filename
  echo "→ $1"
  npx remotion render "$1" "out/$1.mp4" \
    --codec=h264 --crf=19 --audio-bitrate=192k --log=error
  $FF -i "out/$1.mp4" \
    -c:v libx264 -preset slow -crf 23 -profile:v high -level 4.0 \
    -pix_fmt yuv420p -movflags +faststart \
    -c:a aac -b:a 160k -ar 48000 -ac 2 \
    "out/delivery/$2"
  echo "  out/delivery/$2  $(du -h "out/delivery/$2" | cut -f1)"
}

render Adapt     ClimbSmarter_01_It-Adapts_20s.mp4
render Ask       ClimbSmarter_02_Ask-It-Anything_20s.mp4
render Fuel      ClimbSmarter_03_Fueling-Plan_18s.mp4
render Grind     ClimbSmarter_04_The-Grind_22s.mp4
render Quietfeet ClimbSmarter_05_Tip-Quiet-Feet_20s.mp4
