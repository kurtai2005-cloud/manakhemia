"""《微光小圃》M1b 功能音（郵局／廚房／圖鑑／家具／狩獵）。

100% 原創程式合成（numpy/scipy），無取樣、無錄音、無第三方素材。現有檔一字未改。
規格：ogg Vorbis 44.1 kHz 單聲道 -q:a 4、-fflags +bitexact；HPF 120 Hz、LPF 6.5 kHz；
檔頭 3 ms 餘弦淡入、檔尾 20 ms 淡出＋10 ms 靜音（循環檔 sfx_kitchen_stir 例外：0.500 s 圓周無縫，冇尾靜音）；
峰值上限 -1.5 dBFS（硬上限 -1）；純增益迭代至 LUFS20 目標（解碼後無間隔重複 20 次）。
重音喺 0 ms（hook 觸發即播）。每個檔用 crc32(檔名) 做隨機種子。

LUFS20：-14 主要功能動作；-16 次要；-18 環境／可循環（攪拌）。
音色刻意同現有 ui8／寵物／小動物檔分開（見各函式註解）。

用法（喺 audio/）：
  PYTHONPATH=tools /workspace/audio-venv/bin/python tools/gen_sfx_m1b.py
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
TMP = ROOT / "tmp_m1b"
SFX = ROOT / "sfx"
CEIL = 10 ** (-1.7 / 20)  # headroom for Vorbis overshoot; hard cap still -1 dBFS
HP = butter(2, 120 / (SR / 2), "high", output="sos")
LP = butter(2, 6500 / (SR / 2), output="sos")

ACC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(s: str) -> float:
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
    na = min(na, max(1, n // 2))
    nr = min(nr, n - na)
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    e[n - nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e


def band(rng, n, lo, hi, order=2):
    x = rng.standard_normal(n)
    lo = max(lo, 30.0)
    hi = min(hi, SR * 0.45)
    if lo >= hi:
        return x * 0
    return sosfiltfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), x)


def nz(x):
    return x / (np.max(np.abs(x)) + 1e-12)


LP_BODY = butter(2, 1400 / (SR / 2), output="sos")


def fill_body(v, wet=0.55):
    """Add a lowpassed copy so short attacks can reach target LUFS without a limiter."""
    v = np.asarray(v, float)
    body = sosfiltfilt(LP_BODY, v)
    return v * (1.0 - wet * 0.35) + wet * body


def flatten_crest(v, ratio=0.5):
    """Lower crest factor by a linear RMS gain ride (no tanh / limiter)."""
    v = np.asarray(v, float)
    win = max(1, int(0.025 * SR))
    env = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, "same") + 1e-12)
    floor = max(float(np.percentile(env, 20)), 1e-6)
    env = np.maximum(env, floor)
    target = float(np.mean(env))
    g = np.clip(target / env, 0.45, 2.2)
    g = 1.0 + ratio * (g - 1.0)
    return v * g



def paper(rng, d, lo=1400, hi=5200, decay=7.0, att=0.006, flutter=16.0):
    """Paper flutter — mid-high band noise, slower than a letter-drop tick."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    x = band(rng, n, lo, hi)
    fl = 0.55 + 0.45 * np.sin(2 * np.pi * flutter * t + rng.uniform(0, 2 * np.pi))
    return nz(x) * np.exp(-t * decay) * fl * fade(n, att, 0.06)


