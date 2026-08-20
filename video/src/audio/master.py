"""
Builds the ad's master audio: original score + processed voiceover, mixed with
sidechain ducking, at 120 BPM so every picture cut lands on a bar line.

Edit grid (bar = 2.0s):
   0.0  fail clip, the fall lands on the bar at 2.0
   4.0  beat card
   6.0  app: onboarding      (groove enters)
   9.0  app: today's session
  13.0  app: progress
  17.0  training b-roll      (riser builds)
  20.0  THE SEND             (drop)
  24.0  top-out
  29.0  end card
  32.0  end
"""
import numpy as np
import soundfile as sf
from scipy import signal as sig

SR = 48_000
BPM, BEAT, BAR, BARS = 120.0, 0.5, 2.0, 16
DUR = BARS * BAR
N = int(DUR * SR)
t = np.arange(N) / SR
SC = "/tmp/claude-0/-home-user-ClimbSmarter-Marketing/863fe68c-182d-51cd-a651-cef894d96a88/scratchpad"

# where each voiceover line starts
VO_AT = {"a": 2.15, "b": 6.25, "c": 20.30, "d": 29.25}


def env(start, dur, a=0.002, d=0.1, s=0.0, r=0.05, peak=1.0):
    e = np.zeros(N); i0 = int(start * SR); n = int(dur * SR)
    if i0 >= N: return e
    n = min(n, N - i0); seg = np.zeros(n)
    na, nd = min(int(a * SR), n), 0
    nd = min(int(d * SR), max(n - na, 0))
    if na: seg[:na] = np.linspace(0, peak, na)
    if nd: seg[na:na + nd] = np.linspace(peak, peak * s, nd)
    if na + nd < n: seg[na + nd:] = peak * s
    nr = min(int(r * SR), n)
    if nr: seg[-nr:] *= np.linspace(1, 0, nr)
    e[i0:i0 + n] = seg
    return e


note = lambda m: 440.0 * 2 ** ((m - 69) / 12.0)
saw = lambda f: sig.sawtooth(2 * np.pi * f * t)
def lp(x, c, o=4): return sig.filtfilt(*sig.butter(o, np.clip(c, 30, SR/2-100)/(SR/2), "low"), x)
def hp(x, c, o=4): return sig.filtfilt(*sig.butter(o, c/(SR/2), "high"), x)


def reverb(x, decay=1.4, mix=0.25):
    L = int(decay * SR)
    ir = np.random.randn(L) * np.exp(-np.linspace(0, 7, L))
    ir = lp(ir, 5200); ir[:int(0.005 * SR)] = 0
    wet = sig.fftconvolve(x, ir)[:len(x)]
    return (1 - mix) * x + mix * wet / (np.max(np.abs(wet)) + 1e-9)


# ---- drums -----------------------------------------------------------------
# bar 0 sparse; bars 1-2 drop out (the fall lands in the silence); bar 3 on.
kick = np.zeros(N); kick_times = []
for bar in range(BARS):
    for b in range(4):
        if bar in (1, 2):            continue
        if bar == 0 and b % 2:       continue
        s = bar * BAR + b * BEAT
        kick_times.append(s)
        n = int(0.12 * SR)
        pitch = 145 * np.exp(-np.linspace(0, 34, n))
        body = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-np.linspace(0, 9, n))
        click = hp(np.random.randn(n), 2200) * np.exp(-np.linspace(0, 90, n)) * 0.30
        i0 = int(s * SR); m = min(n, N - i0)
        if m > 0: kick[i0:i0 + m] += body[:m] * 0.55 + click[:m]

clap = np.zeros(N)
for bar in range(3, BARS):
    for b in (1, 3):
        n = int(0.16 * SR)
        i0 = int((bar * BAR + b * BEAT) * SR); m = min(n, N - i0)
        if m > 0:
            clap[i0:i0 + m] += (np.random.randn(n) * np.exp(-np.linspace(0, 16, n)))[:m] * 0.5
clap = reverb(hp(clap, 1400), 0.5, 0.35)

hat = np.zeros(N)
for bar in range(3, BARS):
    for i in range(8):
        amp = (0.22 if i % 2 == 0 else 0.13) * (0.6 if bar < 5 else 1.0)
        n = int(0.05 * SR)
        i0 = int((bar * BAR + i * BEAT / 2) * SR); m = min(n, N - i0)
        if m > 0:
            hat[i0:i0 + m] += (np.random.randn(n) * np.exp(-np.linspace(0, 26, n)))[:m] * amp
hat = hp(hat, 7000)

# ---- harmony (A minor: Am / F / C / G) -------------------------------------
PROG = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
pad = np.zeros(N); bass = np.zeros(N)
for bar in range(BARS):
    ch = PROG[bar % 4]; s = bar * BAR
    e = env(s, BAR, a=0.35, d=0.2, s=0.85, r=0.5)
    for m in ch:
        f = note(m - 12)
        pad += sum(saw(f * (1 + dt)) for dt in (-0.004, 0, 0.004)) / 3 * e * 0.17
    root = note(ch[0] - 24)
    be = env(s, BAR, a=0.01, d=0.15, s=0.75, r=0.25)
    bass += (np.sin(2 * np.pi * root * t) * 0.22 + saw(root * 2) * 0.30) * be

