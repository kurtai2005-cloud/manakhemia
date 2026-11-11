"""《微光小圃》需求泡泡提示音（sfx_need_warning_a / _b）。

需要泡泡（飢／潔／親等）出現時播一次：柔和、聽得到、唔急促，唔係錯誤蜂鳴。
兩音上行圓潤「啵鈴」＋一粒細閃光；重音喺 0 ms（hook 喺泡泡出現即播）。
音色刻意同 sfx_ui8_error（低暖雙噗、向下）、sfx_ui8_toast_in／sfx_ui8_popup_open
（25% 脈衝上滑＋C7／G6 鋼片琴、重音約 220–238 ms）分開：正弦／二諧波圓氣泡、
中音域（E5→A5／F5→Bb5），冇方波、冇密集 shimmer。b 係輕微變體。

100% 原創程式合成（numpy/scipy），無取樣、無錄音、無第三方素材。
規格：ogg Vorbis 44.1 kHz 單聲道 -q:a 4、-fflags +bitexact；HPF 120 Hz、LPF 5.5 kHz
（圓潤、壓低玻璃感）；檔頭 3 ms 餘弦淡入、檔尾 20 ms 淡出＋10 ms 靜音；
峰值上限 -1.5 dBFS（硬上限 -1）；純增益迭代至 LUFS20 -18（次要／通知檔，
解碼後無間隔重複 20 次）。每個檔用 crc32(檔名) 做隨機種子。長度 0.35–0.5 s。

用法（喺 audio/）：
  PYTHONPATH=tools /workspace/audio-venv/bin/python tools/gen_sfx_need.py
"""
from __future__ import annotations
import os, shutil, subprocess, zlib
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfiltfilt

from dsp import SR, mtof, place
from measure import ebur

FF = os.environ.get("FF", "ffmpeg")
ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "tmp_need"
SFX = ROOT / "sfx"
TGT = -18.0
CEIL = 10 ** (-1.5 / 20)
HP = butter(2, 120 / (SR / 2), "high", output="sos")
LP = butter(2, 5500 / (SR / 2), output="sos")

ACC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(s: str) -> float:
    # 'E5', 'Bb5', 'Eb6'
    name = s[0]
    i = 1
    off = 0
    if i < len(s) and s[i] in "b#":
        off = -1 if s[i] == "b" else 1
        i += 1
    return 12 * (int(s[i:]) + 1) + ACC[name] + off


def rng_for(name: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(name.encode("utf-8")) & 0xFFFFFFFF)