def whoosh(rng, d, f0=900.0, f1=260.0, lo=220, hi=2800, att=0.004):
    """Soft body/air whoosh: descending band + sine glide. Not a chip sweep."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    x = band(rng, n, lo, hi)
    env = np.exp(-t * 8.0) * fade(n, att, 0.08)
    f = f0 * (f1 / max(f0, 1e-9)) ** np.clip(t / max(d, 1e-9), 0, 1)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) * np.exp(-t * 10.0)
    return nz(0.85 * nz(x) * env + 0.45 * tone * env)


def wood(f, d=0.26, decay=18.0, att=0.006, noise=0.10, rng=None):
    """Warm wooden / mailbox / furniture body: inharmonic partials, short noise attack."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * decay)
    y += 0.48 * np.sin(2 * np.pi * f * 1.76 * t) * np.exp(-t * decay * 1.55)
    y += 0.22 * np.sin(2 * np.pi * f * 2.33 * t) * np.exp(-t * decay * 2.2)
    y += 0.10 * np.sin(2 * np.pi * f * 3.15 * t) * np.exp(-t * decay * 3.0)
    if rng is not None and noise > 0:
        attn = band(rng, n, 400, 2800)
        y += noise * nz(attn) * np.exp(-t * 70.0)
    return nz(y) * fade(n, att, 0.05)


def pot(f, d=0.35, decay=10.0, att=0.004, rng=None):
    """Warm pan/lid: less bright than a glock/celesta, slightly inharmonic."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    parts = [(1.0, 1.0, 1.0), (1.47, 0.45, 1.4), (2.15, 0.22, 2.0), (2.98, 0.10, 2.8)]
    y = np.zeros(n)
    for r, a, dk in parts:
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * decay * dk)
    if rng is not None:
        y += 0.08 * nz(band(rng, n, 600, 2400)) * np.exp(-t * 40.0)
    return nz(y) * fade(n, att, 0.06)


def softbell(f, d=0.40, decay=9.0, att=0.004, kind="warm"):
    """Warm mid bell — 1,2,2.76 partials only, no 5.4× glock sheen, LPF later.
    Distinct from ui8 celesta (1,2,3,4.2) / glock (1,2.76,5.4) clusters."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    if kind == "warm":
        parts = [(1.0, 1.0, 1.0), (2.0, 0.22, 1.8), (2.76, 0.08, 2.6)]
    else:
        parts = [(1.0, 1.0, 1.0), (1.5, 0.18, 1.6), (2.0, 0.10, 2.2)]
    y = np.zeros(n)
    for r, a, dk in parts:
        y += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * decay * dk)
    return nz(y) * fade(n, att, 0.05)


def body_pad(notes, d, a=0.008, r=0.12, decay=3.2):
    """Mid pad under a one-shot so LUFS can reach -14 without a spiky peak."""
    n = int(round(d * SR))
    t = np.arange(n) / SR
    y = np.zeros(n)
    for m in notes:
        f = mtof(midi(m) if isinstance(m, str) else m)
        y += np.sin(2 * np.pi * f * t)
        y += 0.35 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * decay * 1.2)
        y += 0.12 * np.sin(2 * np.pi * f * 3 * t) * np.exp(-t * decay * 1.8)
    return nz(y) * fade(n, a, r) * np.exp(-t * decay * 0.22)


def steam(rng, d, lo=1800, hi=4800, att=0.02):
    n = int(round(d * SR))
    t = np.arange(n) / SR
    x = band(rng, n, lo, hi)
    env = (0.4 + 0.6 * (1 - np.exp(-t * 12.0))) * np.exp(-t * 3.2) * fade(n, att, 0.08)
    return nz(x) * env


# ---------------------------------------------------------------------------
# Builders — each starts with the hook energy at 0 ms.
# ---------------------------------------------------------------------------

