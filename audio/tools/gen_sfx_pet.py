"""《微光小圃》SFX — original procedurally generated (numpy/scipy). No samples. Writes tmp/<name>.wav (float, unnormalised)."""
import os, numpy as np, soundfile as sf
from dsp import *
rng = np.random.default_rng(20261027)
os.makedirs('tmp', exist_ok=True)
S = {}
def mixs(*a):
    y = np.zeros(max(len(x) for x in a))
    for x in a: y[:len(x)] += x
    return y
def seq(parts):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def munch(d=0.11, f0=420, f1=260, crunch=0.35):
    """soft 'mm-nom': low round blip + tiny filtered-noise crunch"""
    y = glide(f0, f1, d, a=0.006, r=0.04, decay=14); n = bandnoise(rng, 0.03, 1500, 4500)
    place(y, 0, crunch * n * adsr(len(n), 0.002, 0.02, 90)); return y
C5, D5, E5, G5, A5, C6, D6, E6, G6, A6, C7 = 72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96
# 餵食
S['sfx_feed_snack'] = seq([(0, munch()), (0.14, munch(f0=460, f1=290)), (0.30, bell(mtof(G6), 0.25, decay=14), 0.25)])
S['sfx_feed_meal'] = seq([(0, munch(0.13, 380, 240)), (0.2, munch(0.13, 400, 250)), (0.4, munch(0.13, 420, 260)),
                          (0.65, bell(mtof(E6), 0.5, decay=10), 0.5), (0.75, bell(mtof(G6), 0.5, decay=10), 0.4), (0.85, bell(mtof(C7), 0.6, decay=10), 0.3)])
# 玩耍：逗玩 – 兩個上揚俏皮顫音
S['sfx_play_tease'] = seq([(0, glide(mtof(G5), mtof(C6), 0.2, decay=5, vib=0.01, vibf=14) + 0.25 * glide(mtof(G5) * 2, mtof(C6) * 2, 0.2, decay=7)),
                           (0.16, glide(mtof(E5), mtof(A5), 0.18, decay=5, vib=0.01, vibf=14)),
                           (0.30, glide(mtof(A5), mtof(E6), 0.3, decay=5, vib=0.012, vibf=14) + 0.25 * glide(mtof(A5) * 2, mtof(E6) * 2, 0.3, decay=6))])
# 清潔：沖洗 = 水沙沙 + 氣泡
def bubble(f, d=0.07): return glide(f, f * 2.2, d, a=0.004, r=0.02, decay=30)
wash = np.zeros(int(round(1.4 * SR))); sw = bandnoise(rng, 1.4, 1800, 7000) * (0.5 + 0.5 * np.sin(2 * np.pi * 2.2 * tt(1.4))) ** 1.5 * adsr(len(wash), 0.12, 0.35)
wash += 0.35 * sw
for s in np.sort(rng.uniform(0.05, 1.2, 14)): place(wash, s, bubble(rng.uniform(500, 1400)), rng.uniform(0.12, 0.3))
S['sfx_clean_wash'] = wash
# 清便便：一抹 + 啵 + 閃光
swipe = bandnoise(rng, 0.25, 800, 5000) * adsr(int(.25 * SR), 0.08, 0.1) * np.linspace(0.3, 1, int(.25 * SR))
S['sfx_clean_poop'] = seq([(0, swipe, 0.5), (0.2, glide(300, 600, 0.09, decay=25), 0.9), (0.3, bell(mtof(E6), 0.3, decay=12), 0.4), (0.38, bell(mtof(A6), 0.4, decay=12), 0.3)])
# 睡眠：關燈 – 三音下行搖籃音 + 低頻暗下
S['sfx_sleep_on'] = verb(seq([(0, bell(mtof(E6), 1.0, decay=5)), (0.35, bell(mtof(C6), 1.0, decay=5)), (0.7, bell(mtof(G5), 1.2, decay=4)),
                              (0, glide(mtof(C5), mtof(C5 - 7), 1.6, a=0.2, r=0.6) * 0.25)]), rng, wet=0.3, rt=0.9, tail=0.3)[:int(1.9 * SR)]
