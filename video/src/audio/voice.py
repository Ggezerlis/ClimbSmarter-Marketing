"""
Voiceover: synthesis, processing, and word-level caption timings.

No one is on camera in these spots, so the read carries the whole message and
has to sound like a climber talking, not a station announcer - hence the
Conversation/Casual voice and a fairly aggressive processing chain (the raw TTS
is thin and sits behind the music otherwise).

The caption timings are transcribed back off the *processed* audio rather than
taken from the script, so the karaoke highlight lands on the word actually being
said, including wherever the synthesiser decided to breathe.
"""
import hashlib
import json
import os
import subprocess

import numpy as np
import soundfile as sf
from scipy import signal as sig

SR = 48_000
VOICE = "en-US-BrianMultilingualNeural"
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("VO_CACHE", "/tmp/climbsmarter_vo")

_whisper = None


def _lp(x, c, o=4):
    return sig.filtfilt(*sig.butter(o, np.clip(c, 30, SR / 2 - 100) / (SR / 2), "low"), x)


def _hp(x, c, o=4):
    return sig.filtfilt(*sig.butter(o, c / (SR / 2), "high"), x)


def _compress(x, thresh=0.16, ratio=4.0, attack_ms=6.0, release_ms=90.0):
    """Level the read so the quiet ends of sentences still cut through the bed."""
    env = np.abs(x)
    a = np.exp(-1.0 / (attack_ms / 1000 * SR))
    r = np.exp(-1.0 / (release_ms / 1000 * SR))
    smooth = np.empty_like(env)
    g = 0.0
    for i, v in enumerate(env):
        g = a * g + (1 - a) * v if v > g else r * g + (1 - r) * v
        smooth[i] = g
    over = np.maximum(smooth, thresh)
    return x * (thresh + (over - thresh) / ratio) / over


def _deess(x):
    """Brian pushes his sibilants; duck 5-9k only when they spike."""
    sos = sig.butter(4, [5000, 9000], btype="band", fs=SR, output="sos")
    s = sig.sosfilt(sos, x)
    env = _lp(np.abs(s), 40)
    duck = np.clip(1 - (env / (np.percentile(env, 99.2) + 1e-9) - 1) * 0.6, 0.45, 1.0)
    return x - s * (1 - duck)


def synth(text, path):
    """edge-tts to 48k mono wav, cached on the text so reruns are free."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    key = hashlib.sha1(f"{VOICE}|{text}".encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    raw = os.path.join(CACHE, f"{key}.mp3")
    if not os.path.exists(raw):
        subprocess.run(
            # a negative pitch has to be glued to the flag or argparse reads it
            # as the next option
            ["edge-tts", "--voice", VOICE, "--rate=+6%", "--pitch=-2Hz",
             "--text", text, "--write-media", raw],
            check=True, capture_output=True)
    wav = os.path.join(CACHE, f"{key}.wav")
    if not os.path.exists(wav):
        subprocess.run(
            ["npx", "remotion", "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", raw, "-ar", str(SR), "-ac", "1", wav],
            check=True, capture_output=True, cwd=os.path.join(HERE, "..", ".."))
    x, _ = sf.read(wav)
    if x.ndim > 1:
        x = x.mean(axis=1)

    # trim the silence the synthesiser leaves on both ends, or the line drifts
    # off the beat it was written for
    amp = _lp(np.abs(x), 30)
    live = np.where(amp > amp.max() * 0.02)[0]
    if len(live):
        x = x[max(0, live[0] - int(0.03 * SR)):min(len(x), live[-1] + int(0.12 * SR))]

    x = _hp(x, 95)
    x = _deess(x)
    x = _compress(x)
    # presence, so it reads on a phone speaker over the music
    x += sig.sosfilt(sig.butter(2, [1800, 5200], btype="band", fs=SR, output="sos"), x) * 0.45
    x = _lp(x, 13000)
    x = np.tanh(x * 1.5) * 0.62
    x /= np.max(np.abs(x)) + 1e-9
    x *= 0.88
    sf.write(path, x, SR)
    return len(x) / SR


def words(path, spoken=None):
    """Word timings, relative to the start of the file."""
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = _whisper.transcribe(path, word_timestamps=True, beam_size=5,
                                  initial_prompt=spoken)
    out = []
    for s in segs:
        for w in s.words:
            out.append({"t": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
    return [w for w in out if w["t"]]


def chunk(ws, offset, per=4, gap=0.55, lift=None):
    """
    Group words into caption cards.

    A card breaks on a clear pause or at `per` words, and a card's end is
    clamped just short of the next one - otherwise a card that holds too long
    sits underneath its successor.
    """
    cards = []
    cur = []
    for i, w in enumerate(ws):
        cur.append(w)
        nxt = ws[i + 1] if i + 1 < len(ws) else None
        brk = (
            nxt is None
            or len(cur) >= per
            or nxt["s"] - w["e"] > gap
            or w["t"].endswith((".", "!", "?", ",", "—", ":"))
            and len(cur) >= 2
        )
        if brk:
            cards.append(cur)
            cur = []
    out = []
    for i, c in enumerate(cards):
        start = offset + c[0]["s"] - 0.10
        end = offset + c[-1]["e"] + 0.42
        if i + 1 < len(cards):
            # never outlive the next card, but never cut the last word's
            # highlight short either
            end = max(min(end, offset + cards[i + 1][0]["s"] - 0.06),
                      offset + c[-1]["e"] + 0.05)
        card = {
            "start": round(float(max(start, 0)), 3),
            "end": round(float(end), 3),
            "words": [{"t": w["t"], "s": round(float(offset + w["s"]), 3),
                       "e": round(float(offset + w["e"]), 3)} for w in c],
        }
        if lift:
            card["lift"] = lift
        out.append(card)
    return out


def build_lines(lines, workdir, fix=None):
    """
    lines: [{"id","text","at", "lift"?, "say"?}]  ->  (vo map, caption cards)

    `say` overrides the text handed to the synthesiser (spelling a brand the way
    it should be pronounced); `fix` rewrites what the transcript claims a word
    was, keeping whisper's timing but showing the right spelling.
    """
    vo, caps = {}, []
    for ln in lines:
        wav = os.path.join(workdir, f"{ln['id']}.wav")
        dur = synth(ln.get("say", ln["text"]), wav)
        ws = words(wav, spoken=ln["text"])
        for w in ws:
            for bad, good in (fix or {}).items():
                if w["t"].lower().strip(".,!?") == bad.lower():
                    w["t"] = good + w["t"][len(bad):] if len(w["t"]) > len(bad) else good
        caps += chunk(ws, ln["at"], lift=ln.get("lift"))
        vo[os.path.basename(wav)] = ln["at"]
        ln["dur"] = dur
    return vo, caps


def write_captions(caps, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(caps, f, indent=1)
    return path
