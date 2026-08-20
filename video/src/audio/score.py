"""
Score + master-mix engine for the ClimbSmarter ads.

The music is written here rather than licensed, for two reasons: the ad carries
no music rights, and the arrangement can be pinned to the picture edit — every
cut lands on a beat, the fall lands on an impact, the send lands on the drop.

    python3 score.py            # builds both the 32s and the 15s masters

Run from this directory; it writes the mixes into ../../public/.
"""
import os
import numpy as np
import soundfile as sf
from scipy import signal as sig

SR = 48_000
BPM = 120.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
HERE = os.path.dirname(os.path.abspath(__file__))
VO_DIR = os.environ.get("VO_DIR", HERE)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _lp(x, c, o=4):
    return sig.filtfilt(*sig.butter(o, np.clip(c, 30, SR / 2 - 100) / (SR / 2), "low"), x)


def _hp(x, c, o=4):
    return sig.filtfilt(*sig.butter(o, c / (SR / 2), "high"), x)


def _reverb(x, decay=1.4, mix=0.25):
    L = int(decay * SR)
    ir = np.random.randn(L) * np.exp(-np.linspace(0, 7, L))
    ir = _lp(ir, 5200)
    ir[: int(0.005 * SR)] = 0
    wet = sig.fftconvolve(x, ir)[: len(x)]
    return (1 - mix) * x + mix * wet / (np.max(np.abs(wet)) + 1e-9)


