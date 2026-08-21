#!/usr/bin/env python3
"""
Single source of truth for the five spots.

Everything timed lives here - which frames of which source file, when each
voiceover line starts, where the music hits - because picture and sound have to
agree to the frame and keeping them in two files guarantees they eventually
won't. This writes three things per spot:

    public/<slug>/*.mp4        the cut clips
    public/<slug>/master.mp3   score + voiceover, mastered to -14 LUFS
    src/spots/<slug>.json      shot list + captions, read by src/Spot.tsx

    python3 tools/build_spots.py            # everything
    python3 tools/build_spots.py adapt      # one spot
    python3 tools/build_spots.py --audio    # skip re-cutting the clips

Grid: 120 BPM. Beat 0.5s, bar 2.0s. Every picture cut lands on a beat.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "audio"))

import prep  # noqa: E402
import score  # noqa: E402
import voice  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
PUB = os.path.join(VIDEO, "public")
SPEC = os.path.join(VIDEO, "src", "spots")
WORK = "/tmp/climbsmarter_build"

CAM = {
    "m1364": "IMG_1364.MOV",   # macro: shoe onto a red foothold, grey wall
    "m1365": "IMG_1365.MOV",   # macro: same hold, tighter
    "m1366": "IMG_1366.MOV",   # macro: shoe on hold, backlit against sky
    "gym": "IMG_1368.MOV",     # wide: climber on the roof, big windows
    "try": "IMG_1370.MOV",     # attempt on the black-volume wall
    "proj": "IMG_1371.MOV",    # attempt on the yellow overhang + walk-past
    "send": "IMG_1373.MOV",    # the send, bottom to top
}


def clip(name, src, ss, t, **kw):
    return dict(name=name, src=src, ss=ss, t=t, **kw)


# ---------------------------------------------------------------------------
# 1. It Adapts - the weekly check-in actually rewrites the plan
# ---------------------------------------------------------------------------
ADAPT = {
    "slug": "adapt",
    "seconds": 20.0,
    "shots": [
        # at, dur, clip, extras
        (0.0, 2.0, clip("hook", CAM["try"], 25.2, 2.0, kind="cam", x=0.0, y=0.85, zoom=1.55),
         {"gain": 0.06, "push": [1.0, 1.07]}),
        (2.0, 2.0, clip("weak", "screen1", 94.4, 2.0, kind="screen", bias=0.34), {}),
        (4.0, 2.0, clip("answers", "screen1", 102.6, 2.0, kind="screen", bias=0.26), {}),
        (6.0, 3.0, clip("typing", "screen1", 112.5, 3.0, kind="screen", bias=0.10), {}),
        (9.0, 2.0, clip("submit", "screen1", 116.9, 2.0, kind="screen", bias=0.34), {}),
        # the confirmation toast is only readable for about a second before the
        # app navigates on underneath it
        (11.0, 1.0, clip("saved", "screen1", 119.5, 1.0, kind="screen", bias=0.0), {}),
        (12.0, 3.0, clip("plan", "screen1", 44.8, 3.0, kind="screen", bias=0.15),
         {"push": [1.0, 1.08]}),
        (15.0, 2.5, clip("send", CAM["send"], 24.0, 2.5, kind="cam", x=0.60, y=0.5, zoom=1.4),
         {"gain": 0.07}),
    ],
    "vo": [
        # Nobody watching this has heard of ClimbSmarter, so the first line
        # names it and says what it is before any "it" appears.
        {"id": "a", "at": 2.15, "text": "ClimbSmarter writes your climbing training plan."},
        {"id": "b", "at": 5.05, "text": "Then it asks how the week actually went. Did it feel weak?"},
        {"id": "c", "at": 8.85, "text": "You answer in your own words."},
        {"id": "d", "at": 11.05, "text": "And next week gets rebuilt around it."},
        {"id": "e", "at": 15.15, "text": "Not a PDF. A coach that's paying attention."},
    ],
    "score": dict(
        bars=10, silent_bars={0}, groove_from=2,
        fx=[("impact", 2.0, None, 0.85), ("riser", 0.0, 2.0, 0.40),
            ("whoosh", 4.0, 0.4, 0.26), ("whoosh", 6.0, 0.4, 0.26),
            ("impact", 11.0, None, 0.55), ("riser", 13.0, 2.0, 0.60),
            ("impact", 15.0, None, 1.0), ("impact", 17.5, None, 0.45)],
        gain_points=[(0, .34), (2, .62), (6, .72), (11, .85), (13, .88),
                     (15, 1.0), (17.5, .95), (19, .8), (20, 0)],
    ),
}

# ---------------------------------------------------------------------------
# 2. Ask It Anything - one real exchange with the coach
# ---------------------------------------------------------------------------
ASK = {
    "slug": "ask",
    "seconds": 20.0,
    "shots": [
        # he walks straight past the lens - a face is the only real scroll-stopper
        (0.0, 2.0, clip("hook", CAM["proj"], 66.2, 2.0, kind="cam", x=1.0, y=1.0, zoom=1.4),
         {"gain": 0.08}),
        (2.0, 3.0, clip("askit", "screen1", 20.6, 3.0, kind="screen", bias=0.05), {}),
        # a bigger push than this crops the right-hand edge off the reply text
        (5.0, 6.0, clip("reply", "screen1", 25.0, 6.0, kind="screen", bias=0.30),
         {"push": [1.0, 1.07]}),
        (11.0, 3.0, clip("feet", CAM["m1365"], 17.0, 3.0, kind="cam", x=0.45, y=0.45, zoom=1.2),
         {"gain": 0.06}),
        (14.0, 3.5, clip("card", "screen1", 43.7, 3.5, kind="screen", bias=0.55),
         {"push": [1.0, 1.05]}),
    ],
    "vo": [
        {"id": "a", "at": 2.05, "text": "ClimbSmarter's a climbing app with a coach in it."},
        {"id": "b", "at": 5.15, "text": "So I asked it how to warm up for hangboard."},
        {"id": "c", "at": 8.15,
         "text": "Five rounds. Cruise the first three, then bump it a notch."},
        {"id": "d", "at": 12.55,
         "text": "And then this. Exhale, and place your feet silently."},
        {"id": "e", "at": 16.15, "text": "Hear a stomp? Drop a grade."},
    ],
    "score": dict(
        bars=10, silent_bars={0}, groove_from=1,
        fx=[("impact", 2.0, None, 0.70), ("riser", 0.5, 1.5, 0.34),
            ("whoosh", 5.0, 0.4, 0.24), ("riser", 9.5, 1.5, 0.44),
            ("impact", 11.0, None, 0.80), ("impact", 14.0, None, 0.55),
            ("impact", 17.5, None, 0.45)],
        gain_points=[(0, .34), (2, .60), (5, .60), (9, .72), (11, .95),
                     (14, .95), (17.5, 1.0), (19, .8), (20, 0)],
    ),
}

# ---------------------------------------------------------------------------
# 3. The Fueling Plan - the half of the app nobody knows about
# ---------------------------------------------------------------------------
FUEL = {
    "slug": "fuel",
    "seconds": 18.0,
    "shots": [
        (0.0, 2.0, clip("hook", CAM["gym"], 26.0, 2.0, kind="cam", x=0.5, y=0.10, zoom=1.3),
         {"gain": 0.06, "push": [1.0, 1.06]}),
        (2.0, 2.0, clip("logged", "screen1", 142.8, 2.0, kind="screen", bias=0.12), {}),
        (4.0, 2.0, clip("goals", "screen1", 147.2, 2.0, kind="screen", bias=0.30), {}),
        (6.0, 3.0, clip("plan", "screen1", 151.9, 3.0, kind="screen", bias=0.62),
         {"push": [1.0, 1.10]}),
        (9.0, 2.5, clip("meals", "screen1", 156.0, 2.5, kind="screen", bias=0.55), {}),
        (11.5, 2.0, clip("refresh", "screen1", 166.3, 2.0, kind="screen", bias=0.30), {}),
        # bookends the hook: same wall, same light, two seconds later
        (13.5, 2.0, clip("out", CAM["gym"], 28.8, 2.0, kind="cam", x=0.5, y=0.10, zoom=1.3),
         {"gain": 0.07}),
    ],
    "vo": [
        {"id": "a", "at": 2.15, "text": "ClimbSmarter plans your climbing training."},
        {"id": "b", "at": 4.75, "text": "It plans what you eat around it, too."},
        {"id": "c", "at": 7.35,
         "text": "Protein oats. Banana and rice cakes an hour out. Actual grams."},
        {"id": "d", "at": 12.35, "text": "Don't like it? Regenerate it."},
        {"id": "e", "at": 14.55, "text": "One app. Both halves."},
    ],
    "score": dict(
        bars=9, silent_bars={0}, groove_from=1,
        fx=[("impact", 2.0, None, 0.75), ("riser", 0.5, 1.5, 0.36),
            ("whoosh", 4.0, 0.4, 0.24), ("whoosh", 9.0, 0.4, 0.24),
            ("impact", 6.0, None, 0.45), ("riser", 12.0, 1.5, 0.50),
            ("impact", 13.5, None, 0.90), ("impact", 15.5, None, 0.45)],
        gain_points=[(0, .34), (2, .62), (6, .72), (9, .78), (11.5, .85),
                     (13.5, 1.0), (15.5, .95), (17, .8), (18, 0)],
    ),
}

# ---------------------------------------------------------------------------
# 4. The Grind - no app at all until the last card
# ---------------------------------------------------------------------------
GRIND = {
    "slug": "grind",
    "seconds": 22.0,
    "shots": [
        (0.0, 2.0, clip("a1", CAM["try"], 15.0, 2.0, kind="cam", x=0.0, y=0.82, zoom=1.55),
         {"gain": 0.10}),
        (2.0, 1.0, clip("a2", CAM["try"], 17.9, 1.0, kind="cam", x=0.0, y=0.80, zoom=1.55),
         {"gain": 0.10}),
        (3.0, 1.0, clip("a3", CAM["try"], 21.8, 1.0, kind="cam", x=0.05, y=0.78, zoom=1.55),
         {"gain": 0.10}),
        (4.0, 1.0, clip("a4", CAM["try"], 26.4, 1.0, kind="cam", x=0.05, y=0.80, zoom=1.55),
         {"gain": 0.10}),
        (5.0, 1.0, clip("b1", CAM["proj"], 55.8, 1.0, kind="cam", x=0.0, y=0.95, zoom=1.55),
         {"gain": 0.10}),
        (6.0, 1.0, clip("b2", CAM["proj"], 58.8, 1.0, kind="cam", x=0.0, y=0.95, zoom=1.55),
         {"gain": 0.10}),
        (7.0, 1.0, clip("b3", CAM["proj"], 62.2, 1.0, kind="cam", x=0.08, y=0.92, zoom=1.55),
         {"gain": 0.10}),
        (8.0, 1.0, clip("b4", CAM["proj"], 64.3, 1.0, kind="cam", x=0.12, y=0.88, zoom=1.55),
         {"gain": 0.10}),
        (9.0, 1.0, clip("chalk", CAM["m1366"], 22.2, 1.0, kind="cam", x=0.10, y=0.35, zoom=1.5),
         {"gain": 0.10}),
        # he walks straight past the lens here - a natural wipe into the send
        (10.0, 2.0, clip("walk", CAM["proj"], 66.4, 2.0, kind="cam", x=1.0, y=1.0, zoom=1.55),
         {"gain": 0.12}),
        (12.0, 3.0, clip("s1", CAM["send"], 16.5, 3.0, kind="cam", x=0.0, y=0.5, zoom=1.4),
         {"gain": 0.10}),
        (15.0, 2.5, clip("s2", CAM["send"], 24.0, 2.5, kind="cam", x=0.60, y=0.5, zoom=1.4),
         {"gain": 0.10}),
        (17.5, 2.0, clip("s3", CAM["send"], 31.0, 2.0, kind="cam", x=1.0, y=0.36, zoom=1.4),
         {"gain": 0.10}),
    ],
    "vo": [
        {"id": "a", "at": 2.15, "text": "Board limit practice. Three problems, five attempts each."},
        # No app UI in this spot at all, so the product gets named here, in the
        # middle, where the caption is still on screen - at the end it would be
        # buried under the end card.
        {"id": "b", "at": 6.55,
         "text": "That's what ClimbSmarter put in today's plan. Something just out of reach, on purpose."},
        {"id": "c", "at": 12.35,
         "text": "You're not meant to send it today. You're meant to get closer."},
        {"id": "d", "at": 16.05, "text": "And then one day, it goes."},
    ],
    "score": dict(
        bars=11, silent_bars={0}, groove_from=1,
        fx=[("impact", 2.0, None, 0.75), ("riser", 0.5, 1.5, 0.36),
            ("impact", 5.0, None, 0.45), ("impact", 8.0, None, 0.55),
            ("riser", 10.0, 2.0, 0.70), ("impact", 12.0, None, 1.0),
            ("impact", 17.5, None, 0.60), ("impact", 19.5, None, 0.45)],
        gain_points=[(0, .32), (2, .58), (5, .70), (8, .78), (10, .85),
                     (12, 1.0), (17.5, 1.0), (19.5, .9), (21, .75), (22, 0)],
    ),
}

# ---------------------------------------------------------------------------
# 5. Tip 01: Quiet Feet - organic, teaches one thing, soft plug
# ---------------------------------------------------------------------------
QUIET = {
    "slug": "quietfeet",
    "seconds": 20.0,
    "shots": [
        (0.0, 2.0, clip("hook", CAM["m1366"], 5.2, 2.0, kind="cam", x=0.10, y=0.35, zoom=1.35),
         {"gain": 0.08}),
        (2.0, 3.0, clip("place1", CAM["m1364"], 16.4, 3.0, kind="cam", x=0.45, y=0.45, zoom=1.2),
         {"gain": 0.08}),
        (5.0, 3.0, clip("place2", CAM["m1365"], 16.8, 3.0, kind="cam", x=0.45, y=0.45, zoom=1.2),
         {"gain": 0.08}),
        # The explainer animation goes here. tools/cut_anim.py overwrites this
        # clip with the recorded animation; until it does, the slot holds real
        # footage of the same thing so the spot is never left with a hole.
        (8.0, 4.0, clip("contact", CAM["m1364"], 26.2, 4.0, kind="cam",
                        x=0.45, y=0.45, zoom=1.15), {"gain": 0.08}),
        (12.0, 3.0, clip("drive", CAM["m1366"], 21.6, 3.0, kind="cam", x=0.10, y=0.35, zoom=1.25),
         {"gain": 0.08}),
        (15.0, 3.5, clip("cue", "screen1", 27.0, 3.5, kind="screen", bias=0.34),
         {"push": [1.0, 1.12]}),
    ],
    "vo": [
        {"id": "a", "at": 2.15,
         "text": "Don't stomp it. Look at the hold, and place the toe once."},
        {"id": "b", "at": 5.95, "text": "Shuffle or re-grip, and your fingers pay for it."},
        # over the explainer animation
        {"id": "c", "at": 8.65,
         "text": "A stomp bounces you off the hold. A quiet placement presses into it."},
        {"id": "d", "at": 13.25, "text": "Place it once. Then trust it."},
        {"id": "e", "at": 16.15, "text": "That's from ClimbSmarter. It plans my climbing."},
    ],
    "score": dict(
        bars=10, silent_bars={0}, groove_from=1,
        fx=[("impact", 2.0, None, 0.70), ("riser", 0.5, 1.5, 0.34),
            ("whoosh", 5.0, 0.4, 0.24), ("impact", 8.0, None, 0.55),
            ("whoosh", 12.0, 0.4, 0.24), ("impact", 15.0, None, 0.50),
            ("impact", 17.0, None, 0.45)],
        gain_points=[(0, .34), (2, .58), (5, .62), (8, .70), (12, .80),
                     (15, .88), (17, .95), (19, .8), (20, 0)],
    ),
}

SPOTS = {s["slug"]: s for s in (ADAPT, ASK, FUEL, GRIND, QUIET)}

# Whisper's spelling ends up burned into the picture, so anything it reliably
# gets wrong is corrected here - its timings are kept either way.
FIXES = {"pdf": "PDF", "hangboard": "hangboard"}


def cut_clips(spot):
    out = os.path.join(PUB, spot["slug"])
    os.makedirs(out, exist_ok=True)
    for at, dur, c, _ in spot["shots"]:
        dst = os.path.join(out, c["name"] + ".mp4")
        path = prep.resolve(c["src"])
        if c["kind"] == "screen":
            vf, edges = prep.screen_filter(path, c["ss"] + c["t"] / 2,
                                           c.get("bias", 0.0), span=c["t"] * 0.9)
            note = f"chrome {edges[0]}..{edges[1]}"
        else:
            vf = prep.cam_filter(path, c.get("x", 0.5), c.get("y", 0.5), c.get("zoom", 1.0))
            note = f"zoom {c.get('zoom', 1.0)}"
        prep.run(prep.FF + [
            "-ss", str(c["ss"]), "-i", path, "-t", str(c["t"]),
            "-vf", vf, "-r", "30",
            "-c:v", "libx264", "-preset", "slow", "-crf", "17",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "160k", "-ac", "2", dst,
        ])
        print(f"  {spot['slug']}/{c['name']}.mp4  {c['t']}s  ({note})")


def build_audio(spot):
    work = os.path.join(WORK, spot["slug"])
    os.makedirs(work, exist_ok=True)
    vo, caps = voice.build_lines(spot["vo"], work, fix=FIXES)

    # A line that runs into the next one reads as two people talking at once,
    # and one that runs past the end is simply cut off mid-word.
    for ln, nxt in zip(spot["vo"], spot["vo"][1:] + [None]):
        end = ln["at"] + ln["dur"]
        if nxt and end > nxt["at"] - 0.15:
            print(f"  ! {spot['slug']} line {ln['id']} ends {end:.2f}s, "
                  f"line {nxt['id']} starts {nxt['at']:.2f}s "
                  f"(overlap {end - nxt['at']:.2f}s)")
        if end > spot["seconds"]:
            print(f"  ! {spot['slug']} line {ln['id']} runs to {end:.2f}s "
                  f"of {spot['seconds']}s")

    os.environ["VO_DIR"] = work
    score.VO_DIR = work
    wav = os.path.join(work, "master.wav")
    dur, lufs = score.build(vo=vo, out_path=wav, **spot["score"])

    mp3 = os.path.join(PUB, spot["slug"], "master.mp3")
    os.makedirs(os.path.dirname(mp3), exist_ok=True)
    prep.run(prep.FF + ["-i", wav, "-c:a", "libmp3lame", "-b:a", "256k", mp3])
    print(f"  {spot['slug']}/master.mp3  {dur:.1f}s  {lufs:.1f} LUFS  "
          f"({len(caps)} caption cards)")
    return caps


def write_spec(spot, caps):
    shots = []
    for at, dur, c, extra in spot["shots"]:
        shots.append({"at": at, "dur": dur,
                      "src": f"{spot['slug']}/{c['name']}.mp4", **extra})
    os.makedirs(SPEC, exist_ok=True)
    path = os.path.join(SPEC, f"{spot['slug']}.json")
    with open(path, "w") as f:
        json.dump({"shots": shots, "captions": caps}, f, indent=1)
    print(f"  src/spots/{spot['slug']}.json")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    audio_only = "--audio" in sys.argv
    clips_only = "--clips" in sys.argv
    for slug in (args or SPOTS):
        spot = SPOTS[slug]
        print(spot["slug"])
        if not audio_only:
            cut_clips(spot)
        if not clips_only:
            caps = build_audio(spot)
            write_spec(spot, caps)


if __name__ == "__main__":
    main()
