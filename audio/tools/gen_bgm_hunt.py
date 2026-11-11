"""bgm_hunt_loop.ogg — 《微光小圃》狩獵草原 BGM。

108 BPM、4/4、16 小節＝1,568,000 samples＝35.555… s（小節長度 98,000 samples，樣本精確）。
輕冒險但仍然溫暖：VCSL CC0 豎琴／鐘琴／高音直笛（經原創 SFZ map + pysfizz 渲染）
＋原創軟合成低音／輕打擊／空氣層。唔用 pedalboard（團規 GPL）。
無縫循環：尾巴 overlap-add 回開頭；空氣／shaker 用圓周 FFT；頭尾都落喺 C 大調。
目標：解碼後 ogg -16.0 LUFS integrated，true peak ≤ -1 dBTP，44.1 kHz 立體聲
ogg Vorbis -q:a 5、-fflags +bitexact。

VCSL 係第三方 CC0 樣本，只用嚟做樂器，唔當遊音原創素材發行；樂句、編曲、合成層同
SFZ map 係原創。SFX 完全唔用呢批樣本。

用法（喺 audio/）：
  PYTHONPATH=tools /workspace/audio-venv/bin/python tools/gen_bgm_hunt.py
"""
from __future__ import annotations
import os, re, subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from dsp import SR, mtof, place, adsr, tt, softsine, verb_ir
from pysfizz import Synth

FF = os.environ.get("FF", "ffmpeg")
ROOT = Path(__file__).resolve().parents[1]
MAPS = Path("/workspace/audio-libs/maps")

BPM = 108
BEAT = 60.0 / BPM          # 4000/9 s, exact with samples below
BAR_SAMP = 98000           # 4 beats * 44100 * 60 / 108
NBAR = 16
N = BAR_SAMP * NBAR        # 1_568_000
BAR = BAR_SAMP / SR
BEAT_S = BAR / 4.0
TAIL = int(6 * SR)

# C major / cozy-adventure progression, starts and ends on C for a clean fold.
# 4-bar phrases: establish, A, B (slightly more motion), turnaround back to C.
PROG = [
    "C", "C", "G", "C",
    "F", "C", "G", "C",
    "Am", "F", "G", "C",
    "F", "G", "C", "C",
]
# root, triad (midi)
CH = {
    "C":  (36, [48, 52, 55, 60]),
    "G":  (43, [47, 50, 55, 59]),
    "F":  (41, [45, 48, 53, 57]),
    "Am": (33, [45, 48, 52, 57]),
}

# Recorder melody, beats from the start of each 4-bar block (blocks at bars 4, 8, 12
# start at bar index 4/8/12). Notes in C pentatonic mostly, a little G major colour.
# (beat_offset, midi, duration_beats) relative to block start.
MEL_A = [  # bars 5–8 (block starts at bar 4)
    (0.0, 76, 2.0), (2.0, 79, 1.0), (3.0, 76, 1.0),
    (4.0, 74, 2.0), (6.0, 72, 2.0),
    (8.0, 79, 1.5), (9.5, 81, 0.5), (10.0, 79, 2.0),
    (12.0, 76, 2.0), (14.0, 74, 1.0), (15.0, 72, 1.0),
]
MEL_B = [  # bars 9–12
    (0.0, 81, 2.0), (2.0, 79, 1.0), (3.0, 76, 1.0),
    (4.0, 77, 2.0), (6.0, 76, 1.0), (7.0, 74, 1.0),
    (8.0, 72, 2.0), (10.0, 74, 2.0),
    (12.0, 76, 2.0), (14.0, 72, 2.0),
]
# Glock answers (sparse), beats from piece start.
GLOCK = [
    (4 * 4 + 1.5, 84, 0.2),
    (4 * 4 + 3.5, 79, 0.2),
    (6 * 4 + 1.5, 83, 0.2),
    (6 * 4 + 3.0, 84, 0.2),
    (9 * 4 + 2.0, 88, 0.2),
    (10 * 4 + 1.5, 84, 0.2),
    (11 * 4 + 3.0, 86, 0.2),
    (14 * 4 + 2.0, 84, 0.2),
    (15 * 4 + 3.0, 79, 0.2),
]


