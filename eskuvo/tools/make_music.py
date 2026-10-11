#!/usr/bin/env python3
"""Saját, jogdíjmentes háttérzene: lágy zongoraszerű arpeggio és pad, ~2 perc, hézagmentesen ismételhető."""
import subprocess
import tempfile
import os
import numpy as np
from scipy.signal import fftconvolve
from scipy.io import wavfile

SR = 44100
BPM = 72
BEAT = 60 / BPM
rng = np.random.default_rng(10102026)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# F-dúr hangulat: Fmaj7, Am7, Dm9, Bbmaj9, Gm9, C6sus, Fmaj7/A, Bbmaj7
chords = [
    [53, 60, 64, 67, 69, 72], [57, 60, 64, 67, 71, 72],
    [50, 57, 60, 64, 65, 69], [46, 57, 60, 62, 65, 69],
    [43, 58, 62, 65, 69, 70], [48, 57, 60, 62, 67, 69],
    [45, 60, 64, 65, 69, 72], [46, 58, 62, 65, 69, 74],
]
BARS_PER_CHORD = 2
LOOPS = 2
total_bars = len(chords) * BARS_PER_CHORD * LOOPS
dur = total_bars * 4 * BEAT
N = int(dur * SR)
out = np.zeros((N, 2))


def piano(f, length, vel):
    t = np.arange(int(length * SR)) / SR
    env = np.exp(-t * (1.6 + f / 900)) * (1 - np.exp(-t * 300))
    tone = (np.sin(2 * np.pi * f * t)
            + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3)
            + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 5)
            + 0.05 * np.sin(2 * np.pi * 4.01 * f * t) * np.exp(-t * 7))
    return tone * env * vel


def pad(freqs, length):
    t = np.arange(int(length * SR)) / SR
    a = 1.2
    env = np.minimum(1, t / a) * np.minimum(1, (length - t) / a)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.12):
            s += np.sin(2 * np.pi * (f + det) * t + rng.random() * 6.28)
    return s * env / len(freqs)


def add(sig, start, pan=0.5):
    i = int(start * SR)
    j = min(N, i + len(sig))
    out[i:j, 0] += sig[: j - i] * (1 - pan)
    out[i:j, 1] += sig[: j - i] * pan


patterns = [[0, 2, 3, 4, 5, 4, 3, 2], [0, 3, 4, 5, 3, 4, 2, 4]]
bar = 0
for loop in range(LOOPS):
    for ci, ch in enumerate(chords):
        cstart = bar * 4 * BEAT
        clen = BARS_PER_CHORD * 4 * BEAT
        add(pad([hz(m) for m in ch[1:4]], clen + 1.0) * 0.07, cstart)
        add(piano(hz(ch[0] - 12), 5, 0.22), cstart, 0.45)
        add(piano(hz(ch[0]), 5, 0.12), cstart, 0.5)
        for b in range(BARS_PER_CHORD):
            pat = patterns[(ci + b) % 2]
            for k, idx in enumerate(pat):
                t0 = cstart + b * 4 * BEAT + k * BEAT / 2 + rng.normal(0, 0.008)
                vel = 0.13 * (1.0 if k % 2 == 0 else 0.75) * rng.uniform(0.85, 1.1)
                m = ch[idx]
                add(piano(hz(m), 3.5, vel), t0, 0.35 + 0.3 * (m - 55) / 25)
        # dallamhang minden második akkordon, második körben
        if loop == 1 and ci % 2 == 0:
            add(piano(hz(ch[-1] + 12), 4, 0.07), cstart + 2 * BEAT, 0.6)
        bar += BARS_PER_CHORD

# Egyszerű zengető: lecsengő zajimpulzus
ir_len = int(2.8 * SR)
t = np.arange(ir_len) / SR
ir = rng.normal(0, 1, (ir_len, 2)) * np.exp(-t * 2.4)[:, None]
ir[:, :] *= 0.04
wet = np.stack([fftconvolve(out[:, c], ir[:, c])[:N] for c in range(2)], axis=1)
# a farkat visszahajtjuk az elejére, így hézag nélkül ismételhető
tail = np.stack([fftconvolve(out[:, c], ir[:, c])[N:] for c in range(2)], axis=1)
wet[: len(tail)] += tail
mix = out * 0.8 + wet * 0.9
mix /= np.max(np.abs(mix)) * 1.12

WAV = os.path.join(tempfile.gettempdir(), "eskuvo_music.wav")
wavfile.write(WAV, SR, (mix * 32767).astype(np.int16))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", WAV,
                "-c:a", "libmp3lame", "-b:a", "160k", "assets/music.mp3"], check=True)
print(f"kész: {dur:.0f} mp")