# 迷你遊戲
S['sfx_mg_start'] = seq([(0, bell(mtof(C6), 0.3, decay=12), 0.8), (0.2, bell(mtof(C6), 0.3, decay=12), 0.8), (0.4, bell(mtof(G6), 0.55, decay=8)), (0.4, bell(mtof(C7), 0.55, decay=9), 0.3)])
S['sfx_mg_catch'] = mixs(bell(mtof(E6), 0.2, decay=22, a=0.002), 0.3 * bell(mtof(E6 + 12), 0.12, decay=30))
S['sfx_mg_miss'] = glide(240, 150, 0.28, a=0.01, r=0.1, decay=9) + 0.15 * bandnoise(rng, 0.28, 300, 1200) * adsr(int(.28 * SR), 0.01, 0.1, 18)
S['sfx_mg_win'] = verb(seq([(i * 0.1, bell(mtof(m), 0.6, decay=7)) for i, m in enumerate([C6, E6, G6, A6, C7])] +
                           [(0.5, bell(mtof(m), 1.2, decay=3), 0.5) for m in (C6, E6, G6, D6 + 12)]), rng, wet=0.25, rt=0.9, tail=0.3)[:int(1.95 * SR)]
S['sfx_reward_orb'] = verb(seq([(0, bell(mtof(G6), 0.4, decay=10)), (0.09, bell(mtof(C7), 0.4, decay=10)), (0.18, bell(mtof(E6 + 12), 0.6, decay=8), 0.8),
                                (0.18, bell(mtof(G6 + 12), 0.5, decay=12), 0.2)]), rng, wet=0.3, rt=0.5, tail=0.2)
# Jingles（≤3s）
def swell(d, lo, hi, amp=1.0):
    n = bandnoise(rng, d, lo, hi); return n * adsr(len(n), d * 0.8, d * 0.2) ** 1.5 * amp
def padchord(ms, d, a, r, amp=1.0):
    y = 0
    for m in ms: y = y + softsine(mtof(m), d, a=a, r=r, harm=(1, 2), amps=(1, .25)) + softsine(mtof(m) * 1.003, d, a=a, r=r, harm=(1,), amps=(.6,))
    return y * amp / len(ms)
tick = lambda f: mixs(bandnoise(rng, 0.02, 2000, 6000) * adsr(int(.02 * SR), 0.001, 0.015, 120), 0.5 * glide(f, f * 0.8, 0.04, decay=60))
hatch = seq([(0.0, tick(900), 0.5), (0.35, tick(1000), 0.6), (0.62, tick(1100), 0.7), (0.62 + 0.14, tick(1250), 0.8),
             (0.9, swell(0.8, 2500, 9000), 0.12), (0.9, padchord([C5, G5, E6], 1.0, 0.7, 0.2), 0.6)] +
            [(1.55 + i * 0.12, bell(mtof(m), 1.2, decay=4), 0.7) for i, m in enumerate([C6, E6, G6, C7])] +
            [(1.55, padchord([C5, G5, C6, E6], 1.4, 0.05, 0.9), 0.5)])
S['sfx_hatch'] = verb(hatch, rng, wet=0.25, rt=1.0, tail=0.2)[:int(2.9 * SR)]
evo = seq([(0, padchord([C5, G5], 1.6, 1.2, 0.2), 0.6), (0.1, swell(1.5, 1500, 8000), 0.1)] +
          [(0.1 + i * 0.14, bell(mtof(m), 0.8, decay=6), 0.55 + 0.05 * i) for i, m in enumerate([C5, D5, E5, G5, A5, C6, D6, E6])] +
          [(1.35, padchord([C5, G5, E6, D6 + 12], 1.5, 0.04, 1.0), 0.55)] +
          [(1.3 + i * 0.07, bell(mtof(m), 1.0, decay=5), 0.4) for i, m in enumerate([G6, C7, E6 + 12, G6 + 12])])
S['sfx_evolve'] = verb(evo, rng, wet=0.28, rt=1.1, tail=0.2)[:int(2.9 * SR)]
fade = seq([(0, padchord([C5 - 12 + 12, E5, G5, A5], 2.8, 0.5, 1.4), 0.7)] +
           [(0.1 + i * 0.4, bell(mtof(m), 1.4, decay=3.5), 0.6) for i, m in enumerate([G5, E6, D6, C6])] +  # 下行、溫暖
           [(1.5 + i * 0.09, bell(mtof(m), 1.3, decay=4), 0.3) for i, m in enumerate([C6, E6, G6, C7, E6 + 12, G6 + 12])] +  # 光粒上升
           [(1.2, swell(1.6, 3000, 10000), 0.05)])
S['sfx_fade_light'] = verb(fade, rng, wet=0.3, rt=1.3, tail=0.2)[:int(3.0 * SR)]
for k, v in S.items():
    v = v - np.mean(v); nf = int(0.04 * SR); v[-nf:] *= np.linspace(1, 0, nf)  # 40ms 收尾，避免截斷 click
    v = v / np.max(np.abs(v)) * 0.8
    sf.write(f'tmp/{k}.wav', v, SR, subtype='PCM_16')
print(len(S), 'pet sfx generated')