def sfx_post_letter_send(name):
    """寄信：信紙甩入郵筒＋木門篤。長過 letter_drop（0.17 s 短篤），冇 visitor offer 嘅「遞出」。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.62 * SR)))
    place(y, 0.000, whoosh(rng, 0.22, f0=1100, f1=240, lo=300, hi=2600), 0.70)
    place(y, 0.000, paper(rng, 0.32, lo=1600, hi=4800, decay=8.0, flutter=21.0), 0.55)
    place(y, 0.000, wood(210, 0.20, decay=26, noise=0.22, rng=rng), 0.85)
    place(y, 0.000, body_pad(["G3", "D4", "G4"], 0.55, decay=3.4), 0.70)
    place(y, 0.085, paper(rng, 0.18, lo=2000, hi=5000, decay=14.0, flutter=28.0), 0.22)
    return y


def sfx_post_letter_receive(name):
    """收信：信落到枱＋細蠟印篤，上行，唔似 ui8_confirm 嘅 80 ms 落章。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.62 * SR)))
    place(y, 0.000, wood(190, 0.18, decay=24, noise=0.16, rng=rng), 0.70)
    place(y, 0.000, paper(rng, 0.28, lo=1300, hi=4200, decay=7.5, flutter=14.0), 0.60)
    place(y, 0.000, body_pad(["C4", "E4", "G4"], 0.56, decay=3.2), 0.62)
    place(y, 0.020, softbell(mtof(midi("E5")), 0.36, decay=10.0), 0.42)
    place(y, 0.110, softbell(mtof(midi("A5")), 0.28, decay=12.0), 0.28)
    return y


def sfx_kitchen_cook_start(name):
    """開火：暖鍋沿＋細蒸汽，唔似 feed_meal 嘅咀嚼。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.58 * SR)))
    place(y, 0.000, pot(196, 0.28, decay=14.0, rng=rng), 1.10)
    place(y, 0.000, wood(155, 0.18, decay=24, noise=0.16, rng=rng), 0.80)
    place(y, 0.000, body_pad(["C3", "G3", "C4"], 0.55, decay=3.2), 0.58)
    place(y, 0.040, steam(rng, 0.36), 0.22)
    return y


def sfx_kitchen_cook_done(name):
    """煮好：鍋蓋叮（中音暖鈴，唔用 C7 鋼片琴簇）＋輕蒸汽。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.70 * SR)))
    place(y, 0.000, pot(262, 0.28, decay=11.0, rng=rng), 0.80)
    place(y, 0.000, softbell(mtof(midi("G5")), 0.48, decay=8.5), 0.70)
    place(y, 0.000, body_pad(["C4", "E4", "G4"], 0.72, decay=2.2), 0.85)
    place(y, 0.090, softbell(mtof(midi("D6")), 0.36, decay=11.0), 0.36)
    place(y, 0.030, steam(rng, 0.32, lo=2000, hi=4500), 0.12)
    return y


def sfx_kitchen_stir(name):
    """短攪拌，0.500 s 圓周無縫，可 start_loop（見 README：AudioManager 要檔名有 _loop 先自動循環）。"""
    rng = rng_for(name)
    n = int(round(0.500 * SR))  # 22050
    t = np.arange(n) / SR
    # viscous swirl: two slow moving band-noise layers, integer cycles in 0.5 s
    swirl = band(rng, n, 250, 1600)
    swirl2 = band(rng, n, 800, 2800)
    # 4 cycles / 0.5 s = 8 Hz, 2 cycles = 4 Hz — periodic so it tiles
    lfo1 = 0.55 + 0.45 * np.sin(2 * np.pi * 8.0 * t)
    lfo2 = 0.50 + 0.50 * np.sin(2 * np.pi * 4.0 * t + 0.7)
    y = 0.70 * nz(swirl) * lfo1 + 0.40 * nz(swirl2) * lfo2
    # wooden tick at 0 ms (accent) and a softer one at 250 ms (half loop)
    tick = wood(220, 0.12, decay=36, noise=0.20, rng=rng)
    place(y, 0.000, tick, 0.85)
    place(y, 0.250, wood(200, 0.10, decay=40, noise=0.14, rng=rng), 0.40)
    # circularize: crossfade 8 ms of end onto start after placing ticks
    xf = int(0.008 * SR)
    fade_in = 0.5 - 0.5 * np.cos(np.pi * np.arange(xf) / xf)
    fade_out = 1.0 - fade_in
    head = y[:xf].copy()
    tail = y[-xf:].copy()
    y[:xf] = head * fade_in + tail * fade_out
    y[-xf:] = tail * fade_out + head * fade_in
    return y


