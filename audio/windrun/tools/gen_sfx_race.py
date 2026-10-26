"""《風野競走》賽中 SFX（12 個）＋ 3 個 stinger — 原創程式合成（numpy/scipy），無取樣。
輸出 tmp/<name>.wav（float，未標準化；之後由 norm.py 設響度）。固定亂數種子，可重現。
SFX 單聲道；stinger（finish／win／lose）立體聲。設計原則：起音喺 ≤10 ms 內（音畫同步）、柔和唔刺耳。"""
import os, numpy as np, soundfile as sf
from dsp import *
from gen_bgm_race import flute, gpluck
rng = np.random.default_rng(20261030)
os.makedirs('tmp', exist_ok=True)
def mixs(*a):
    y = np.zeros(max(len(x) for x in a))
    for x in a: y[:len(x)] += x
    return y
def seq(parts, total=None):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(max(L, int((total or 0) * SR)))
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def svf_bp(x, fc, q=2.0):
    """Chamberlin 狀態變數帶通；fc 可為隨時間變化嘅陣列（Hz，<7 kHz）"""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape); f = 2 * np.sin(np.pi * np.minimum(fc, 7000) / SR); q1 = 1.0 / q
    low = band = 0.0; y = np.empty_like(x)
    for i in range(len(x)):
        low += f[i] * band; high = x[i] - low - q1 * band; band += f[i] * high; y[i] = band
    return y
def nz(d): return rng.standard_normal(int(round(d * SR)))
def sweep(a, b, d): t = np.linspace(0, 1, int(round(d * SR))); return a * (b / a) ** t
def env(n, a=0.004, r=0.03, decay=0.0): return adsr(n, a, r, decay)
def sweep_noise(d, f0, f1, q=2.0, a=0.004, r=0.05, decay=0.0):
    x = svf_bp(nz(d), sweep(f0, f1, d), q); x = x / (np.std(x) + 1e-9); return x * env(len(x), a, r, decay)
def thud(f0, f1, d, decay=20, a=0.001):
    x = tt(d); f = f1 + (f0 - f1) * np.exp(-x * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * decay) * env(len(x), a, 0.01)
def grain(fc, d=0.012, q=2.0, a=0.0008):
    x = svf_bp(nz(d + 0.01), fc, q)[:int(d * SR)]; x = x / (np.std(x) + 1e-9); return x * env(len(x), a, d * 0.5, 40 / max(d, 0.01) * 0.3)
def tailfade(y, ms=6):
    n = int(ms / 1000 * SR); y = y.copy(); y[-n:] *= (np.linspace(1, 0, n) if y.ndim == 1 else np.linspace(1, 0, n)[:, None]); return y
def stereo_verb(x, wet=0.25, rt=1.0, tail=0.6, seed=5):
    """立體聲：左右唔同 IR；x 單聲道或 (n,2)"""
    r = np.random.default_rng(seed); n = len(x) + int(tail * SR); out = []
    for k in range(2):
        s = x if x.ndim == 1 else x[:, k]; ir = verb_ir(r, rt); sp = np.concatenate([s, np.zeros(n - len(s))])
        out.append((1 - wet) * sp + wet * fftconvolve(sp, ir)[:n])
    return np.stack(out, axis=1)
S = {}; ST = {}
G5, B5, D6, E6, G6, B6, D7, G7 = 79, 83, 86, 88, 91, 95, 98, 103
# ---- 換棒 ----
# 交棒者減速：下行風切（一下「咻」落）＋低音下滑＋起音 tick
S['sfx_baton_out'] = tailfade(mixs(sweep_noise(0.55, 1900, 320, q=1.6, a=0.004, r=0.2, decay=3.5) * 0.9,
                                   thud(260, 120, 0.45, decay=6) * 0.5, grain(3200, 0.006) * 0.6))
# 新人入場光尾：上行 whoosh（0.3 s 內到頂）＋閃光鐘聲尾（G–B–D–G 琶音）
bi = seq([(0, sweep_noise(0.36, 450, 4600, q=1.8, a=0.005, r=0.08, decay=0.0) * np.linspace(0.35, 1, int(.36 * SR)) ** 1.5, 0.9), (0, grain(3500, 0.005), 0.5)] +
         [(0.26 + i * 0.07, bell(mtof(m), 0.7, decay=9, a=0.002), 0.30 - 0.04 * i) for i, m in enumerate([G6, B6, D7, G7])] + [(0.0, bell(mtof(D6), 0.25, decay=14, a=0.002), 0.3)])