cut = np.interp(t, [0, 4, 6, 17, 20, 32], [380, 500, 1500, 2200, 4200, 3000])
out = np.zeros(N); step = SR // 4
for i in range(0, N, step):
    j = min(i + step, N)
    out[i:j] = lp(pad[max(0, i - 2000):j], float(cut[i]))[-(j - i):]
pad = out
bass = lp(hp(bass, 55), 900)

# ---- arp (enters with the app section, doubles at the drop) ----------------
arp = np.zeros(N); PENT = [69, 72, 74, 76, 79, 81]
for bar in range(3, BARS):
    div = 4 if bar < 10 else 8
    for i in range(div):
        s = bar * BAR + i * (BAR / div)
        f = note(PENT[(bar * 3 + i) % len(PENT)])
        e = env(s, BAR / div, a=0.003, d=0.09, r=0.02)
        arp += (saw(f) * 0.5 + np.sin(2 * np.pi * f * t) * 0.5) * e * 0.30
arp = reverb(hp(lp(arp, 5000), 300), 1.1, 0.32)

# ---- transitions -----------------------------------------------------------
fx = np.zeros(N)

def riser(start, dur, peak=0.4):
    i0 = int(start * SR); n = min(int(dur * SR), N - i0)
    if n <= 0: return
    noise = np.random.randn(n); o = np.zeros(n); step = SR // 8
    for i in range(0, n, step):
        j = min(i + step, n)
        o[i:j] = hp(noise[max(0, i - 1500):j], 400 + 5500 * (i / n) ** 2)[-(j - i):]
    fx[i0:i0 + n] += o * np.linspace(0, 1, n) ** 2.2 * peak

def impact(start, amp=0.85):
    i0 = int(start * SR); n = min(int(1.3 * SR), N - i0)
    if n <= 0: return
    pitch = 95 * np.exp(-np.linspace(0, 5, n))
    boom = np.sin(2 * np.pi * np.cumsum(pitch) / SR) * np.exp(-np.linspace(0, 6, n))
    crash = hp(np.random.randn(n), 3500) * np.exp(-np.linspace(0, 9, n)) * 0.35
    fx[i0:i0 + n] += (boom + crash) * amp

def whoosh(center, dur=0.45, amp=0.28):
    i0 = int((center - dur / 2) * SR); n = min(int(dur * SR), N - max(i0, 0))
    if i0 < 0 or n <= 0: return
    noise = np.random.randn(n); o = np.zeros(n); step = SR // 16
    for i in range(0, n, step):
        j = min(i + step, n)
        o[i:j] = hp(noise[max(0, i - 1200):j], 600 + 4000 * np.sin(np.pi * i / n))[-(j - i):]
    fx[i0:i0 + n] += o * np.sin(np.pi * np.linspace(0, 1, n)) * amp

impact(2.00, 0.95)          # the fall
riser(4.00, 2.00, 0.42)     # under the beat card
impact(6.00, 0.50)          # groove enters
riser(17.00, 3.00, 0.62)    # build under the b-roll
impact(20.00, 1.00)         # THE SEND
impact(29.00, 0.50)         # end card
for c in (9.0, 13.0, 24.0):
    whoosh(c)

# ---- mix -------------------------------------------------------------------
duck = np.ones(N)
for s in kick_times:
    i0 = int(s * SR); n = min(int(0.34 * SR), N - i0)
    if n > 0:
        duck[i0:i0 + n] = np.minimum(duck[i0:i0 + n], 1 - 0.72 * np.exp(-np.linspace(0, 5, n)))

music = (kick + clap * 1.25 + hat * 1.15
         + (bass + pad * 1.5 + arp * 1.7) * duck + fx)
music *= np.interp(t, [0, 2, 4, 6, 17, 20, 29, 30.5, 32],
                      [0.30, 0.55, 0.40, 0.80, 0.85, 1.0, 1.0, 0.85, 0.0])
music = hp(music, 42)
music += sig.sosfilt(sig.butter(2, [900, 5200], btype='band', fs=SR, output='sos'), music) * 0.55
music = reverb(np.tanh(music * 1.35) * 0.86, 0.9, 0.10)
music /= np.max(np.abs(music)) + 1e-9

# ---- voiceover, ducking the music beneath it -------------------------------
vo = np.zeros(N)
spans = []
for k, at in VO_AT.items():
    x, _ = sf.read(f"{SC}/vo_{k}.wav")
    i0 = int(at * SR); n = min(len(x), N - i0)
    vo[i0:i0 + n] += x[:n]
    spans.append((at, at + n / SR))

vduck = np.ones(N)
for s, e in spans:
    i0, i1 = int((s - 0.25) * SR), int(min(e + 0.35, DUR) * SR)
    ramp = int(0.25 * SR)
    seg = np.full(i1 - i0, 0.34)
    seg[:ramp] = np.linspace(1, 0.34, ramp)
    seg[-ramp:] = np.linspace(0.34, 1, ramp)
    vduck[i0:i1] = np.minimum(vduck[i0:i1], seg)

master = music * 0.62 * vduck + vo * 0.95
master = np.tanh(master * 1.1)
master /= np.max(np.abs(master)) + 1e-9
master *= 0.92

sf.write(f"{SC}/master_audio.wav", np.stack([master, np.roll(master, 60)], 1), SR)
sf.write(f"{SC}/music_only.wav", np.stack([music, np.roll(music, 60)], 1), SR)
print(f"master_audio.wav {DUR}s | VO spans: " +
      ", ".join(f"{k} {s:.2f}-{e:.2f}" for k, (s, e) in zip(VO_AT, spans)))
