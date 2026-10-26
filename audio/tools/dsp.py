"""Shared DSP helpers (numpy/scipy). 100% procedural, no samples."""
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve
SR = 44100
def mtof(m): return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)
def tt(d): return np.arange(int(round(SR * d))) / SR
def adsr(n, a=0.005, r=0.05, decay=0.0):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, min(n, int(r * SR)))
    e[:na] *= np.linspace(0, 1, na)[:n]; e[-nr:] *= np.linspace(1, 0, nr)
    if decay: e = e * np.exp(-np.arange(n) / SR * decay)
    return e
def bell(f, d, decay=6.0, a=0.003, r=0.04, bright=1.0, detune=0.0):
    """Soft celesta / music-box tone: a few slightly inharmonic partials, higher ones die faster."""
    x = tt(d); y = np.zeros(len(x))
    for ratio, amp, dk in [(1, 1.0, 1.0), (2.0, 0.35, 1.8), (3.01, 0.12, 2.6), (5.4, 0.08 * bright, 4.0)]:
        y += amp * np.sin(2 * np.pi * f * ratio * (1 + detune) * x) * np.exp(-x * decay * dk * 0.35)
    return y * adsr(len(x), a, r, decay * 0.35)
def pluck(f, d, decay=3.0, a=0.002, r=0.05):
    """Harp-like pluck: additive harmonics with 1/n rolloff and faster decay of overtones."""
    x = tt(d); y = np.zeros(len(x))
    for h in range(1, 7):
        y += (1.0 / h ** 1.3) * np.sin(2 * np.pi * f * h * x) * np.exp(-x * decay * (1 + 0.8 * (h - 1)))
    return y * adsr(len(x), a, r)
def softsine(f, d, a=0.01, r=0.1, decay=0.0, harm=(1,), amps=(1,)):
    x = tt(d); y = sum(A * np.sin(2 * np.pi * f * h * x) for h, A in zip(harm, amps))
    return y * adsr(len(x), a, r, decay)
def glide(f0, f1, d, a=0.005, r=0.05, decay=0.0, vib=0.0, vibf=6.0):
    x = tt(d); f = f0 * (f1 / f0) ** (x / d) * (1 + vib * np.sin(2 * np.pi * vibf * x))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * adsr(len(x), a, r, decay)
def bandnoise(rng, d, lo, hi, order=2):
    n = rng.standard_normal(int(round(SR * d)))
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, n)
def place(buf, start, x, gain=1.0):
    i = int(round(start * SR))
    if i >= len(buf): return
    n = min(len(x), len(buf) - i); buf[i:i + n] += gain * x[:n]
def verb_ir(rng, rt=1.0, pre=0.01, damp=3500, length=None):
    L = int((length or rt * 1.6) * SR); t = np.arange(L) / SR
    ir = rng.standard_normal(L) * np.exp(-t * 6.9 / rt)
    b, a = butter(1, damp / (SR / 2)); ir = lfilter(b, a, ir)
    ir = np.concatenate([np.zeros(int(pre * SR)), ir]); return ir / np.sqrt(np.sum(ir ** 2))
def verb(x, rng, wet=0.25, rt=0.6, tail=0.5):
    """Linear (non-circular) reverb for one-shots; extends the clip by `tail` seconds."""
    ir = verb_ir(rng, rt); y = fftconvolve(np.concatenate([x, np.zeros(int(tail * SR))]), ir)[:len(x) + int(tail * SR)]
    xp = np.concatenate([x, np.zeros(int(tail * SR))]); return (1 - wet) * xp + wet * y * 1.0