S['sfx_baton_in'] = tailfade(verb(bi, rng, wet=0.18, rt=0.5, tail=0.3)[:int(1.1 * SR)])
# ---- 技能 ----
# 蓄力 0.3 s：上行音高＋加速顫音＋上行氣流，尾端急收（接爆發）
d = 0.3; x = tt(d); f = sweep(220, 940, d); ph = 2 * np.pi * np.cumsum(f) / SR
trem = 1 - 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(sweep(14, 42, d)) / SR))
chg = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)) * trem * 0.5 + 0.45 * sweep_noise(d, 700, 3200, q=2.5, a=0.003, r=0.012)
S['sfx_skill_charge'] = tailfade(chg * np.linspace(0.5, 1, len(x)) ** 1.2 * env(len(x), 0.004, 0.012), 10)
# 疾風衝：爆發撞擊（低音 thump＋破風 crack）→ 大風掃過（頻率先升後降）→ 細小口哨
d = 1.15; n = int(round(d * SR)); tg = np.arange(n) / SR; fcw = 700 * (3400 / 700) ** np.clip(tg / 0.28, 0, 1) * (500 / 3400) ** np.clip((tg - 0.28) / 0.8, 0, 1)
wh = svf_bp(nz(d), fcw, 1.4); wh = wh / np.std(wh) * np.exp(-np.maximum(tg - 0.1, 0) * 3.2) * env(n, 0.005, 0.2)
air = svf_bp(nz(d), 5200, 1.2); air = air / np.std(air) * np.exp(-tg * 5) * env(n, 0.004, 0.2)
whistle = np.sin(2 * np.pi * np.cumsum(900 * (2.0 ** np.sin(np.pi * np.clip(tg / 0.9, 0, 1)))) / SR) * np.exp(-tg * 4)
bg = mixs(wh * 0.9, air * 0.12, 0.05 * whistle, np.pad(thud(160, 52, 0.4, decay=11) * 0.8, (0, n - int(.4 * SR))), np.pad(grain(2800, 0.02, 1.2) * 0.8, (0, n - int(.02 * SR))))
S['sfx_skill_burst_gale'] = tailfade(bg)
# 絆草：草叢沙沙（多粒短噪音）＋橡筋「繃」滑音＋絆倒悶響（0.38 s、0.5 s 兩下）
tg = seq([(0, grain(4200, 0.03, 1.8), 1.0), (0.03, grain(3200, 0.025, 1.8), 0.8), (0.07, grain(5200, 0.03, 1.8), 0.7), (0.11, grain(3600, 0.025, 1.8), 0.6),
          (0.16, grain(4600, 0.03, 1.8), 0.5), (0.21, grain(3000, 0.03, 1.8), 0.4), (0.26, grain(4000, 0.03, 1.8), 0.3),
          (0.02, glide(330, 190, 0.3, a=0.002, r=0.1, decay=9), 0.45), (0.02, glide(660, 380, 0.2, a=0.002, r=0.05, decay=14), 0.12),
          (0.38, thud(130, 62, 0.16, decay=18), 0.6), (0.38, grain(1200, 0.02, 1.2), 0.5), (0.5, thud(110, 55, 0.14, decay=22), 0.45)])
S['sfx_skill_trip_grass'] = tailfade(tg[:int(0.75 * SR)] if len(tg) > .75 * SR else tg)
# 回氣：輕柔吸氣＋暖和鈴聲上行＋柔和 pad
rc = seq([(0, bell(mtof(B5), 0.4, decay=8, a=0.002), 0.5)] +
         [(0.0, sweep_noise(0.5, 600, 2300, q=1.3, a=0.01, r=0.25, decay=0.0) * np.linspace(0.3, 1, int(.5 * SR)), 0.5)] +
         [(0.08 + i * 0.11, bell(mtof(m), 0.9, decay=5, a=0.002), 0.5 - 0.05 * i) for i, m in enumerate([G5, B5, D6, G6])] +
         [(0.0, mixs(*[softsine(mtof(m), 1.1, a=0.12, r=0.5, harm=(1, 2), amps=(1, .2)) for m in (55, 62, 67)]), 0.12)])
S['sfx_skill_recover'] = tailfade(verb(rc, rng, wet=0.25, rt=0.8, tail=0.3)[:int(1.3 * SR)])
# 風罩：升起「叮」＋旋轉風（6 Hz 掃頻＋顫幅）＋低哼＋遞減閃光
d = 1.45; n = int(round(d * SR)); tg = np.arange(n) / SR
sw = svf_bp(nz(d), 950 + 450 * np.sin(2 * np.pi * 6 * tg), 3.0); sw = sw / np.std(sw) * (0.65 + 0.35 * np.sin(2 * np.pi * 7 * tg + 1)) * env(n, 0.04, 0.5)
hum = (softsine(mtof(55), d, a=0.08, r=0.5, harm=(1, 2, 3), amps=(1, .35, .1))) * (1 + 0.02 * np.sin(2 * np.pi * 5 * tg))
ws = seq([(0, sw, 0.55), (0, hum, 0.25), (0, bell(mtof(D6), 0.5, decay=9, a=0.002), 0.5), (0, bell(mtof(G6), 0.5, decay=9, a=0.002), 0.35)] +
         [(0.15 + i * 0.17, bell(mtof(G6 + (i % 3) * 4), 0.35, decay=14, a=0.002), 0.2 * (1 - i / 8)) for i in range(7)], total=d)