def _note(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _lufs(x):
    """Integrated loudness, BS.1770-style (K-weighting + gating).

    Takes the stereo signal, since channel powers sum: measuring the mono bus
    instead reads about 3 dB quiet and the file ships too loud.
    """
    x = np.atleast_2d(x.T).T if x.ndim > 1 else x[:, None]
    y = sig.lfilter(*sig.butter(2, 60 / (SR / 2), "high"), x, axis=0)
    y = y + sig.lfilter(*sig.butter(2, 1500 / (SR / 2), "high"), x, axis=0) * 0.6
    blk, step = int(0.4 * SR), int(0.1 * SR)
    p = [-0.691 + 10 * np.log10(m)
         for i in range(0, len(y) - blk, step)
         for m in [np.mean(y[i:i + blk] ** 2, axis=0).sum()] if m > 0]
    g = np.array([v for v in p if v > -70])
    if not len(g):
        return -70.0
    rel = -0.691 + 10 * np.log10(np.mean(10 ** ((g + 0.691) / 10))) - 10
    g2 = g[g > rel]
    return -0.691 + 10 * np.log10(np.mean(10 ** ((g2 + 0.691) / 10))) if len(g2) else rel


def _limit(x, ceiling=0.89, attack_ms=1.5, release_ms=120.0):
    """Look-ahead peak limiter. The impacts are far louder than the bed, so
    without this the whole mix has to sit quiet just to keep them under 0 dBFS."""
    look = int(attack_ms / 1000 * SR)
    pad = np.concatenate([x, np.zeros((look,) + x.shape[1:])])
    peak = np.abs(pad).max(axis=1) if pad.ndim > 1 else np.abs(pad)
    # running max over the look-ahead window
    env = np.array([peak[i:i + look + 1].max() for i in range(len(peak))])
    gain = np.minimum(1.0, ceiling / (env + 1e-9))
    # smooth the gain so it releases rather than pumping per-sample
    a = np.exp(-1.0 / (release_ms / 1000 * SR))
    out = np.empty_like(gain)
    g = 1.0
    for i, v in enumerate(gain):
        g = v if v < g else a * g + (1 - a) * v
        out[i] = g
    return (pad * (out[:, None] if pad.ndim > 1 else out))[:len(x)]


def _normalise(x, target_lufs=-14.0, ceiling_db=-2.0):
    """Social platforms normalise to about -14 LUFS; leave true-peak headroom
    so the AAC encode does not clip."""
    limit = 10 ** (ceiling_db / 20)
    x = x * 10 ** ((target_lufs - _lufs(x)) / 20)
    x = _limit(x, ceiling=limit)
    peak = np.max(np.abs(x)) + 1e-9
    if peak > limit:
        x *= limit / peak
    return x


def build(bars, silent_bars, groove_from, fx, gain_points, vo, out_path):
    """
    bars          total length in bars
    silent_bars   bars where the kit drops out (the fall lands in that hole)
    groove_from   first bar carrying hats/claps/arp
    fx            list of ("impact"|"riser"|"whoosh", start, arg, amp)
    gain_points   [(seconds, gain), ...] arrangement automation
    vo            {"file.wav": start_seconds}
    """
    N = int(bars * BAR * SR)
    t = np.arange(N) / SR
    dur = N / SR

    def env(start, d, a=0.002, dec=0.1, s=0.0, r=0.05):
        e = np.zeros(N)
        i0, n = int(start * SR), int(d * SR)
        if i0 >= N:
            return e
        n = min(n, N - i0)
        seg = np.zeros(n)
        na = min(int(a * SR), n)
        nd = min(int(dec * SR), max(n - na, 0))
        if na:
            seg[:na] = np.linspace(0, 1, na)
        if nd:
            seg[na:na + nd] = np.linspace(1, s, nd)
        if na + nd < n:
            seg[na + nd:] = s
        nr = min(int(r * SR), n)
        if nr:
            seg[-nr:] *= np.linspace(1, 0, nr)
        e[i0:i0 + n] = seg
        return e

    saw = lambda f: sig.sawtooth(2 * np.pi * f * t)

    # ---- kit ----
    kick = np.zeros(N)
    kick_times = []
    for bar in range(bars):
        for b in range(4):
            if bar in silent_bars:
                continue
            if bar == 0 and b % 2:
                continue
            s = bar * BAR + b * BEAT
            kick_times.append(s)
            n = int(0.12 * SR)
            pitch = 145 * np.exp(-np.linspace(0, 34, n))
            body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-np.linspace(0, 9, n))
            click = _hp(np.random.randn(n), 2200) * np.exp(-np.linspace(0, 90, n)) * 0.30
            i0 = int(s * SR)
            m = min(n, N - i0)
            if m > 0:
                kick[i0:i0 + m] += body[:m] * 0.55 + click[:m]

    clap = np.zeros(N)
    for bar in range(groove_from, bars):
        for b in (1, 3):
            n = int(0.16 * SR)
            i0 = int((bar * BAR + b * BEAT) * SR)
            m = min(n, N - i0)
            if m > 0:
                clap[i0:i0 + m] += (np.random.randn(n) * np.exp(-np.linspace(0, 16, n)))[:m] * 0.5
    clap = _reverb(_hp(clap, 1400), 0.5, 0.35)

    hat = np.zeros(N)
    for bar in range(groove_from, bars):
        for i in range(8):
            amp = (0.22 if i % 2 == 0 else 0.13) * (0.6 if bar < groove_from + 2 else 1.0)
            n = int(0.05 * SR)
            i0 = int((bar * BAR + i * BEAT / 2) * SR)
            m = min(n, N - i0)
            if m > 0:
                hat[i0:i0 + m] += (np.random.randn(n) * np.exp(-np.linspace(0, 26, n)))[:m] * amp
    hat = _hp(hat, 7000)

    # ---- harmony: A minor, Am / F / C / G ----
    PROG = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
    pad = np.zeros(N)
    bass = np.zeros(N)
    for bar in range(bars):
        ch = PROG[bar % 4]
        s = bar * BAR
        e = env(s, BAR, a=0.35, dec=0.2, s=0.85, r=0.5)
        for m in ch:
            f = _note(m - 12)
            pad += sum(saw(f * (1 + d)) for d in (-0.004, 0, 0.004)) / 3 * e * 0.17
        root = _note(ch[0] - 24)
        be = env(s, BAR, a=0.01, dec=0.15, s=0.75, r=0.25)
        # octave-up saw keeps the bass audible on phone speakers
        bass += (np.sin(2 * np.pi * root * t) * 0.22 + saw(root * 2) * 0.30) * be

    cut = np.interp(t, [0, groove_from * BAR, dur * 0.6, dur], [380, 1500, 3200, 3000])
    opened = np.zeros(N)
    step = SR // 4
    for i in range(0, N, step):
        j = min(i + step, N)
        opened[i:j] = _lp(pad[max(0, i - 2000):j], float(cut[i]))[-(j - i):]
    pad = opened
    bass = _lp(_hp(bass, 55), 900)

    arp = np.zeros(N)
    PENT = [69, 72, 74, 76, 79, 81]
    for bar in range(groove_from, bars):
        div = 4 if bar < bars * 0.62 else 8
        for i in range(div):
            s = bar * BAR + i * (BAR / div)
            f = _note(PENT[(bar * 3 + i) % len(PENT)])
            e = env(s, BAR / div, a=0.003, dec=0.09, r=0.02)
            arp += (saw(f) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5) * e * 0.30
    arp = _reverb(_hp(_lp(arp, 5000), 300), 1.1, 0.32)

    # ---- transitions ----
    fxbus = np.zeros(N)
    for kind, start, arg, amp in fx:
        i0 = int(start * SR)
        if kind == "impact":
            n = min(int(1.3 * SR), N - i0)
            if n <= 0:
                continue
            pitch = 95 * np.exp(-np.linspace(0, 5, n))
            boom = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-np.linspace(0, 6, n))
            crash = _hp(np.random.randn(n), 3500) * np.exp(-np.linspace(0, 9, n)) * 0.35
            fxbus[i0:i0 + n] += (boom + crash) * amp
        elif kind == "riser":
            n = min(int(arg * SR), N - i0)
            if n <= 0:
                continue
            noise = np.random.randn(n)
            o = np.zeros(n)
            st = SR // 8
            for i in range(0, n, st):
                j = min(i + st, n)
                o[i:j] = _hp(noise[max(0, i - 1500):j], 400 + 5500 * (i / n) ** 2)[-(j - i):]
            fxbus[i0:i0 + n] += o * np.linspace(0, 1, n) ** 2.2 * amp
        elif kind == "whoosh":
            i0 = int((start - arg / 2) * SR)
            n = min(int(arg * SR), N - max(i0, 0))
            if i0 < 0 or n <= 0:
                continue
            noise = np.random.randn(n)
            o = np.zeros(n)
            st = SR // 16
            for i in range(0, n, st):
                j = min(i + st, n)
                o[i:j] = _hp(noise[max(0, i - 1200):j], 600 + 4000 * np.sin(np.pi * i / n))[-(j - i):]
            fxbus[i0:i0 + n] += o * np.sin(np.pi * np.linspace(0, 1, n)) * amp

    # ---- mix ----
    duck = np.ones(N)
    for s in kick_times:
        i0 = int(s * SR)
        n = min(int(0.34 * SR), N - i0)
        if n > 0:
            duck[i0:i0 + n] = np.minimum(
                duck[i0:i0 + n], 1 - 0.72 * np.exp(-np.linspace(0, 5, n)))

    music = kick + clap * 1.25 + hat * 1.15 + (bass + pad * 1.5 + arp * 1.7) * duck + fxbus
    gx, gy = zip(*gain_points)
    music *= np.interp(t, gx, gy)
    music = _hp(music, 42)
    music += sig.sosfilt(
        sig.butter(2, [900, 5200], btype="band", fs=SR, output="sos"), music) * 0.55
    music = _reverb(np.tanh(music * 1.35) * 0.86, 0.9, 0.10)
    music /= np.max(np.abs(music)) + 1e-9

    # ---- voiceover, music ducking beneath it ----
    vobus = np.zeros(N)
    spans = []
    for fn, at in vo.items():
        x, _ = sf.read(os.path.join(VO_DIR, fn))
        i0 = int(at * SR)
        n = min(len(x), N - i0)
        vobus[i0:i0 + n] += x[:n]
        spans.append((at, at + n / SR))

    vduck = np.ones(N)
    ramp = int(0.25 * SR)
    for s, e in spans:
        i0, i1 = int(max(s - 0.25, 0) * SR), int(min(e + 0.35, dur) * SR)
        seg = np.full(i1 - i0, 0.34)
        seg[:ramp] = np.linspace(1, 0.34, ramp)
        seg[-ramp:] = np.linspace(0.34, 1, ramp)
        vduck[i0:i1] = np.minimum(vduck[i0:i1], seg)

    mono = np.tanh((music * 0.62 * vduck + vobus * 0.95) * 1.1)
    master = _normalise(np.stack([mono, np.roll(mono, 60)], 1))
    sf.write(out_path, master, SR)
    return dur, _lufs(master)