class Inst:
    def __init__(self, sfz: Path):
        self.s = Synth(sample_rate=SR, block_size=1024)
        ok = self.s.load_sfz_file(str(sfz), quiet=True)
        if not ok:
            raise RuntimeError(f"failed to load {sfz}")
        self.cache: dict = {}

    def note(self, pitch: int, vel: int, on: float, dur: float) -> np.ndarray:
        key = (int(pitch), int(vel), round(float(on), 4), round(float(dur), 4))
        if key not in self.cache:
            y = self.s.render_note(int(pitch), int(vel), float(on), float(dur))
            # (2, n) float, often very quiet — peak-normalise to 0.5
            pk = float(np.max(np.abs(y)) + 1e-12)
            y = (y / pk) * 0.5
            self.cache[key] = y.astype(np.float64)
        return self.cache[key]


def eq_pan(gain: float, pan: float):
    pan = max(-1.0, min(1.0, pan))
    th = (pan + 1) * np.pi / 4
    return gain * np.cos(th), gain * np.sin(th)


def put_mono(L, R, t, x, gain=1.0, pan=0.0):
    if t < 0:
        t += N / SR
    gl, gr = eq_pan(gain, pan)
    place(L, t, x, gl)
    place(R, t, x, gr)


def put_stereo(L, R, t, y2, gain=1.0, pan=0.0):
    """y2 shape (2, n) or (n,)."""
    if t < 0:
        t += N / SR
    if y2.ndim == 1:
        put_mono(L, R, t, y2, gain, pan)
        return
    gl, gr = eq_pan(gain, pan)
    # mild additional stereo from the sample itself
    place(L, t, y2[0], gl)
    place(R, t, y2[1], gr)


def bass_note(midi_n, d, a=0.012, r=0.18):
    f = float(mtof(midi_n))
    x = tt(d)
    y = 0.85 * np.sin(2 * np.pi * f * x)
    y += 0.22 * np.sin(2 * np.pi * f * 2 * x) * np.exp(-x * 4.0)
    y += 0.12 * np.sin(2 * np.pi * f * 1.004 * x)  # slight chorus
    # very soft triangle 3rd
    tri = 0.08 * (2 / np.pi) * np.arcsin(np.sin(2 * np.pi * f * x))
    y = y + tri
    return y * adsr(len(x), a, r, decay=1.6)


def soft_kick(d=0.32):
    x = tt(d)
    f = 86 * (42 / 86) ** np.clip(x / 0.08, 0, 1)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9.0)
    return y * adsr(len(x), 0.003, 0.08)


def wood_tick(rng, d=0.07):
    n = int(round(d * SR))
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * 980 * t) * np.exp(-t * 48)
    y += 0.4 * np.sin(2 * np.pi * 1560 * t) * np.exp(-t * 60)
    noise = rng.standard_normal(n)
    y += 0.15 * noise * np.exp(-t * 80)
    return y * adsr(n, 0.002, 0.03)


def shaker_loop(rng, n):
    """Circular 8th-note shaker bed, very light, LPF ~7.5 kHz."""
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    H = (1 / (1 + (1800 / np.maximum(f, 1e-9)) ** 2)) * (1 / (1 + (f / 7500) ** 6))
    y = np.fft.irfft(X * H, n)
    t = np.arange(n) / SR
    # 8 pulses per bar (eighth notes), 16 bars — integer cycles
    # pulse envelope: narrow bumps at each 8th
    eighth = BEAT_S / 2.0
    env = np.zeros(n)
    n_8 = int(round(NBAR * 8))
    for i in range(n_8):
        t0 = i * eighth
        # slightly accent 1 and 3 of each bar (i % 8 in 0, 4)
        acc = 1.0 if (i % 8) in (0, 4) else (0.7 if (i % 2 == 0) else 0.45)
        w = int(0.040 * SR)
        i0 = int(round(t0 * SR))
        if i0 >= n:
            continue
        e = np.exp(-np.arange(w) / SR * 70.0)
        sl = slice(i0, min(n, i0 + w))
        env[sl] += acc * e[: sl.stop - sl.start]
    y = y / (np.std(y) + 1e-12) * env
    return y