S['sfx_skill_wind_shield'] = tailfade(ws[:n])
# 命中停頓：短促低音撞擊＋破裂 crack＋小「叮」（主體 ≈0.1 s，配合 2–4 幀停頓）
S['sfx_hit_stop_impact'] = tailfade(seq([(0, thud(210, 50, 0.32, decay=8), 0.7), (0, grain(2600, 0.03, 1.1), 0.6), (0, sweep_noise(0.11, 1400, 600, q=0.9, a=0.001, r=0.05, decay=18), 0.7),
                                         (0.012, bell(mtof(E6), 0.28, decay=14, a=0.001), 0.14)]))
# ---- 地形腳步（各一下，程式按步頻重複）----
S['sfx_step_moss'] = tailfade(seq([(0, thud(150, 70, 0.22, decay=13), 0.6), (0, sweep_noise(0.12, 520, 380, q=0.9, a=0.002, r=0.05, decay=22), 0.6),
                                   (0.015, grain(3200, 0.03, 1.5), 0.25), (0.045, grain(2600, 0.025, 1.5), 0.15)]))
S['sfx_step_gravel'] = tailfade(seq([(0, grain(float(rng.uniform(2500, 5800)), float(rng.uniform(.006, .014)), 2.0), float(rng.uniform(.4, 1.0))) for _ in range(1)] +
                                    [(float(t), grain(float(rng.uniform(2200, 6000)), float(rng.uniform(.006, .014)), 2.0), float(rng.uniform(.35, .9))) for t in np.sort(rng.uniform(0.002, 0.11, 9))] +
                                    [(float(t), grain(float(rng.uniform(2200, 5500)), 0.008, 2.0), float(rng.uniform(.1, .3))) for t in np.sort(rng.uniform(0.12, 0.26, 4))] +
                                    [(0, thud(125, 68, 0.2, decay=16), 0.55), (0, sweep_noise(0.1, 900, 600, q=0.9, a=0.002, r=0.04, decay=26), 0.35)]))
wt = seq([(0, thud(160, 85, 0.25, decay=12), 0.45), (0, sweep_noise(0.3, 1900, 900, q=1.2, a=0.0015, r=0.12, decay=8), 1.0), (0, grain(4000, 0.01, 1.5), 0.4)] +
         [(float(t), glide(f, f * 2.3, 0.07, a=0.003, r=0.02, decay=28), float(g)) for t, f, g in zip([0.05, 0.12, 0.19, 0.27, 0.33], rng.uniform(750, 1700, 5), [.28, .22, .2, .14, .1])] +
         [(float(t), grain(float(rng.uniform(3000, 5500)), 0.012, 1.8), 0.22) for t in np.sort(rng.uniform(0.06, 0.3, 4))])
S['sfx_step_shallow_water'] = tailfade(wt[:int(0.55 * SR)])
# ---- 起跑 GO（倒數最後一下）----
go = seq([(0, grain(3000, 0.012, 1.2), 0.6), (0, sweep_noise(0.3, 900, 3800, q=1.8, a=0.003, r=0.1, decay=5), 0.5)] +
         [(0, bell(mtof(m), 0.9, decay=5, a=0.002), g) for m, g in ((G5, .9), (D6, .8), (G6, .7), (B6, .35))] +
         [(0, gpluck(mtof(m), 0.5, 7), 0.5) for m in (67, 71, 74)] + [(0, thud(150, 60, 0.2, decay=14), 0.6)])
S['sfx_countdown_go'] = tailfade(verb(go, rng, wet=0.15, rt=0.4, tail=0.2)[:int(0.9 * SR)])
# ================= Stinger（立體聲）=================
def lr(parts, total):
    """parts: (t, mono, gain, pan)"""
    L = np.zeros(int(total * SR)); R = np.zeros_like(L)
    for t, x, g, p in parts:
        th = (p + 1) * np.pi / 4; place(L, t, x, g * np.cos(th)); place(R, t, x, g * np.sin(th))
    return np.stack([L, R], axis=1)