def fade(n, a, r):
    e = np.ones(n)
    na = max(1, int(a * SR))
    nr = max(1, int(r * SR))
    na = min(na, n // 2)
    nr = min(nr, n - na)
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    e[n - nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e


def bubble(f, d, rng, decay=9.5, chirp=1.10, h2=0.22, h3=0.05, pop=0.07, att=0.006):
    """Round soap-bubble tone: sine + soft 2nd/3rd, brief downward settle, tiny band pop."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    # start slightly sharp, settle to f in ~25 ms (rounded pop, not a chip glide)
    f_t = f * (1.0 + (chirp - 1.0) * np.exp(-t * 85.0))
    ph = 2 * np.pi * np.cumsum(f_t) / SR
    y = np.sin(ph)
    y += h2 * np.sin(2 * ph) * np.exp(-t * decay * 1.7)
    y += h3 * np.sin(3 * ph) * np.exp(-t * decay * 2.6)
    y *= np.exp(-t * decay * 0.52)
    if pop > 0:
        noise = rng.standard_normal(n)
        lo, hi = 900 / (SR / 2), 2200 / (SR / 2)
        noise = sosfiltfilt(butter(2, [lo, hi], "band", output="sos"), noise)
        pop_env = np.exp(-t * 70.0) * fade(n, 0.002, d - 0.01)
        y += pop * noise / (np.max(np.abs(noise)) + 1e-12) * pop_env
    y *= fade(n, att, 0.04)
    return y / (np.max(np.abs(y)) + 1e-12)


def sparkle(f, d=0.16, decay=18.0, att=0.004):
    """One tiny high sine grain — a fleck, not a celesta cluster."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * decay)
    y += 0.12 * np.sin(2 * np.pi * f * 1.997 * t) * np.exp(-t * decay * 1.8)
    return y * fade(n, att, 0.03) / (np.max(np.abs(y)) + 1e-12)


def build(name: str, lo: str, hi: str, gap_ms: float, spark_ms: float, spark_note: str, gap2=None):
    rng = rng_for(name)
    y = np.zeros(int(round(0.48 * SR)))
    n1 = bubble(mtof(midi(lo)), 0.38, rng, decay=8.0, chirp=1.12, h2=0.26, h3=0.08, pop=0.10, att=0.004)
    n2 = bubble(mtof(midi(hi)), 0.32, rng, decay=11.5, chirp=1.07, h2=0.18, h3=0.04, pop=0.04, att=0.006)
    place(y, 0.0, n1, 1.00)
    place(y, gap_ms / 1000.0, n2, 0.55)  # quieter follow-up so RMS accent stays on note 1
    place(y, spark_ms / 1000.0, sparkle(mtof(midi(spark_note)), 0.16, 16.0), 0.22)
    if gap2 is not None:
        # b only: a second, even softer fleck, different pitch
        t2, note2, g2 = gap2
        place(y, t2 / 1000.0, sparkle(mtof(midi(note2)), 0.12, 20.0), g2)
    return y


SPECS = {
    # a: E5 → A5 (perfect 4th), compact
    "sfx_need_warning_a": dict(lo="E5", hi="A5", gap_ms=95, spark_ms=175, spark_note="D6"),
    # b: F5 → Bb5 (same interval, a semitone up), slightly later second note
    "sfx_need_warning_b": dict(lo="F5", hi="Bb5", gap_ms=108, spark_ms=188, spark_note="Eb6",
                               gap2=(230, "G6", 0.09)),
}


def lufs20(path: Path) -> float:
    x, sr = sf.read(str(path))
    tmp = "/tmp/_need_l20.wav"
    sf.write(tmp, np.tile(x, 20), sr, subtype="FLOAT")
    return ebur(tmp)[0]


def enc(x, k: str) -> Path:
    TMP.mkdir(exist_ok=True)
    wav = TMP / f"{k}.wav"
    out = SFX / f"{k}.ogg"
    sf.write(str(wav), x, SR, subtype="FLOAT")
    subprocess.run(
        [FF, "-y", "-v", "error", "-i", str(wav),
         "-ac", "1", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "4",
         "-fflags", "+bitexact", "-flags:a", "+bitexact", str(out)],
        check=True,
    )
    return out


def finish(v):
    a = np.abs(v)
    nz = np.nonzero(a > a.max() * 1e-3)[0]
    v = v[: nz[-1] + 1]
    # keep duration in 0.35–0.50 s including 10 ms pad
    hi_n = int(0.50 * SR) - int(0.01 * SR)
    if len(v) > hi_n:
        v = v[:hi_n].copy()
        nq = int(0.04 * SR)
        v[-nq:] *= np.linspace(1, 0.4, nq)
    v = sosfiltfilt(LP, sosfiltfilt(HP, v - np.mean(v)))
    na = int(0.003 * SR)
    v[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nf = int(0.020 * SR)
    v[-nf:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf)
    v = np.concatenate([v, np.zeros(int(0.01 * SR))])
    if len(v) < int(0.35 * SR):
        v = np.concatenate([v, np.zeros(int(0.35 * SR) - len(v))])
    return v


def generate():
    SFX.mkdir(exist_ok=True)
    rows = []
    for k, spec in SPECS.items():
        extra = {}
        if "gap2" in spec:
            extra["gap2"] = spec["gap2"]
        v = finish(build(k, spec["lo"], spec["hi"], spec["gap_ms"], spec["spark_ms"],
                         spec["spark_note"], **extra))
        v = v / (np.max(np.abs(v)) + 1e-12) * 0.3
        g = 0.0
        L = peak = 0.0
        y = v
        path = SFX / f"{k}.ogg"
        for _ in range(8):
            y = v * 10 ** (g / 20)
            if np.max(np.abs(y)) > CEIL:
                y = y / np.max(np.abs(y)) * CEIL
            path = enc(y, k)
            x, _ = sf.read(str(path))
            peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
            if peak > -1.1:
                g -= (peak - (-1.5)) + 0.1
                continue
            L = lufs20(path)
            if abs(L - TGT) <= 0.15 or (L < TGT and np.max(np.abs(y)) >= CEIL * 0.999):
                break
            g += TGT - L
        print(f"{k:24s} {len(y)/SR:6.3f}s  LUFS20 {L:6.2f}  peak {peak:6.2f} dBFS")
        rows.append((k, path, L, peak))
    shutil.rmtree(TMP, ignore_errors=True)
    return rows


if __name__ == "__main__":
    os.chdir(ROOT)
    generate()
    print("2 need-warning sfx generated")
