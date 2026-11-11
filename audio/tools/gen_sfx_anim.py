"""《微光小圃》寵物／訪客／小動物動作音（anim_timing 對拍）。

讀 art-pet/anim_timing.json，為每個要新做嘅 hook 合成原創音效：
每個檔嘅 accent（land／peak／release）放喺 0 ms（hook 喺 clip 嘅 t_ms 觸發即播）。
如現有檔（例如 sfx_pet_yawn）本身有吸氣前導，唔改檔，只喺 anim_sfx_map.json 寫 preroll_ms。

風格同 tools/gen_sfx_life.py：加法／濾波噪音程式合成，無取樣。
4.2 kHz 二階低通、檔頭 10 ms 餘弦淡入、檔尾 40 ms 淡出＋10 ms 靜音、峰值上限 -6 dBFS、
純增益迭代到 LUFS20。ogg Vorbis 44.1 kHz 單聲道 -q:a 3 -fflags +bitexact。

用法（喺 audio/）：
  PYTHONPATH=tools /workspace/audio-venv/bin/python tools/gen_sfx_anim.py \\
      [--timing /tmp/anim-timing/art-pet/anim_timing.json]
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, zlib
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from dsp import SR, bandnoise, place, tt
from measure import ebur

FF = os.environ.get("FF", "ffmpeg")
ROOT = Path(__file__).resolve().parents[1]  # audio/
TMP = ROOT / "tmp_anim"
SFX = ROOT / "sfx"
CEIL = 10 ** (-6 / 20)
LP = butter(2, 4200 / (SR / 2), output="sos")


def rng_for(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode("utf-8")) & 0xFFFFFFFF)


def seq(parts):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts)
    y = np.zeros(L)
    for s, p, *g in parts:
        place(y, s, p, g[0] if g else 1.0)
    return y


def renv(n, a, r):
    e = np.ones(n)
    na = max(1, min(n, int(round(a * SR))))
    nr = max(1, min(n, int(round(r * SR))))
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    e[-nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e


def puff(rng, d, lo, hi, a=0.01, r=0.05, g=0.3):
    x = bandnoise(rng, d, lo, hi)
    return g * x / (np.max(np.abs(x)) + 1e-12) * renv(len(x), a, r)


def thump(f0, f1, d, decay, a=0.008, g=1.0, h2=0.25, body=0.0):
    x = tt(d)
    f = f0 * (f1 / f0) ** (x / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return g * (np.sin(ph) + h2 * np.sin(2 * ph) + body * np.sin(3.7 * ph)) * np.exp(-x * decay) * renv(len(x), a, 0.02)


def sine_glide(f0, f1, d, a=0.008, r=0.04, decay=12.0, g=1.0, h2=0.2):
    x = tt(d)
    f = f0 * (f1 / f0) ** (x / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + h2 * np.sin(2 * ph)) * np.exp(-x * decay)
    return g * y * renv(len(y), a, r)


def softbell(f, d, decay=8.0, g=1.0, a=0.004):
    x = tt(d)
    y = np.zeros(len(x))
    for ratio, amp, dk in ((1.0, 1.0, 1.0), (2.0, 0.28, 1.8), (2.76, 0.10, 2.8), (4.0, 0.05, 3.6)):
        if f * ratio > 4200:
            continue
        y += amp * np.sin(2 * np.pi * f * ratio * x) * np.exp(-x * decay * dk * 0.35)
    return g * y * renv(len(y), a, 0.06)


# ---------------------------------------------------------------------------
# builders：accent 喺 0 ms（淡入 10 ms 之後約 8–18 ms 到能量峰）
# ---------------------------------------------------------------------------
def build_grass_rustle(name, var):
    rng = rng_for(name)
    lo, hi = (1100, 3200) if var == "a" else (900, 2800)
    n = 8 if var == "a" else 7
    ticks = []
    for i in range(n):
        t = 0.004 + i * (0.022 if var == "a" else 0.026)
        g = 0.85 * (0.72 ** i)   # 最密最響喺開頭（accent 0）
        ticks.append((t, puff(rng, rng.uniform(0.016, 0.032), lo * rng.uniform(0.85, 1.1), hi, 0.003, 0.018, g)))
    return seq(
        [
            (0.0, thump(200 if var == "a" else 180, 120 if var == "a" else 110, 0.11, 22, a=0.006, g=1.0, h2=0.4, body=0.35)),
            (0.0, puff(rng, 0.10, 250, 1100, 0.006, 0.07, 0.55)),
            (0.0, puff(rng, 0.18, lo, hi, 0.005, 0.12, 0.55)),
            *ticks,
        ]
    )


def build_jump(name, var):
    rng = rng_for(name)
    f0, f1 = (200, 115) if var == "a" else (185, 105)
    up0, up1 = (280, 520) if var == "a" else (260, 480)
    return seq(
        [
            (0.0, thump(f0, f1, 0.11, 28, a=0.006, g=1.0, h2=0.35, body=0.3)),
            (0.004, puff(rng, 0.05, 400, 1800, 0.004, 0.03, 0.22)),
            (0.01, sine_glide(up0, up1, 0.12, a=0.008, r=0.05, decay=22, g=0.22, h2=0.15)),
        ]
    )


def build_step_walk(name, var):
    rng = rng_for(name)
    f0, f1 = (185, 115) if var == "a" else (170, 105)
    return seq(
        [
            (0.0, thump(f0, f1, 0.13, 26, a=0.007, g=1.0, h2=0.4, body=0.35)),
            (0.004, puff(rng, 0.05, 350, 1400, 0.005, 0.035, 0.28)),
            (0.012, puff(rng, 0.07, 1200, 2800, 0.008, 0.045, 0.08)),
        ]
    )


def build_letter_drop(name, var):
    rng = rng_for(name)
    tick_f = 920 if var == "a" else 840
    return seq(
        [
            (0.0, puff(rng, 0.09, 800, 2800, 0.004, 0.06, 0.55)),
            (0.0, sine_glide(tick_f, tick_f * 0.72, 0.07, a=0.002, r=0.04, decay=28, g=0.45, h2=0.35)),
            (0.012, thump(240, 150, 0.08, 30, a=0.005, g=0.35, body=0.2)),
            (0.04, puff(rng, 0.12, 600, 2200, 0.01, 0.08, 0.25)),
        ]
    )


def build_clap(name, var):
    rng = rng_for(name)
    f = 280 if var == "a" else 250
    parts = [
        (0.0, puff(rng, 0.028, 500, 2400, 0.002, 0.02, 0.7)),
        (0.0, thump(f, f * 0.62, 0.08, 28, a=0.003, g=0.85, h2=0.4, body=0.35)),
        (0.01, sine_glide(f * 0.9, f * 0.55, 0.10, a=0.006, r=0.06, decay=16, g=0.28, h2=0.25)),
    ]
    if var == "b":
        parts += [
            (0.055, puff(rng, 0.022, 600, 2600, 0.002, 0.016, 0.4)),
            (0.055, thump(f * 1.1, f * 0.7, 0.055, 40, a=0.003, g=0.4, body=0.25)),
        ]
    return seq(parts)


def build_pickup(name, var):
    rng = rng_for(name)
    f = 340 if var == "a" else 300
    return seq(
        [
            (0.0, thump(f, f * 0.7, 0.07, 32, a=0.005, g=0.45, body=0.2)),
            (0.0, puff(rng, 0.08, 900, 2800, 0.004, 0.05, 0.55)),
            (0.03, sine_glide(420 if var == "a" else 390, 520 if var == "a" else 480, 0.1, a=0.008, r=0.05, decay=18, g=0.2)),
            (0.02, puff(rng, 0.12, 700, 2200, 0.01, 0.08, 0.22)),
        ]
    )


def build_place(name, var):
    rng = rng_for(name)
    f0, f1 = (200, 120) if var == "a" else (185, 110)
    return seq(
        [
            (0.0, thump(f0, f1, 0.1, 28, a=0.006, g=0.8, body=0.3)),
            (0.0, puff(rng, 0.07, 700, 2400, 0.004, 0.045, 0.5)),
            (0.025, puff(rng, 0.1, 500, 1800, 0.01, 0.07, 0.22)),
        ]
    )


def build_reach(name, var):
    rng = rng_for(name)
    f0, f1 = (220, 280) if var == "a" else (200, 255)
    return seq(
        [
            (0.0, sine_glide(f0, f1, 0.09, a=0.006, r=0.05, decay=18, g=0.5, h2=0.2)),
            (0.0, puff(rng, 0.10, 250, 1200, 0.006, 0.07, 0.45)),
            (0.0, thump(170, 125, 0.10, 20, a=0.008, g=0.55, h2=0.35, body=0.4)),
        ]
    )


def build_stretch(name, var):
    rng = rng_for(name)
    f0, f1 = (210, 140) if var == "a" else (195, 130)
    # 較長中頻身（低 peak、夠 RMS）令 LUFS20 去到 -20，能量峰仍喺開頭
    return seq(
        [
            (0.0, sine_glide(f0 * 1.05, f0 * 0.95, 0.22, a=0.008, r=0.12, decay=5, g=0.9, h2=0.4)),
            (0.0, thump(f0, f1, 0.28, 8, a=0.01, g=0.55, h2=0.5, body=0.5)),
            (0.0, puff(rng, 0.20, 200, 800, 0.01, 0.14, 0.32)),
            (0.18, sine_glide(f1 * 1.05, f1 * 0.8, 0.18, a=0.03, r=0.1, decay=9, g=0.22)),
        ]
    )


def build_proud(name, var):
    rng = rng_for(name)
    f0, f1 = (190, 130) if var == "a" else (175, 120)
    return seq(
        [
            (0.0, thump(f0, f1, 0.16, 14, a=0.008, g=0.85, h2=0.45, body=0.45)),
            (0.0, sine_glide(f0, f1, 0.16, a=0.01, r=0.08, decay=8, g=0.45, h2=0.3)),
            (0.0, puff(rng, 0.08, 300, 1100, 0.006, 0.05, 0.32)),
            (0.025, sine_glide(420 if var == "a" else 390, 360 if var == "a" else 330, 0.08, a=0.008, r=0.05, decay=18, g=0.14)),
        ]
    )


def build_point(name, var):
    rng = rng_for(name)
    f0, f1 = (320, 480) if var == "a" else (300, 450)
    return seq(
        [
            (0.0, sine_glide(f0, f1, 0.09, a=0.006, r=0.05, decay=20, g=0.35, h2=0.12)),
            (0.0, puff(rng, 0.08, 400, 1600, 0.006, 0.05, 0.35)),
            (0.012, thump(240, 170, 0.07, 30, a=0.005, g=0.4, body=0.2)),
            (0.03, sine_glide(880 if var == "a" else 820, 700, 0.06, a=0.003, r=0.04, decay=32, g=0.16, h2=0.2)),
        ]
    )


def build_startle(name, var):
    rng = rng_for(name)
    f0, f1 = (260, 150) if var == "a" else (240, 140)
    return seq(
        [
            (0.0, thump(f0, f1, 0.08, 36, a=0.004, g=1.0, h2=0.3, body=0.25)),
            (0.0, puff(rng, 0.04, 600, 2200, 0.003, 0.028, 0.4)),
            (0.015, sine_glide(400 if var == "a" else 370, 280, 0.07, a=0.006, r=0.04, decay=24, g=0.2)),
        ]
    )


def build_shake(name, var):
    rng = rng_for(name)
    rate = 18 if var == "a" else 15
    n = 3 if var == "a" else 3
    f = 220 if var == "a" else 200
    parts = []
    for i in range(n):
        t = i / rate
        g = 1.0 if i == 0 else 0.7 - 0.15 * i
        parts.append((t, thump(f * (1 + 0.06 * (i % 2)), f * 0.75, 0.05, 36, a=0.004, g=g, body=0.2)))
        parts.append((t, puff(rng, 0.035, 500, 2000, 0.003, 0.022, 0.28 * g)))
    return seq(parts)


def build_transform(name, var):
    rng = rng_for(name)
    f = 523.25 if var == "a" else 392.0  # C5 / G4
    f2 = 659.25 if var == "a" else 523.25
    return seq(
        [
            (0.0, softbell(f, 0.38, decay=7.0, g=0.85, a=0.005)),
            (0.0, softbell(f2, 0.32, decay=8.5, g=0.4, a=0.006)),
            (0.0, puff(rng, 0.12, 400, 1800, 0.008, 0.08, 0.22)),
            (0.0, sine_glide(180, 260, 0.16, a=0.01, r=0.08, decay=10, g=0.28, h2=0.3)),
            (0.08, softbell(f * 1.5 if f * 1.5 < 4000 else f, 0.22, decay=12, g=0.18, a=0.008)),
        ]
    )


def build_roll(name, var):
    rng = rng_for(name)
    f0 = 210 if var == "a" else 190
    tocks = []
    for i, dt in enumerate((0.0, 0.055, 0.12, 0.19)):
        g = 1.0 * (0.7 ** i)
        tocks.append((dt, thump(f0 * (1.0 - 0.08 * i), f0 * 0.7, 0.06, 30, a=0.004, g=g, body=0.25)))
        tocks.append((dt, puff(rng, 0.04, 400, 1600, 0.003, 0.025, 0.22 * g)))
    return seq(tocks + [(0.02, puff(rng, 0.22, 200, 900, 0.02, 0.14, 0.22))])


def build_offer_letter(name, var="a"):
    rng = rng_for(name)
    return seq(
        [
            (0.0, puff(rng, 0.12, 700, 2600, 0.006, 0.08, 0.6)),
            (0.0, sine_glide(180, 150, 0.14, a=0.01, r=0.08, decay=12, g=0.35, h2=0.25)),
            (0.02, puff(rng, 0.14, 500, 2000, 0.015, 0.1, 0.25)),
            (0.04, sine_glide(740, 620, 0.08, a=0.004, r=0.05, decay=22, g=0.16, h2=0.2)),
        ]
    )


def build_offer_seed(name, var="a"):
    rng = rng_for(name)
    return seq(
        [
            (0.0, thump(240, 160, 0.09, 26, a=0.006, g=0.5, body=0.3)),
            (0.0, puff(rng, 0.08, 500, 1800, 0.005, 0.055, 0.4)),
            (0.015, sine_glide(560, 420, 0.1, a=0.005, r=0.06, decay=18, g=0.28, h2=0.2)),
            (0.04, puff(rng, 0.1, 800, 2400, 0.01, 0.07, 0.18)),
        ]
    )


def build_nod(name, var):
    rng = rng_for(name)
    f0, f1 = (170, 110) if var == "a" else (160, 100)
    return seq(
        [
            (0.0, thump(f0, f1, 0.11, 22, a=0.007, g=1.0, h2=0.45, body=0.4)),
            (0.0, puff(rng, 0.05, 300, 1100, 0.006, 0.035, 0.28)),
        ]
    )


def build_rattle(name, var):
    rng = rng_for(name)
    n = 5 if var == "a" else 4
    base = 620 if var == "a" else 560
    parts = [(0.0, sine_glide(200, 180, 0.1, a=0.008, r=0.06, decay=14, g=0.3, h2=0.3))]
    for i in range(n):
        t = (0.0 if i == 0 else rng.uniform(0.01, 0.12))
        f = base * rng.uniform(0.9, 1.15)
        parts.append((t, sine_glide(f, f * 0.85, 0.04, a=0.002, r=0.025, decay=40, g=rng.uniform(0.25, 0.55), h2=0.25)))
        parts.append((t, puff(rng, 0.025, 1200, 3200, 0.002, 0.016, rng.uniform(0.15, 0.35))))
    return seq(parts)


# (filename without .ogg, target LUFS20, builder, variant)
NEW = [
    ("sfx_pet_grass_rustle_a", -22.0, build_grass_rustle, "a"),
    ("sfx_pet_grass_rustle_b", -22.0, build_grass_rustle, "b"),
    ("sfx_pet_jump_a", -22.0, build_jump, "a"),
    ("sfx_pet_jump_b", -22.0, build_jump, "b"),
    ("sfx_pet_step_walk_a", -22.0, build_step_walk, "a"),
    ("sfx_pet_step_walk_b", -22.0, build_step_walk, "b"),
    ("sfx_pet_letter_drop_a", -22.0, build_letter_drop, "a"),
    ("sfx_pet_letter_drop_b", -22.0, build_letter_drop, "b"),
    ("sfx_pet_clap_a", -22.0, build_clap, "a"),
    ("sfx_pet_clap_b", -22.0, build_clap, "b"),
    ("sfx_pet_pickup_a", -22.0, build_pickup, "a"),
    ("sfx_pet_pickup_b", -22.0, build_pickup, "b"),
    ("sfx_pet_place_a", -22.0, build_place, "a"),
    ("sfx_pet_place_b", -22.0, build_place, "b"),
    ("sfx_pet_reach_a", -22.0, build_reach, "a"),
    ("sfx_pet_reach_b", -22.0, build_reach, "b"),
    ("sfx_pet_stretch_a", -20.0, build_stretch, "a"),
    ("sfx_pet_stretch_b", -20.0, build_stretch, "b"),
    ("sfx_pet_proud_a", -20.0, build_proud, "a"),
    ("sfx_pet_proud_b", -20.0, build_proud, "b"),
    ("sfx_pet_point_a", -22.0, build_point, "a"),
    ("sfx_pet_point_b", -22.0, build_point, "b"),
    ("sfx_critter_startle_a", -20.0, build_startle, "a"),
    ("sfx_critter_startle_b", -20.0, build_startle, "b"),
    ("sfx_critter_shake_a", -22.0, build_shake, "a"),
    ("sfx_critter_shake_b", -22.0, build_shake, "b"),
    ("sfx_critter_transform_a", -20.0, build_transform, "a"),
    ("sfx_critter_transform_b", -20.0, build_transform, "b"),
    ("sfx_critter_roll_a", -22.0, build_roll, "a"),
    ("sfx_critter_roll_b", -22.0, build_roll, "b"),
    ("sfx_visitor_offer_letter", -22.0, build_offer_letter, "a"),
    ("sfx_visitor_offer_seed", -22.0, build_offer_seed, "a"),
    ("sfx_visitor_nod_a", -22.0, build_nod, "a"),
    ("sfx_visitor_nod_b", -22.0, build_nod, "b"),
    ("sfx_visitor_rattle_a", -22.0, build_rattle, "a"),
    ("sfx_visitor_rattle_b", -22.0, build_rattle, "b"),
]

TGT = {k: t for k, t, *_ in NEW}


def lufs20(path):
    x, sr = sf.read(path)
    tmp = "/tmp/_anim_l20.wav"
    sf.write(tmp, np.tile(x, 20), sr, subtype="FLOAT")
    return ebur(tmp)[0]


def enc(x, k):
    wav = TMP / f"{k}.wav"
    ogg = SFX / f"{k}.ogg"
    sf.write(str(wav), x, SR, subtype="FLOAT")
    subprocess.run(
        [FF, "-y", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "44100",
         "-c:a", "libvorbis", "-q:a", "3", "-fflags", "+bitexact", "-flags:a", "+bitexact",
         str(ogg)],
        check=True,
    )


def post(v):
    v = sosfiltfilt(LP, v - np.mean(v))
    na = int(0.010 * SR)
    v[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nf = int(0.04 * SR)
    v[-nf:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf)
    v = np.concatenate([v, np.zeros(int(0.01 * SR))])
    return v


def render_one(k, tgt, builder, var):
    v = post(builder(k, var))
    v = v / (np.max(np.abs(v)) + 1e-12) * 0.25
    g = 0.0
    L = -99.0
    for _ in range(7):
        y = v * 10 ** (g / 20)
        if np.max(np.abs(y)) > CEIL:
            y = y / np.max(np.abs(y)) * CEIL
        enc(y, k)
        x, _ = sf.read(str(SFX / f"{k}.ogg"))
        if np.max(np.abs(x)) > CEIL * 1.02:
            g -= 20 * np.log10(np.max(np.abs(x)) / CEIL) + 0.1
            continue
        L = lufs20(str(SFX / f"{k}.ogg"))
        if abs(L - tgt) <= 0.15 or (L < tgt and np.max(np.abs(y)) >= CEIL * 0.999):
            break
        g += tgt - L
    return L, len(sf.read(str(SFX / f"{k}.ogg"))[0]) / SR


# ---------------------------------------------------------------------------
# mapping（36 個 null 點＋6 個已有 hook；hop_peak 建議靜音）
# ---------------------------------------------------------------------------
SIZE_PITCH = {"S": 1.12, "M": 1.0, "L": 0.88}

# (clip_id, event_index_or_id+t_ms to disambiguate duplicate ids) filled from json
# Static assignment keyed by (clip, event_id, t_ms)

def files_of(*stems):
    return [s + ".ogg" for s in stems]


ASSIGN = {
    # already hooked by 遊美
    ("pounce", "land", 500): dict(
        sfx_hook="sfx_pet_step_hop_a",
        files=["sfx_pet_step_hop_a.ogg", "sfx_pet_step_hop_b.ogg"],
        kind="foley", source="existing", preroll_ms=0, accent_offset_ms=12,
        note="已有 hook。落地；a/b 交替。現有檔能量峰約 11–12 ms（10 ms 淡入）。",
    ),
    ("cheer", "cheer_peak", 200): dict(
        sfx_hook="sfx_pet_happy",
        files=["sfx_pet_happy.ogg"],
        kind="voice", character="tuanrong", source="existing", preroll_ms=0, accent_offset_ms=63,
        future_name="sfx_pet_happy_tuanrong",
        note="已有 hook。團絨聲線；細佬／訪客尚未做，fallback＝本檔＋體型音高。現有檔三音上行，能量峰約 63 ms（第一聲近 0，未改檔）。",
    ),
    ("cheer", "land", 400): dict(
        sfx_hook="sfx_pet_step_hop_a",
        files=["sfx_pet_step_hop_a.ogg", "sfx_pet_step_hop_b.ogg"],
        kind="foley", source="existing", preroll_ms=0, accent_offset_ms=12,
        note="已有 hook。落地；a/b 交替。",
    ),
    ("idle_lively", "land", 500): dict(
        sfx_hook="sfx_pet_step_hop_a",
        files=["sfx_pet_step_hop_a.ogg", "sfx_pet_step_hop_b.ogg"],
        kind="foley", source="existing", preroll_ms=0, accent_offset_ms=12,
        note="已有 hook。循環落地（750 ms）；a/b 交替。",
    ),
    ("idle_lazy", "yawn", 600): dict(
        sfx_hook="sfx_pet_yawn",
        files=["sfx_pet_yawn.ogg"],
        kind="voice", character="tuanrong", source="existing", preroll_ms=600, accent_offset_ms=603,
        future_name="sfx_pet_yawn_tuanrong",
        note="已有 hook。現有檔有吸氣前導，能量峰約 603 ms。播放起點＝t_ms−600（約 clip t=0），令呵欠峰對準 frame 3。循環 1200 ms 但檔長 1.58 s，可能同下一圈重疊；建議狀態機唔好每圈重觸發，或者淡出。細佬／訪客 fallback＝本檔＋體型音高。未改檔。",
    ),
    ("scratch_head", "scratch", 250): dict(
        sfx_hook="sfx_pet_scratch_a",
        files=["sfx_pet_scratch_a.ogg", "sfx_pet_scratch_b.ogg"],
        kind="foley", source="existing", preroll_ms=0, accent_offset_ms=7, accent_measure="onset",
        note="已有 hook。抓癢開始；a（快 6 下）／b（慢 5 下）交替。accent＝起音（約 4–7 ms），中段仲有幾下沙沙，能量峰唔喺 0。",
    ),
    # new foley
    ("part_grass", "grass_rustle", 250): dict(
        sfx_hook="sfx_pet_grass_rustle_a",
        files=["sfx_pet_grass_rustle_a.ogg", "sfx_pet_grass_rustle_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="撥草：肉墊入草＋葉沙。唔借用花盆 bump。a/b 交替。",
    ),
    ("pounce", "jump", 250): dict(
        sfx_hook="sfx_pet_jump_a",
        files=["sfx_pet_jump_a.ogg", "sfx_pet_jump_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="起跳蹬地＋短上 sweep。唔借用 step_hop（hop 係落地）。",
    ),
    ("cheer", "jump", 100): dict(
        sfx_hook="sfx_pet_jump_a",
        files=["sfx_pet_jump_a.ogg", "sfx_pet_jump_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="同 pounce 起跳共用。",
    ),
    ("carry_fruit", "footstep", 0): dict(
        sfx_hook="sfx_pet_step_walk_a",
        files=["sfx_pet_step_walk_a.ogg", "sfx_pet_step_walk_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="普通行路步。MOTION 註明唔借用 hop／drag／plod。循環兩步（0／300），a/b 交替，檔長須 <300 ms。",
    ),
    ("carry_fruit", "footstep", 300): dict(
        sfx_hook="sfx_pet_step_walk_a",
        files=["sfx_pet_step_walk_a.ogg", "sfx_pet_step_walk_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="另一步；建議播 _b 或交替。",
    ),
    ("mail_post", "footstep", 0): dict(
        sfx_hook="sfx_pet_step_walk_a",
        files=["sfx_pet_step_walk_a.ogg", "sfx_pet_step_walk_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="行近信箱，共用普通行路步。",
    ),
    ("mail_post", "letter_drop", 500): dict(
        sfx_hook="sfx_pet_letter_drop_a",
        files=["sfx_pet_letter_drop_a.ogg", "sfx_pet_letter_drop_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="信封入箱：紙沙＋細「篤」。唔借用 gift_return 事件合輯。",
    ),
    ("mail_post", "clap", 625): dict(
        sfx_hook="sfx_pet_clap_a",
        files=["sfx_pet_clap_a.ogg", "sfx_pet_clap_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="軟肉墊拍手（b 兩下）。唔借用 bug_pat。",
    ),
    ("idle_lively", "hop_peak", 250): dict(
        sfx_hook=None, files=[], kind=None, source="silent", preroll_ms=0,
        note="建議唔好有聲：循環 750 ms 嘅蹦跳峰；落地已有 step_hop。再加峰頂聲會太密。",
    ),
    ("idle_diligent", "pickup", 250): dict(
        sfx_hook="sfx_pet_pickup_a",
        files=["sfx_pet_pickup_a.ogg", "sfx_pet_pickup_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="執起葉子。循環 750 ms，請保持細聲；a/b 交替。",
    ),
    ("idle_diligent", "place", 625): dict(
        sfx_hook="sfx_pet_place_a",
        files=["sfx_pet_place_a.ogg", "sfx_pet_place_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="放低葉子。循環 750 ms。",
    ),
    ("idle_clingy", "reach", 250): dict(
        sfx_hook="sfx_pet_reach_a",
        files=["sfx_pet_reach_a.ogg", "sfx_pet_reach_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="伸爪最盡：身體前傾毛皮輕 sweep，唔用 curious／turn_huh（聲線，而且語境唔同）。循環 750 ms。若後日要加「嗯？」聲，應做 voice（每角色一檔）。",
    ),
    ("stretch", "stretch", 250): dict(
        sfx_hook="sfx_pet_stretch_a",
        files=["sfx_pet_stretch_a.ogg", "sfx_pet_stretch_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="踮腳拉到最高再放鬆。MOTION 註明唔借用 yawn。純身體／毛皮，冇口型聲。",
    ),
    ("proud_hips", "hands_hips", 250): dict(
        sfx_hook="sfx_pet_proud_a",
        files=["sfx_pet_proud_a.ogg", "sfx_pet_proud_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="挺胸叉腰：胸腔輕「噗」＋爪就位。唔借用 happy（歡呼聲太大）。若加得意叫聲應做 voice。",
    ),
    ("point_frame", "point", 375): dict(
        sfx_hook="sfx_pet_point_a",
        files=["sfx_pet_point_a.ogg", "sfx_pet_point_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="臂伸到最前：短 sweep＋細叮。",
    ),
    ("snail_postman_snail_deliver", "offer", 375): dict(
        sfx_hook="sfx_visitor_offer_letter",
        files=["sfx_visitor_offer_letter.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="鞠躬遞信：紙沙＋身低。loop 750 ms，建議只喺進入動作／每 N 圈播，唔好每圈都響。純 foley，未做訪客聲線。",
    ),
    ("mushroom_granny_granny_seed", "nod", 250): dict(
        sfx_hook="sfx_visitor_nod_a",
        files=["sfx_visitor_nod_a.ogg", "sfx_visitor_nod_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="點頭最低：軟肉墊／帽「篤」。loop 750 ms。",
    ),
    ("mushroom_granny_granny_seed", "offer", 375): dict(
        sfx_hook="sfx_visitor_offer_seed",
        files=["sfx_visitor_offer_seed.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="種子伸到最前：細有機「篤」，同遞信分開。loop 750 ms。",
    ),
    ("firefly_vendor_vendor_show", "rattle", 250): dict(
        sfx_hook="sfx_visitor_rattle_a",
        files=["sfx_visitor_rattle_a.ogg", "sfx_visitor_rattle_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="搖瓶（一邊）。同 t=500 交替 a/b。兩下相隔 250 ms，檔長須短過呢個間隔。loop 750 ms。",
    ),
    ("firefly_vendor_vendor_show", "rattle", 500): dict(
        sfx_hook="sfx_visitor_rattle_a",
        files=["sfx_visitor_rattle_a.ogg", "sfx_visitor_rattle_b.ogg"],
        kind="foley", source="new", preroll_ms=0,
        note="搖瓶（另一邊）；建議播 _b。",
    ),
}

CRITTER_CLIPS = {
    "dewlet_scared": "startle",
    "loambun_scared": "startle",
    "mossback_scared": "startle",
    "seedfluff_scared": "startle",
    "dewlet_tofruit": None,
    "loambun_tofruit": None,
    "mossback_tofruit": None,
    "seedfluff_tofruit": None,
}

def critter_assign(clip, ev, t):
    if ev == "startle":
        return dict(
            sfx_hook="sfx_critter_startle_a",
            files=["sfx_critter_startle_a.ogg", "sfx_critter_startle_b.ogg"],
            kind="foley", source="new", preroll_ms=0,
            note="受驚身體一縮（四種小動物共用）。循環 scared clip 只喺進入狀態播一次，唔好每圈（~667 ms）重播。唔做每種小動物聲線。",
        )
    if ev == "shake":
        return dict(
            sfx_hook="sfx_critter_shake_a",
            files=["sfx_critter_shake_a.ogg", "sfx_critter_shake_b.ogg"],
            kind="foley", source="new", preroll_ms=0,
            note="變成果前左右抖，四種共用。",
        )
    if ev == "transform":
        return dict(
            sfx_hook="sfx_critter_transform_a",
            files=["sfx_critter_transform_a.ogg", "sfx_critter_transform_b.ogg"],
            kind="foley", source="new", preroll_ms=0,
            note="成果瞬間：柔和短铃＋暖身，四種共用。唔借用 evolve／事件 jingle。",
        )
    if ev == "roll":
        return dict(
            sfx_hook="sfx_critter_roll_a",
            files=["sfx_critter_roll_a.ogg", "sfx_critter_roll_b.ogg"],
            kind="foley", source="new", preroll_ms=0,
            note="成果碌走：幾下軟「篤」。四種共用。",
        )
    return None


def build_map(timing):
    entries = []
    missing = []
    for c in timing["clips"]:
        for e in c.get("events", []):
            key = (c["id"], e["id"], int(e["t_ms"]))
            asg = ASSIGN.get(key)
            if asg is None:
                asg = critter_assign(c["id"], e["id"], int(e["t_ms"]))
            if asg is None:
                missing.append(key)
                continue
            rec = {
                "clip": c["id"],
                "zh_clip": c.get("zh"),
                "kind_clip": c.get("kind"),
                "event": e["id"],
                "zh": e.get("zh"),
                "frameIndex": e["frameIndex"],
                "t_ms": e["t_ms"],
                "accent": e["accent"],
                "sfx_hook": asg["sfx_hook"],
                "files": asg["files"],
                "kind": asg["kind"],
                "preroll_ms": asg.get("preroll_ms", 0),
            }
            if asg.get("accent_offset_ms") is not None:
                rec["accent_offset_ms"] = asg["accent_offset_ms"]
            if asg.get("accent_measure"):
                rec["accent_measure"] = asg["accent_measure"]
            if asg.get("character"):
                rec["character"] = asg["character"]
            if asg.get("future_name"):
                rec["future_name"] = asg["future_name"]
            if asg.get("source"):
                rec["source"] = asg["source"]
            if asg.get("note"):
                rec["note"] = asg["note"]
            entries.append(rec)
    if missing:
        raise SystemExit("unmapped events: " + ", ".join(map(str, missing)))
    return {
        "format": "anim_sfx_map/1",
        "timingSource": {
            "format": timing.get("format"),
            "stack": timing.get("stack"),
            "toleranceFrames": timing.get("toleranceFrames", 1),
            "pathHint": "read-only reference, e.g. /tmp/anim-timing/art-pet/anim_timing.json",
        },
        "rules": {
            "accent": "hook 喺 clip 嘅 t_ms 觸發；檔內 accent 預設喺 0 ms。若有 preroll_ms，播放起點＝t_ms − preroll_ms（現有 yawn 要用）。",
            "kind": {
                "foley": "共用一檔（所有角色：團絨／細佬／訪客）。執行時按體型調 playbackRate：S 1.12／M 1.00／L 0.88。a/b 交替或隨機，唔好連續兩次同一個。",
                "voice": "每角色一檔，命名 sfx_pet_<action>_<character>_<a|b>（character＝tuanrong／kid／visitor）。而家只有團絨（現有檔名尚未加角色後綴，例如 sfx_pet_happy、sfx_pet_yawn；future_name 係建議改名，今次唔改檔以免破壞現有 hook）。細佬／訪客尚未做：fallback＝團絨檔，再加體型音高。",
            },
            "characters": ["tuanrong", "kid", "visitor"],
            "sizes": SIZE_PITCH,
            "alternate_ab": True,
            "do_not_stack_sfx_tap": True,
        },
        "counts": {},
        "entries": entries,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timing", default="/tmp/anim-timing/art-pet/anim_timing.json")
    ap.add_argument("--skip-render", action="store_true")
    args = ap.parse_args()
    timing = json.loads(Path(args.timing).read_text(encoding="utf-8"))
    mp = build_map(timing)
    n_exist = sum(1 for e in mp["entries"] if e.get("source") == "existing")
    n_new = sum(1 for e in mp["entries"] if e.get("source") == "new")
    n_silent = sum(1 for e in mp["entries"] if e.get("source") == "silent")
    new_files = sorted({f for e in mp["entries"] if e.get("source") == "new" for f in e["files"]})
    exist_files = sorted({f for e in mp["entries"] if e.get("source") == "existing" for f in e["files"]})
    mp["counts"] = {
        "events": len(mp["entries"]),
        "alreadyHookedExisting": n_exist,
        "mappedToExistingAmongNulls": 0,
        "newFoleyPoints": n_new,
        "silentRecommended": n_silent,
        "newFiles": len(new_files),
        "existingFilesReused": len(exist_files),
    }
    if not args.skip_render:
        TMP.mkdir(exist_ok=True)
        SFX.mkdir(exist_ok=True)
        print("generating", len(NEW), "new files")
        for k, tgt, builder, var in NEW:
            L, dur = render_one(k, tgt, builder, var)
            print(f"{k:32s} {dur:6.3f}s  target {tgt:6.1f}  LUFS20 {L:6.1f}")
        shutil.rmtree(TMP, ignore_errors=True)
    out = ROOT / "anim_sfx_map.json"
    out.write_text(json.dumps(mp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", out, "entries", len(mp["entries"]))


if __name__ == "__main__":
    main()
