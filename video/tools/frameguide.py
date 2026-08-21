#!/usr/bin/env python3
"""
Show a source frame with the 9:16 crop window drawn on it.

Framing a vertical crop out of a landscape 4K plate by eye from a contact sheet
does not work - the climber ends up just outside the window. This draws the
exact rectangle `prep.cam_filter` would take, over a labelled grid, so the
x-bias and zoom can be read off rather than guessed.

    python3 tools/frameguide.py IMG_1370.MOV 14,18 0.13:0.5:1.2,0.4:0.6:1.6
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import prep

OUT = os.environ.get("SCOUT_DIR", "/tmp/climbsmarter_scout")


def guide(src, times, windows, name=None):
    path = prep.resolve(src)
    tiles = []
    for t in times:
        tmp = "/tmp/_fg.png"
        subprocess.run(prep.FF + ["-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                                  "-vf", prep.TONEMAP + ",scale=640:-2", tmp],
                       cwd=prep.VIDEO_DIR, capture_output=True)
        im = Image.open(tmp).convert("RGB")
        W, H = im.size
        d = ImageDraw.Draw(im, "RGBA")
        for i in range(1, 20):
            x = W * i / 20
            d.line([(x, 0), (x, H)], fill=(255, 255, 255, 70), width=1)
            if i % 2 == 0:
                d.text((x + 2, 2), f".{i * 5:02d}", fill=(120, 220, 255))
        for i in range(1, 10):
            d.line([(0, H * i / 10), (W, H * i / 10)], fill=(255, 255, 255, 50), width=1)
        sw, sh = prep.frame_size(path)
        for xb, yb, zoom in windows:
            ch = min(sh, round(sw * 1920 / 1080)) / zoom
            cw = round(ch * 1080 / 1920)
            x0 = (sw - cw) * xb * W / sw
            y0 = (sh - ch) * yb * H / sh
            d.rectangle([x0, y0, x0 + cw * W / sw, y0 + ch * H / sh],
                        outline=(249, 115, 22), width=3)
            d.text((x0 + 6, y0 + 6), f"x{xb} y{yb} z{zoom}", fill=(249, 115, 22))
        d.text((4, H - 14), f"{t:.1f}s", fill=(250, 200, 60))
        tiles.append(im)

    tw, th = tiles[0].size
    cols = min(len(tiles), 5)
    rows = (len(tiles) + cols - 1) // cols
    sh = Image.new("RGB", (cols * tw, rows * th), (10, 10, 12))
    for i, im in enumerate(tiles):
        sh.paste(im, ((i % cols) * tw, (i // cols) * th))
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, f"fg_{name or src.split('.')[0]}.jpg")
    sh.save(dst, quality=90)
    print(dst, sh.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    src = a[0]
    times = [float(v) for v in a[1].split(",")]
    wins = [tuple(float(v) for v in p.split(":")) for p in a[2].split(",")]
    guide(src, times, wins, name=a[3] if len(a) > 3 else None)
