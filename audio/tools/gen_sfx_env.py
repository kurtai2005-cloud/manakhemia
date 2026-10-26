"""方案 A ④：環境互動音（花盆、曬太陽）。原創，程式合成（numpy/scipy），無取樣。固定亂數種子。
輸出 tmp/<name>.wav（未歸一）。用法（喺 audio/）：PYTHONPATH=tools python tools/gen_sfx_env.py
- sfx_env_flowerpot_bump：陶盆「篤」（幾個失諧衰減分音 + 低頻悶響 + 一下細微搖晃）＋葉沙沙＋一粒細鈴（G6），約 0.6 s。
- sfx_env_sunbathe_loop：3.529 s = 155,647 samples（1 小節 @68 BPM）。全部成分都用「整數個週期／圓周運算」所以無縫：
  暖 pad（C3／G3／C4／E4，頻率量化到整數週期，成對輕微拍頻）＋圓周濾波空氣＋疏落微光點（圓周疊尾）。"""
import os, numpy as np, soundfile as sf
from dsp import *
os.makedirs('tmp', exist_ok=True)
# ---------- sfx_env_flowerpot_bump ----------
rng = np.random.default_rng(20261104)
D = 0.60; n = int(round(D * SR)); y = np.zeros(n); t = np.arange(n) / SR
def tok(t0, amp, f0=520.0):
    """陶盆被輕撞：失諧分音（陶瓷類比例）＋短悶響"""
    out = np.zeros(n); tl = np.clip(t - t0, 0, None); on = (t >= t0).astype(float)
    for ratio, a, dk in [(1.0, 1.0, 26), (2.31, 0.55, 40), (3.67, 0.35, 55), (5.12, 0.2, 80)]:
        out += a * np.sin(2 * np.pi * f0 * ratio * tl) * np.exp(-tl * dk) * on
    thump = np.sin(2 * np.pi * np.cumsum(np.where(t >= t0, 150 * np.exp(-tl * 18) + 80, 0)) / SR) * np.exp(-tl * 20) * on
    click = bandnoise(rng, D, 900, 3200, 2) * np.exp(-tl * 120) * on * 0.2
    out = out * np.minimum(1, tl / 0.004)   # 4 ms 起音，避免尖銳 click
    return amp * (out * 0.7 + thump * 0.6 + click)
y += tok(0.02, 1.0)
y += tok(0.115, 0.28, 585.0)          # 盆身晃一下嘅細微二次聲
# 葉沙沙：幾個不規則短脈衝嘅帶通噪音（高頻偏柔）
leaf = bandnoise(rng, D, 2200, 7500, 2); env = np.zeros(n)
for c, w, a in [(0.05, 0.05, 0.9), (0.13, 0.07, 0.7), (0.22, 0.09, 0.6), (0.31, 0.08, 0.4), (0.40, 0.07, 0.22)]:
    env += a * np.exp(-0.5 * ((t - c) / (w / 2.2)) ** 2)
y += leaf * env * 0.20 * (1 + 0.5 * np.sin(2 * np.pi * 23 * t))
# 一粒細鈴 G6（1568 Hz），喺撞擊後 0.26 s
place(y, 0.26, bell(mtof(91), 0.34, decay=5.0, a=0.003, r=0.08), 0.5)
y *= 0.5 - 0.5 * np.cos(np.pi * np.clip((D - t) / 0.06, 0, 1))      # 尾端 60 ms 圓滑收
y = y - np.mean(y)
sf.write('tmp/sfx_env_flowerpot_bump.wav', y, SR, subtype='FLOAT')
# ---------- sfx_env_sunbathe_loop ----------
rng = np.random.default_rng(20261105)
NB = int(round(240 / 68 * SR)); DUR = NB / SR; ts = np.arange(NB) / SR; fq = np.fft.rfftfreq(NB, 1 / SR)
def q(f): return max(1, round(f * DUR)) / DUR          # 量化到整數週期 → 圓周無縫
def cs(f, ph=0.0): return np.sin(2 * np.pi * q(f) * ts + ph)
def cenv(cycles, depth, ph=0.0): return 1 - depth + depth * (0.5 + 0.5 * np.sin(2 * np.pi * cycles * ts / DUR + ph))
pad = np.zeros(NB)
for f, a in ((130.81, 1.0), (196.0, 0.7), (261.63, 0.55), (329.63, 0.35), (392.0, 0.12)):
    for k, det in enumerate((0.0, 2.0 / DUR)):      # 成對：差 2 個週期 / 循環 = 0.57 Hz 拍頻（暖、閃動）
        pad += a * (0.5 if k else 1.0) * np.sin(2 * np.pi * (q(f) + det) * ts + rng.uniform(0, 6.28)) * cenv(int(rng.integers(1, 3)), 0.35, rng.uniform(0, 6.28))
pad += 0.12 * cs(65.41)                                  # C2 低頻托底
x = rng.standard_normal(NB); X = np.fft.rfft(x)
H = 1 / (1 + (140 / np.maximum(fq, 1e-9)) ** 2) / (1 + (fq / 1100) ** 4); air = np.fft.irfft(X * H, NB); air /= np.std(air)
y2 = pad / np.std(pad) * 0.55 + air * 0.20 * cenv(1, 0.5, 0.7)
# 微光閃爍：疏落、極輕嘅高音鐘點（C 五聲音階），圓周疊尾
TL = int(3 * SR); buf = np.zeros(NB + TL)
for t0, m in ((0.55, 84), (1.45, 88), (2.35, 91), (3.0, 86)):
    s = bell(mtof(m), 1.4, decay=3.0, a=0.01, r=0.4, bright=0.3) * 0.045
    i = int(t0 * SR); buf[i:i + len(s)] += s[:len(buf) - i]
tail = buf[NB:]; sp = buf[:NB].copy(); sp[:len(tail)] += tail
y2 += sp * 1.0
Y = np.fft.rfft(y2); y2 = np.fft.irfft(Y / (1 + (fq / 4500) ** 4), NB)        # 暖：圓周低通
y2 -= np.mean(y2)
sf.write('tmp/sfx_env_sunbathe_loop.wav', y2, SR, subtype='FLOAT')
print('flowerpot', len(y), 'sunbathe', len(y2), NB)
