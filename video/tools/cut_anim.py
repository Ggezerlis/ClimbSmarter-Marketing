#!/usr/bin/env python3
"""
Drop the recorded explainer animation into the Quiet Feet spot.

The animation is a published web page, and the browser in this sandbox has no
egress, so it is mirrored to disk, served from 127.0.0.1 and captured with
Playwright (see the scratchpad scripts). What lands here is that recording:
this only trims a four-second window out of it and writes it over the clip the
spot already reserves, so the edit itself never has to change.

    python3 tools/cut_anim.py /path/to/page.webm 6.0
"""
import os
import sys

import prep

DST = os.path.join(prep.VIDEO_DIR, "public", "quietfeet", "contact.mp4")


def main():
    src, start = sys.argv[1], float(sys.argv[2])
    dur = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
    prep.run(prep.FF + [
        "-ss", str(start), "-i", src, "-t", str(dur),
        "-vf", f"scale={prep.W}:{prep.H}:flags=lanczos,format=yuv420p", "-r", "30",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-an", DST,
    ])
    print(f"quietfeet/contact.mp4  {dur}s  from {os.path.basename(src)} @{start}s")


if __name__ == "__main__":
    main()