def sfx_codex_page_flip(name, variant="a"):
    """翻頁：長紙摩擦＋翻面氣流。長過 letter 聲，冇鋼片琴。a/b 速度同音高略異。"""
    rng = rng_for(name)
    flutter = 12.0 if variant == "a" else 15.5
    lo, hi = (1100, 3800) if variant == "a" else (1300, 4300)
    y = np.zeros(int(round(0.48 * SR)))
    place(y, 0.000, whoosh(rng, 0.20, f0=700 if variant == "a" else 820,
                           f1=220, lo=200, hi=2200), 0.55)
    place(y, 0.000, paper(rng, 0.36, lo=lo, hi=hi, decay=6.2, flutter=flutter), 0.90)
    place(y, 0.000, wood(140 if variant == "a" else 155, 0.12, decay=40, noise=0.10, rng=rng), 0.35)
    place(y, 0.000, body_pad(["D4", "A4"] if variant == "a" else ["E4", "B4"], 0.42, decay=4.0), 0.42)
    return y


def sfx_codex_new_entry(name):
    """新圖鑑格：紙上一記＋上行五度暖鈴。唔用 ui8_confirm 落章 thump，亦唔用 btn_sparkle 三連鈴。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.62 * SR)))
    place(y, 0.000, wood(175, 0.16, decay=28, noise=0.14, rng=rng), 0.55)
    place(y, 0.000, paper(rng, 0.20, lo=1500, hi=3600, decay=10.0, flutter=10.0), 0.30)
    place(y, 0.000, softbell(mtof(midi("G5")), 0.46, decay=8.0), 0.85)
    place(y, 0.000, body_pad(["C4", "E4", "G4"], 0.58, decay=3.0), 0.55)
    place(y, 0.085, softbell(mtof(midi("D6")), 0.40, decay=9.5), 0.50)
    return y


def sfx_furn_pickup(name):
    """提起家具：偏重木身向上拉，重過 sfx_pet_pickup（招牌、0.15 s、-22）。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.42 * SR)))
    place(y, 0.000, wood(130, 0.22, decay=18, noise=0.16, rng=rng), 0.90)
    place(y, 0.000, whoosh(rng, 0.18, f0=280, f1=620, lo=150, hi=1600), 0.40)
    place(y, 0.000, body_pad(["G2", "D3", "G3"], 0.40, decay=3.6), 0.55)
    return y


def sfx_furn_place(name, variant="a"):
    """放下家具：實木落地。a 偏低、b 稍亮。唔借用 sfx_pet_place。"""
    rng = rng_for(name)
    f = 118 if variant == "a" else 138
    y = np.zeros(int(round(0.48 * SR)))
    place(y, 0.000, wood(f, 0.28, decay=16, noise=0.22, rng=rng), 1.00)
    place(y, 0.000, body_pad(["C3", "G3", "C4"] if variant == "a" else ["D3", "A3", "D4"], 0.50, decay=3.2), 0.62)
    place(y, 0.025, softbell(mtof(midi("E4" if variant == "a" else "F4")), 0.22, decay=16.0), 0.12)
    return y