if __name__ == "__main__":
    pub = os.path.join(HERE, "..", "..", "public")

    # ---- 32s organic cut ----
    d, L = build(
        bars=16, silent_bars={1, 2}, groove_from=3,
        fx=[("impact", 2.0, None, 0.95), ("riser", 4.0, 2.0, 0.42),
            ("impact", 6.0, None, 0.50), ("riser", 17.0, 3.0, 0.62),
            ("impact", 20.0, None, 1.00), ("impact", 29.0, None, 0.50),
            ("whoosh", 9.0, 0.45, 0.28), ("whoosh", 13.0, 0.45, 0.28),
            ("whoosh", 24.0, 0.45, 0.28)],
        gain_points=[(0, .30), (2, .55), (4, .40), (6, .80), (17, .85),
                     (20, 1.0), (29, 1.0), (30.5, .85), (32, 0)],
        vo={"vo_a.wav": 2.15, "vo_b.wav": 6.25, "vo_c.wav": 20.30, "vo_d.wav": 29.25},
        out_path=os.path.join(pub, "v3", "master.wav"))
    print(f"32s master: {d:.1f}s  {L:.1f} LUFS")

    # ---- 15s paid cut ----
    d, L = build(
        bars=8, silent_bars={1}, groove_from=2,
        fx=[("impact", 2.0, None, 0.95), ("riser", 2.5, 1.5, 0.45),
            ("riser", 6.0, 2.0, 0.60), ("impact", 8.0, None, 1.00),
            ("impact", 12.5, None, 0.50), ("whoosh", 6.0, 0.4, 0.28)],
        gain_points=[(0, .35), (2, .55), (4, .80), (6, .85), (8, 1.0),
                     (12.5, 1.0), (14.0, .9), (15.0, 0), (16, 0)],
        vo={"s15_a.wav": 2.10, "s15_b.wav": 5.40, "s15_c.wav": 10.20,
            "s15_d.wav": 12.35},
        out_path=os.path.join(pub, "v15", "master.wav"))
    print(f"15s master: {d:.1f}s  {L:.1f} LUFS")
