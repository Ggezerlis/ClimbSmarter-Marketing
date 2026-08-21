#!/usr/bin/env python3
"""
Cut one shot out of the source footage and normalise it to a 1080x1920 clip.

Two source families need very different handling:

  screen  iOS screen recordings, 1290x2796. Safari's chrome has to come off,
          and it is not a fixed height: when the page is scrolled Safari
          collapses to a slim top bar and hides its bottom toolbar, and when
          it isn't, the tall address pill and the bottom toolbar are both
          there. So the chrome is measured per shot rather than assumed.

  cam     iPhone 4K60 HLG. Needs tone mapping to bt709 or the whole shot
          comes out washed and grey, then a centre-ish 9:16 crop.

Remotion ships a cut-down ffmpeg (crop/format/scale/tonemap/trim/zscale and
the audio handful) - no fps, setpts, unsharp or drawtext - so frame rate is
handled with -r and any speed ramping happens in Remotion via playbackRate.
"""
import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.dirname(HERE)
# The camera originals are far too big to keep in the repo; point this at
# wherever they were pulled down from Drive.
SRC = os.environ.get("FOOTAGE_DIR", "/tmp/climbsmarter_footage")
FF = ["npx", "remotion", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]

W, H = 1080, 1920
SCREEN_W = 1290

SOURCES = {
    "screen1": "screen1_0049.mp4",
    "screen2": "screen2_1849.mp4",
}

# HLG -> bt709. npl=250 keeps the gym highlights from blowing out.
TONEMAP = (
    "zscale=t=linear:npl=250,tonemap=hable:desat=0,"
    "zscale=p=bt709:t=bt709:m=bt709:r=tv,format=yuv420p"
)


def run(cmd):
    p = subprocess.run(cmd, cwd=VIDEO_DIR, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{' '.join(cmd)}\n{p.stderr[-3000:]}")
    return p


def resolve(name):
    return os.path.join(SRC, SOURCES.get(name, name))


def grab(path, at):
    """One full-resolution frame, as an array."""
    tmp = os.path.join(tempfile.gettempdir(), "prep_probe.png")
    run(FF + ["-ss", str(at), "-i", path, "-frames:v", "1", tmp])
    return np.asarray(Image.open(tmp).convert("RGB")).astype(float)


def _is_chrome(row):
    """Safari's chrome is a flat mid-grey; app content never is."""
    return row.std() < 4.0 and 35 < row.mean() < 60


def measure_chrome(path, at, band=460, run=8):
    """
    First and last row of real page content in a screen recording.

    Neither edge can be found by walking in from the frame border: the status
    bar (clock, battery) and the toolbar icons are not flat, so a naive scan
    stops on them. Instead look for the *last* solid band of chrome grey near
    the top and the *first* one near the bottom.
    """
    a = grab(path, at)
    h = a.shape[0]
    chrome = np.array([_is_chrome(row) for row in a])

    top = 0
    for y in range(band, run - 1, -1):
        if chrome[y - run + 1:y + 1].all():
            top = y + 1
            break

    bottom = h
    for y in range(h - band, h - run + 1):
        if chrome[y:y + run].all():
            bottom = y
            break

    return top, bottom


def screen_filter(path, at, bias, span=0.0):
    """
    Crop the chrome, then take a 9:16 window out of what's left.

    `bias` picks the vertical framing when the content is taller than 9:16
    (0 = top of the page, 1 = bottom). When the content is *shorter* than 9:16
    - which happens whenever Safari is showing both toolbars - the window is
    narrowed instead so the full page width still survives.

    Safari can expand or collapse its toolbars *during* a shot, so both ends of
    `span` are measured and the tighter crop wins: cropping too much only loses
    a sliver of page, cropping too little puts the address bar in the ad.
    """
    edges = [measure_chrome(path, t)
             for t in ({at - span / 2, at + span / 2} if span else {at})]
    top = max(e[0] for e in edges)
    bottom = min(e[1] for e in edges)
    ch = bottom - top
    want = round(SCREEN_W * H / W)  # 2293 px of content for a full-width 9:16
    if ch >= want:
        y = top + round((ch - want) * bias)
        crop = f"crop={SCREEN_W}:{want}:0:{y}"
    else:
        cw = (round(ch * W / H) // 2) * 2
        crop = f"crop={cw}:{ch}:{(SCREEN_W - cw) // 2}:{top}"
    return f"{crop},scale={W}:{H}:flags=lanczos,format=yuv420p", (top, bottom)


_dims = {}


def frame_size(path):
    """
    Decoded frame size, not the coded one.

    These are iPhone clips: the stream is stored 3840x2160 with a rotation
    matrix, and ffmpeg applies it on decode, so what the filter graph actually
    sees is 2160x3840 portrait. Reading `stream=width,height` gives the stored
    size and every crop computed from it lands somewhere else entirely, so the
    size is taken from a real decoded frame.
    """
    if path not in _dims:
        tmp = os.path.join(tempfile.gettempdir(), "prep_dims.png")
        run(FF + ["-i", path, "-frames:v", "1", tmp])
        _dims[path] = Image.open(tmp).size
    return _dims[path]


def cam_filter(path, xbias, ybias, zoom):
    """9:16 out of an HLG camera frame, tone mapped on the way."""
    sw, sh = frame_size(path)
    # take the tallest 9:16 window that fits, then punch in by `zoom`
    ch = min(sh, round(sw * H / W)) / zoom
    cw = (round(ch * W / H) // 2) * 2
    ch = (round(ch) // 2) * 2
    x = round((sw - cw) * xbias)
    y = round((sh - ch) * ybias)
    return f"{TONEMAP},crop={cw}:{ch}:{x}:{y},scale={W}:{H}:flags=lanczos"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["screen", "cam"])
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--ss", type=float, required=True)
    ap.add_argument("--t", type=float, required=True)
    ap.add_argument("--bias", type=float, default=0.0, help="screen: vertical framing 0..1")
    ap.add_argument("--x", type=float, default=0.5, help="cam: horizontal framing 0..1")
    ap.add_argument("--y", type=float, default=0.5, help="cam: vertical framing 0..1")
    ap.add_argument("--zoom", type=float, default=1.0, help="cam: punch in")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    path = resolve(args.src)
    out = args.out if os.path.isabs(args.out) else os.path.join(VIDEO_DIR, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    if args.kind == "screen":
        vf, edges = screen_filter(path, args.ss + args.t / 2, args.bias,
                                  span=args.t * 0.9)
        note = f"chrome {edges[0]}..{edges[1]}"
    else:
        vf = cam_filter(path, args.x, args.y, args.zoom)
        note = f"zoom {args.zoom}"

    run(FF + [
        "-ss", str(args.ss), "-i", path, "-t", str(args.t),
        "-vf", vf, "-r", str(args.fps),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "160k", "-ac", "2",
        out,
    ])
    print(f"{os.path.relpath(out, VIDEO_DIR)}  {args.t}s  ({note})")


if __name__ == "__main__":
    main()