def circ_band(n, lo, hi, seed):
    r = np.random.default_rng(seed)
    x = r.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    H = (1 / (1 + (lo / np.maximum(f, 1e-9)) ** 2)) * (1 / (1 + (f / hi) ** 4))
    return np.fft.irfft(X * H, n)


def circ_verb(x, seed, wet=0.32, rt=2.6):
    r = np.random.default_rng(seed)
    ir = verb_ir(r, rt=rt, pre=0.022, damp=2800, length=min(rt * 1.5, 7))
    irp = np.zeros(len(x))
    irp[: min(len(ir), len(x))] = ir[: min(len(ir), len(x))]
    return (1 - wet * 0.5) * x + wet * np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(irp), len(x))


def fold(buf):
    y = buf[:N].copy()
    tl = buf[N:]
    y[: len(tl)] += tl
    return y


def meas(p):
    o = subprocess.run(
        [FF, "-hide_banner", "-nostats", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
    TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)[-1])
    return I, TP


def generate():
    rng = np.random.default_rng(20261111)
    L = np.zeros(N + TAIL)
    R = np.zeros(N + TAIL)

    print("loading VCSL instruments…")
    harp = Inst(MAPS / "concert_harp.sfz")
    glock = Inst(MAPS / "glockenspiel.sfz")
    rec = Inst(MAPS / "soprano_recorder.sfz")

    # --- Harp ostinato: 8th-note broken chords, mid register ---
    # pattern of chord-tone indices: 0,2,1,3,2,1,2,1 (up and back)
    pat = [0, 2, 1, 3, 2, 1, 2, 1]
    print("rendering harp…")
    for b, cname in enumerate(PROG):
        _root, notes = CH[cname]
        ns = [n + 12 for n in notes]  # one octave up from triad list
        for i, idx in enumerate(pat):
            if rng.random() < 0.08 and i not in (0, 4):
                continue
            t = b * BAR + i * BEAT_S / 1.0 * 0.5 + float(rng.normal(0, 0.004))
            # wait: i * (BEAT_S/2)
            t = b * BAR + i * (BEAT_S / 2.0) + float(rng.normal(0, 0.004))
            pitch = int(ns[idx % len(ns)])
            vel = 72 if i % 2 == 0 else 60
            if i == 0:
                vel = 80
            y = harp.note(pitch, vel, 0.18, 1.6)
            pan = -0.45 + 0.90 * (idx / 3)
            g = 0.22 * (1.15 if i == 0 else (0.85 if i % 2 else 1.0))
            put_stereo(L, R, t, y, g, pan)

    # --- Recorder melody on phrases 2 and 3 ---
    print("rendering recorder…")
    for block_bar, phrase in ((4, MEL_A), (8, MEL_B)):
        for bt, pitch, dur_bt in phrase:
            t = block_bar * BAR + bt * BEAT_S + float(rng.normal(0, 0.003))
            on = max(0.12, dur_bt * BEAT_S * 0.82)
            rend = on + 0.45
            y = rec.note(int(pitch), 78, on, rend)
            # gentle LPF already in sample; keep mid
            pan = float(rng.uniform(-0.18, 0.18))
            put_stereo(L, R, t, y, 0.28, pan)

    # --- Sparse glock answers ---
    print("rendering glock…")
    for bt, pitch, _ in GLOCK:
        t = bt * BEAT_S + float(rng.normal(0, 0.002))
        y = glock.note(int(pitch), 64, 0.06, 1.5)
        put_stereo(L, R, t, y, 0.16, float(rng.uniform(-0.35, 0.35)))

    # --- Soft synth bass ---
    print("bass + perc…")
    for b, cname in enumerate(PROG):
        root, _ = CH[cname]
        t0 = b * BAR
        put_mono(L, R, t0, bass_note(root, BAR * 0.95), 0.42, 0.0)
        put_mono(L, R, t0 + 2 * BEAT_S, bass_note(root + 7, BEAT_S * 1.6, r=0.22), 0.22, 0.0)

    # --- Soft kick on 1, light tick on 3; B-section also a very soft tick on 2 ---
    for b in range(NBAR):
        t0 = b * BAR
        put_mono(L, R, t0, soft_kick(), 0.22, 0.0)
        put_mono(L, R, t0 + 2 * BEAT_S, wood_tick(rng), 0.10, 0.15 if b % 2 == 0 else -0.15)
        if b >= 8 and b < 12:
            put_mono(L, R, t0 + BEAT_S, wood_tick(rng), 0.06, -0.25)

    # circular shaker + air
    sh = shaker_loop(np.random.default_rng(11), N)
    air_l = circ_band(N, 200, 1600, 21)
    air_r = circ_band(N, 200, 1600, 22)
    air_l /= np.std(air_l) + 1e-12
    air_r /= np.std(air_r) + 1e-12
    tN = np.arange(N) / SR
    # 8 cycles over the loop (integer) so LFO meets
    lfo_l = 0.6 + 0.4 * np.sin(2 * np.pi * 8 * tN / (N / SR))
    lfo_r = 0.6 + 0.4 * np.sin(2 * np.pi * 8 * tN / (N / SR) + 1.1)
    L[:N] += 0.045 * sh
    R[:N] += 0.045 * sh * 0.92
    L[:N] += 0.010 * air_l * lfo_l
    R[:N] += 0.010 * air_r * lfo_r

    dry_l, dry_r = fold(L), fold(R)
    y = np.stack([circ_verb(dry_l, 31, wet=0.30, rt=2.4),
                  circ_verb(dry_r, 32, wet=0.30, rt=2.4)], axis=1)

    # circular HPF 35 Hz, gentle LPF 10 kHz (keep air, avoid harsh)
    Y = np.fft.rfft(y, axis=0)
    f = np.fft.rfftfreq(N, 1 / SR)
    H = (1 / (1 + (35 / np.maximum(f, 1e-9)) ** 4)) * (1 / (1 + (f / 10000) ** 6))
    Y *= H[:, None]
    y = np.fft.irfft(Y, N, axis=0)

    # C0 seam: spread the wrap jump over 10 ms at the end so |y[0]-y[-1]|
    # stays on the order of a single adjacent sample (QA vs p99.9).
    k = int(0.010 * SR)
    delta = y[0] - y[-1]
    ramp = np.arange(1, k + 1) / float(k + 1)  # ~0→1, last sample almost closes the gap
    y[-k:] += delta * ramp[:, None]

    out_dir = ROOT / "bgm"
    tmp = ROOT / "tmp_bgm_hunt"
    out_dir.mkdir(exist_ok=True)
    tmp.mkdir(exist_ok=True)
    wav = tmp / "bgm_hunt.wav"
    ogg = out_dir / "bgm_hunt_loop.ogg"

    def enc(g):
        sf.write(str(wav), y * g, SR, subtype="FLOAT")
        subprocess.run(
            [FF, "-y", "-v", "error", "-i", str(wav),
             "-ac", "2", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "5",
             "-fflags", "+bitexact", "-flags:a", "+bitexact", str(ogg)],
            check=True,
        )
        return meas(str(ogg))

    # start from a conservative gain
    pk = float(np.max(np.abs(y)) + 1e-12)
    g = 0.12 / pk
    I = TP = 0.0
    for _ in range(8):
        I, TP = enc(g)
        if TP > -1.2:
            g *= 10 ** ((-1.5 - TP) / 20)
            continue
        if abs(I + 16) < 0.12:
            break
        g *= 10 ** ((-16 - I) / 20)
    # final safety if last bump overshoot peak
    if TP > -1.05:
        g *= 10 ** ((-1.5 - TP) / 20)
        I, TP = enc(g)

    # numeric seam on decoded ogg
    x, sr = sf.read(str(ogg))
    seam = np.abs(x[0] - x[-1])
    d = np.abs(np.diff(x, axis=0))
    p999 = np.percentile(d, 99.9, axis=0)
    print(
        f"bgm_hunt_loop  samples={len(x)}  {len(x)/sr:.6f}s  bars={len(x)/sr/BAR:.3f}  "
        f"I={I:.2f} LUFS  TP={TP:.2f} dBTP  "
        f"seam={seam[0]:.5f},{seam[1]:.5f}  p99.9={p999[0]:.5f},{p999[1]:.5f}"
    )
    # cleanup wav only
    try:
        wav.unlink()
        tmp.rmdir()
    except OSError:
        pass
    return ogg, I, TP


if __name__ == "__main__":
    os.chdir(ROOT)
    generate()
    print("bgm_hunt_loop generated")