# 衝線：t=0 即時「布帶斷開」snap＋光亮和弦＋低音撞擊，之後氣流下行同閃光瀑布
fl = lr([(0, grain(3400, 0.014, 1.2), .7, 0), (0, thud(150, 55, 0.4, decay=10), .8, 0), (0, sweep_noise(0.7, 4200, 700, q=1.5, a=0.003, r=0.3, decay=3.5), .45, 0)] +
        [(0, bell(mtof(m), 1.6, decay=3.6, a=0.002), g, p) for m, g, p in ((G5, .6, -.3), (B5, .5, .3), (D6, .5, -.15), (G6, .5, .15))] +
        [(0.12 + i * 0.075, bell(mtof(m), 0.8, decay=7, a=0.002), 0.2 - 0.012 * i, (-1) ** i * .6) for i, m in enumerate([D7, B6, G6, D7, B6, G6, D6, B5])], 1.8)
ST['sfx_finish_line'] = tailfade(stereo_verb(fl, wet=0.22, rt=0.9, tail=0.8)[:int(1.8 * SR)], 20)
# 勝利：三連短音（D6）→ 長音 G6，上行琶音閃光＋亮和弦（G add9）；鐘＋撥弦＋笛，低音鼓點
W = [(0, bell(mtof(D6), 0.5, decay=7, a=0.002), .55, -.2), (0.14, bell(mtof(D6), 0.5, decay=7, a=0.002), .55, .2), (0.28, bell(mtof(D6), 0.5, decay=7, a=0.002), .55, -.2),
     (0, gpluck(mtof(74), 0.4, 6), .5, -.3), (0.14, gpluck(mtof(74), 0.4, 6), .5, .3), (0.28, gpluck(mtof(74), 0.4, 6), .5, -.3),
     (0.42, flute(mtof(G6), 1.5, rng), .45, 0.1), (0.42, bell(mtof(G6), 2.0, decay=2.6, a=0.002), .55, .1), (0.42, gpluck(mtof(79), 1.0, 3), .5, -.2),
     (0.42, mixs(*[softsine(mtof(m), 2.0, a=0.05, r=0.9, harm=(1, 2, 3), amps=(1, .3, .08)) for m in (55, 62, 67, 71, 74)]), .09, 0),
     (0, thud(140, 58, 0.3, decay=11), .6, 0), (0.42, thud(140, 58, 0.35, decay=9), .7, 0)]
W += [(0.62 + i * 0.07, bell(mtof(m), 0.9, decay=6, a=0.002), 0.28 - 0.015 * i, (-1) ** i * .65) for i, m in enumerate([G6, B6, D7, G7, D7, B6, G6, B5][:8])]
ST['sfx_stinger_win'] = tailfade(stereo_verb(lr(W, 2.4), wet=0.26, rt=1.2, tail=1.2)[:int(2.8 * SR)], 30)
# 失敗：溫柔鼓勵——柔笛輕輕下行（D–B–A）再抬頭上行（B–D–G），最後 G add9 暖和弦＋細小鈴光；全程柔和，無低音鼓
LS = [(0.00, flute(mtof(74), 0.55, rng), .35, -.1), (0.42, flute(mtof(71), 0.55, rng), .33, .1), (0.84, flute(mtof(69), 0.6, rng), .30, -.1),
      (1.30, flute(mtof(71), 0.35, rng), .32, .1), (1.58, flute(mtof(74), 0.35, rng), .34, -.1), (1.86, flute(mtof(79), 1.0, rng), .42, 0),
      (1.86, bell(mtof(G6), 1.2, decay=3.5, a=0.003), .30, .2), (1.86, mixs(*[softsine(mtof(m), 1.5, a=0.15, r=0.8, harm=(1, 2), amps=(1, .25)) for m in (55, 62, 66 + 3 + 0, 69)]), .10, 0)]
LS += [(0.0, bell(mtof(86), 0.9, decay=5, a=0.003), .12, .4), (0.84, gpluck(mtof(57), 0.9, 4), .22, -.4), (1.30, gpluck(mtof(59), 0.7, 4), .2, .4), (0.0, gpluck(mtof(62), 0.9, 4), .2, -.4)]
LS += [(2.05 + i * 0.12, bell(mtof(m), 0.7, decay=6, a=0.002), 0.14 - 0.02 * i, (-1) ** i * .6) for i, m in enumerate([D6, G6, B6, D7])]
ST['sfx_stinger_lose'] = tailfade(stereo_verb(lr(LS, 2.6), wet=0.3, rt=1.3, tail=1.3)[:int(3.0 * SR)], 200)
for k, v in {**S, **ST}.items():
    v = np.nan_to_num(v); sf.write(f'tmp/{k}.wav', v, SR, subtype='FLOAT'); print(k, round(len(v) / SR, 3), 's', v.shape)
