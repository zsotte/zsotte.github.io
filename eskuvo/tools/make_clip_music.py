#!/usr/bin/env python3
"""Saját, jogdíjmentes, pörgős alap a vágott videóhoz: 120 BPM, 80 ütés (40 mp)."""
import sys
import numpy as np
from scipy.io import wavfile

SR = 48000
BPM = 120
B = 60 / BPM
BEATS = 80
TAIL = 1.5
N = int((BEATS * B + TAIL) * SR)
out = np.zeros((N, 2))
rng = np.random.default_rng(1010)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def add(sig, t, pan=0.5, gain=1.0):
    i = int(t * SR)
    j = min(N, i + len(sig))
    if j <= i:
        return
    out[i:j, 0] += sig[: j - i] * (1 - pan) * gain
    out[i:j, 1] += sig[: j - i] * pan * gain


def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 50 + 120 * np.exp(-t * 35)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def clap():
    t = np.arange(int(0.22 * SR)) / SR
    n = rng.normal(0, 1, len(t))
    env = np.exp(-t * 22) + 0.6 * np.exp(-((t - 0.012) * 300) ** 2)
    hp = np.diff(n, prepend=0)
    return hp * env * 0.45


def hat(open_=False):
    t = np.arange(int((0.18 if open_ else 0.05) * SR)) / SR
    n = np.diff(rng.normal(0, 1, len(t)), prepend=0)
    return n * np.exp(-t * (18 if open_ else 80)) * 0.18


def pluck(f, length=0.45, bright=1.0):
    t = np.arange(int(length * SR)) / SR
    s = sum((0.6 ** k) * np.sin(2 * np.pi * f * (k + 1) * t) * np.exp(-t * (6 + 4 * k / bright)) for k in range(5))
    return s * (1 - np.exp(-t * 400))


def bass(f, length):
    t = np.arange(int(length * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    env = np.minimum(1, t * 200) * np.minimum(1, (length - t) * 60)
    return s * env


def pad(freqs, length):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(1, t / 0.4) * np.minimum(1, (length - t) / 0.4)
    s = sum(np.sin(2 * np.pi * (f + d) * t) for f in freqs for d in (-0.4, 0.4))
    return s * env / (2 * len(freqs))


def riser(length):
    t = np.arange(int(length * SR)) / SR
    n = np.diff(rng.normal(0, 1, len(t)), prepend=0)
    return n * (t / length) ** 2 * 0.25


# F - C - Dm - Bb, 2 ütem (8 ütés) akkordonként
prog = [(53, [65, 69, 72, 76]), (48, [64, 67, 72, 76]), (50, [65, 69, 72, 74]), (46, [65, 70, 74, 77])]

DROP = 24          # itt indul a lassított szirmos rész
BREAK_END = 36     # utána teljes lendület
for b in range(BEATS):
    t = b * B
    root, chord = prog[(b // 8) % 4]
    in_break = DROP <= b < BREAK_END
    intro = b < 8
    # dob
    if not in_break and b < BEATS - 8:
        add(kick(), t, gain=0.0 if intro and b % 2 else 0.9)
        if b % 2 == 1 and not intro:
            add(clap(), t, 0.5, 0.9)
        add(hat(), t + B / 2, 0.6)
        if not intro:
            add(hat(), t + B / 4, 0.4, 0.5)
            add(hat(), t + 3 * B / 4, 0.4, 0.5)
    if b == DROP - 4:
        add(riser(4 * B), t)
    # basszus nyolcadokban
    if not in_break and b < BEATS - 8:
        for k in range(2):
            add(bass(hz(root - 12), B / 2 * 0.9), t + k * B / 2, 0.5, 0.35 if not intro else 0.0)
    # pluck arpeggio tizenhatodokban
    pattern = [0, 2, 1, 3]
    for k in range(4):
        if in_break and k % 2:
            continue
        note = chord[pattern[(b * 4 + k) % 4]] + (12 if (b // 4) % 2 and not intro else 0)
        add(pluck(hz(note), 0.4, 1.4), t + k * B / 4, 0.3 + 0.4 * (k % 2), 0.12)
    # pad akkordváltáskor
    if b % 8 == 0:
        add(pad([hz(m) for m in chord[:3]], 8 * B), t, 0.5, 0.25 if in_break else 0.12)

# zárás: egy nagy akkord kicsengéssel
end = (BEATS - 8) * B
add(kick(), end, gain=0.9)
for m in [41, 53, 65, 69, 72, 77]:
    add(pluck(hz(m), 3.5, 0.6), end, 0.5, 0.2)
add(pad([hz(65), hz(69), hz(72)], 8 * B + TAIL), end, 0.5, 0.25)

# egyszerű visszhang és összegzés
d = int(B * 0.75 * SR)
echo = np.zeros_like(out)
echo[d:] = out[:-d] * 0.22
mix = out + echo[:, ::-1]
mix = np.tanh(mix * 1.3)
mix /= np.max(np.abs(mix)) * 1.05
fade = int(1.2 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print(f"{len(mix)/SR:.1f} mp")