def sfx_furn_buy(name):
    """買家具：短購買鐘（G4–D5），唔係 toast 用嘅 ui8_coin 數位跳。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.55 * SR)))
    place(y, 0.000, wood(165, 0.14, decay=30, noise=0.10, rng=rng), 0.40)
    place(y, 0.000, softbell(mtof(midi("G4")), 0.42, decay=8.0), 1.00)
    place(y, 0.000, body_pad(["C4", "E4", "G4"], 0.54, decay=3.0), 0.55)
    place(y, 0.070, softbell(mtof(midi("D5")), 0.30, decay=12.0), 0.28)
    return y


def sfx_hunt_pounce(name, variant="a"):
    """撲出：身體氣流＋軟著地墊。唔代替 pounce clip 已有嘅 jump／land（腳步）；呢個係撲本身嘅體勢。"""
    rng = rng_for(name)
    f0, f1 = (1000, 200) if variant == "a" else (860, 180)
    y = np.zeros(int(round(0.42 * SR)))
    place(y, 0.000, whoosh(rng, 0.22, f0=f0, f1=f1, lo=180, hi=2400), 0.70 if variant == "a" else 0.55)
    place(y, 0.000, wood(150 if variant == "a" else 138, 0.16, decay=28, noise=0.18, rng=rng), 0.45 if variant == "a" else 0.32)
    place(y, 0.000, body_pad(["A2", "E3", "A3"] if variant == "a" else ["G2", "D3", "G3"], 0.48 if variant=="a" else 0.55, decay=3.2), 0.70 if variant=="a" else 1.10)
    if variant == "b":
        y = flatten_crest(y, ratio=0.8)
    return y


def sfx_hunt_enter(name):
    """入草原：短草沙＋兩粒暖撥弦（合成 pluck，唔用 VCSL）。短過 treasure_hunt（2.5 s），亦唔似 veil 光幕。"""
    rng = rng_for(name)
    y = np.zeros(int(round(0.78 * SR)))
    grass = paper(rng, 0.40, lo=800, hi=3400, decay=5.0, flutter=9.0)
    place(y, 0.000, grass, 0.50)
    place(y, 0.000, whoosh(rng, 0.28, f0=640, f1=200, lo=160, hi=1800), 0.45)
    place(y, 0.000, body_pad(["C3", "G3", "C4"], 0.72, decay=2.6), 0.62)
    # two warm plucks (additive, harp-like but original)
    def pluck(f, d=0.55, decay=3.4):
        n = int(round(d * SR))
        t = np.arange(n) / SR
        z = np.zeros(n)
        for h in range(1, 7):
            z += (1.0 / h ** 1.3) * np.sin(2 * np.pi * f * h * t) * np.exp(-t * decay * (1 + 0.8 * (h - 1)))
        return nz(z) * fade(n, 0.003, 0.08)
    place(y, 0.000, pluck(mtof(midi("G4"))), 0.55)
    place(y, 0.095, pluck(mtof(midi("D5")), 0.48, decay=3.8), 0.40)
    return y


SPECS = {
    "sfx_post_letter_send":    dict(fn=sfx_post_letter_send,    tgt=-14.0, loop=False),
    "sfx_post_letter_receive": dict(fn=sfx_post_letter_receive, tgt=-14.0, loop=False),
    "sfx_kitchen_cook_start":  dict(fn=sfx_kitchen_cook_start,  tgt=-14.0, loop=False),
    "sfx_kitchen_cook_done":   dict(fn=sfx_kitchen_cook_done,   tgt=-14.0, loop=False),
    "sfx_kitchen_stir":        dict(fn=sfx_kitchen_stir,        tgt=-18.0, loop=True),
    "sfx_codex_page_flip_a":   dict(fn=lambda n: sfx_codex_page_flip(n, "a"), tgt=-16.0, loop=False),
    "sfx_codex_page_flip_b":   dict(fn=lambda n: sfx_codex_page_flip(n, "b"), tgt=-16.0, loop=False),
    "sfx_codex_new_entry":     dict(fn=sfx_codex_new_entry,     tgt=-14.0, loop=False),
    "sfx_furn_pickup":         dict(fn=sfx_furn_pickup,         tgt=-16.0, loop=False),
    "sfx_furn_place_a":        dict(fn=lambda n: sfx_furn_place(n, "a"), tgt=-14.0, loop=False),
    "sfx_furn_place_b":        dict(fn=lambda n: sfx_furn_place(n, "b"), tgt=-14.0, loop=False),
    "sfx_furn_buy":            dict(fn=sfx_furn_buy,            tgt=-14.0, loop=False),
    "sfx_hunt_pounce_a":       dict(fn=lambda n: sfx_hunt_pounce(n, "a"), tgt=-14.0, loop=False),
    "sfx_hunt_pounce_b":       dict(fn=lambda n: sfx_hunt_pounce(n, "b"), tgt=-14.0, loop=False),
    "sfx_hunt_enter":          dict(fn=sfx_hunt_enter,          tgt=-14.0, loop=False),
}


def lufs20(path: Path) -> float:
    x, sr = sf.read(str(path))
    tmp = "/tmp/_m1b_l20.wav"
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


def finish(v, loop=False):
    if loop:
        # already circular 0.500 s; circular EQ (filtfilt is not periodic), no pad
        v = np.asarray(v, float)
        v = v - np.mean(v)
        V = np.fft.rfft(v)
        fr = np.fft.rfftfreq(len(v), 1 / SR)
        H = (1 / (1 + (120 / np.maximum(fr, 1e-9)) ** 4)) * (1 / (1 + (fr / 6500) ** 6))
        v = np.fft.irfft(V * H, len(v))
        # C0 seam
        k = int(0.008 * SR)
        delta = v[0] - v[-1]
        v[-k:] += delta * (np.arange(1, k + 1) / float(k + 1))
        # force exact length
        n = int(round(0.500 * SR))
        if len(v) >= n:
            v = v[:n]
        else:
            v = np.concatenate([v, np.zeros(n - len(v))])
        return v
    a = np.abs(v)
    nz_i = np.nonzero(a > a.max() * 1e-3)[0]
    if len(nz_i):
        v = v[: nz_i[-1] + 1]
    # cap ~0.85 s including pad (hunt_enter a bit longer)
    hi_n = int(0.85 * SR) - int(0.01 * SR)
    if len(v) > hi_n:
        v = v[:hi_n].copy()
        nq = int(0.04 * SR)
        v[-nq:] *= np.linspace(1, 0.4, nq)
    v = fill_body(v, wet=0.70)
    v = flatten_crest(v, ratio=0.55)
    v = sosfiltfilt(LP, sosfiltfilt(HP, v - np.mean(v)))
    na = int(0.003 * SR)
    v[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nf = int(0.020 * SR)
    v[-nf:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf)
    v = np.concatenate([v, np.zeros(int(0.01 * SR))])
    if len(v) < int(0.28 * SR):
        v = np.concatenate([v, np.zeros(int(0.28 * SR) - len(v))])
    return v


def generate():
    SFX.mkdir(exist_ok=True)
    rows = []
    for k, spec in SPECS.items():
        loop = bool(spec.get("loop"))
        tgt = float(spec["tgt"])
        v = finish(spec["fn"](k), loop=loop)
        v = v / (np.max(np.abs(v)) + 1e-12) * 0.3
        g = 0.0
        L = peak = 0.0
        y = v
        path = SFX / f"{k}.ogg"
        for _ in range(20):
            y = v * 10 ** (g / 20)
            path = enc(y, k)
            x, _ = sf.read(str(path))
            peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
            if peak > -1.15:
                g -= (peak - (-1.6)) + 0.10
                continue
            L = lufs20(path)
            # stop if on target, or decoded peak already close to the cap
            if abs(L - tgt) <= 0.15 or (L < tgt and peak >= -1.35):
                break
            g += tgt - L
        if peak > -1.15:
            y = y * 10 ** ((-1.6 - peak) / 20)
            path = enc(y, k)
            x, _ = sf.read(str(path))
            peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
            L = lufs20(path)
        print(f"{k:26s} {len(y)/SR:6.3f}s  LUFS20 {L:6.2f} (tgt {tgt:.1f})  peak {peak:6.2f} dBFS")
        rows.append((k, path, L, peak, tgt))
    shutil.rmtree(TMP, ignore_errors=True)
    return rows


if __name__ == "__main__":
    os.chdir(ROOT)
    generate()
    print(f"{len(SPECS)} m1b sfx generated")
