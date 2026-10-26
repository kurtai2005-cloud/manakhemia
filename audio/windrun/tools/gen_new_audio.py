"""《風野競走》cue 表新增音訊（P1／P2，共 7 個）— 原創程式合成（numpy/scipy），無取樣、無第三方素材。
  P1：stinger_entry（隊伍介紹入場，≈3 s 立體聲）、sfx_countdown_tick（倒數，0.18 s 單聲道）、jingle_capture（結緣成功，≈2 s 立體聲）
  P2：jingle_levelup（≈1.2 s 立體聲）、sfx_stamina_warn、sfx_stamina_empty（≤0.5 s 單聲道）、amb_wind_title（18 s 無縫循環環境風聲，立體聲）
輸出 tmp_new/<name>.wav（float，未標準化；之後 norm_new.py 設響度、encode_new.py 編碼）。固定亂數種子，可重現。
同賽中素材：G 大調、溫暖柔和；stinger 沿用 128 BPM 拍子（一拍 0.46875 s）。"""
import os, numpy as np, soundfile as sf
from scipy.signal import butter, lfilter
from dsp import *
from gen_bgm_race import flute, gpluck
OUT = 'tmp_new'; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(20261101)
G4, B4, D5, E5, Fs5, G5, A5, B5, D6, E6, Fs6, G6, A6, B6, D7, E7, G7 = 67, 71, 74, 76, 78, 79, 81, 83, 86, 88, 90, 91, 93, 95, 98, 100, 103
BEAT = 60 / 128.0                                  # 0.46875 s（賽中 BGM 一拍）
def mixs(*a):
    y = np.zeros(max(len(x) for x in a))
    for x in a: y[:len(x)] += x
    return y
def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def nz(d): return rng.standard_normal(int(round(d * SR)))
def nrm(x): return x / (np.std(x) + 1e-9)
def tailfade(y, ms=6):
    n = int(ms / 1000 * SR); y = y.copy(); y[-n:] *= (np.linspace(1, 0, n) if y.ndim == 1 else np.linspace(1, 0, n)[:, None]); return y
def thud(f0, f1, d, decay=20, a=0.001, k=30):
    x = tt(d); f = f1 + (f0 - f1) * np.exp(-x * k); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * decay) * adsr(len(x), a, 0.01)
def grain(fc, d=0.012, q=(0.6, 1.0), decay=60, a=0.0008):
    n = nrm(bp(nz(d + 0.02), fc * q[0], fc * q[1]))[:int(d * SR)]; return n * np.exp(-tt(d) * decay) * adsr(len(n), a, d * 0.4)
def sweep_noise(d, f0, f1, lo_q=0.7, hi_q=1.4, a=0.004, r=0.05, decay=0.0, steps=24):
    """頻率隨時間變化嘅帶通噪音（分段濾波＋交叉相接，唔需要狀態變數濾波器）"""
    n = int(round(d * SR)); y = np.zeros(n); src = nz(d + 0.2); edges = np.linspace(0, n, steps + 1).astype(int)
    for i in range(steps):
        fc = f0 * (f1 / f0) ** ((i + .5) / steps); seg = bp(src, fc * lo_q, min(fc * hi_q, 20000))[:n]
        w = np.zeros(n); lo, hi = edges[i], edges[i + 1]; ov = (hi - lo)
        w[max(0, lo - ov // 2):min(n, hi + ov // 2)] = np.hanning(min(n, hi + ov // 2) - max(0, lo - ov // 2))
        y += seg * w
    return nrm(y) * adsr(n, a, r, decay)
def seq(parts, total=0):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(max(L, int(total * SR)))
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def lr(parts, total):
    """parts: (t, mono, gain, pan)"""
    L = np.zeros(int(total * SR)); R = np.zeros_like(L)
    for t, x, g, p in parts:
        th = (p + 1) * np.pi / 4; place(L, t, x, g * np.cos(th)); place(R, t, x, g * np.sin(th))
    return np.stack([L, R], axis=1)
def stereo_verb(x, wet=0.25, rt=1.0, tail=0.6, seed=5):
    r = np.random.default_rng(seed); n = len(x) + int(tail * SR); out = []
    for k in range(2):
        s = x[:, k]; ir = verb_ir(r, rt); sp = np.concatenate([s, np.zeros(n - len(s))])
        out.append((1 - wet) * sp + wet * fftconvolve(sp, ir)[:n])
    return np.stack(out, axis=1)
def horn(f, d, a=0.03, r=0.18, decay=0.0, br=1.0):
    """柔和號角式：1–4 次諧波，低通 2.6 kHz，輕微顫音（唔刺耳）"""
    x = tt(d); vib = 0.003 * np.minimum(1, x / 0.2) * np.sin(2 * np.pi * 5.0 * x); ph = 2 * np.pi * np.cumsum(f * (1 + vib)) / SR
    y = np.sin(ph) + 0.5 * br * np.sin(2 * ph) + 0.22 * br * np.sin(3 * ph) + 0.08 * br * np.sin(4 * ph)
    return lp(y, 2600) * adsr(len(x), a, r, decay)
def pad(notes, d, a=0.2, r=0.5):
    return mixs(*[softsine(mtof(m), d, a=a, r=r, harm=(1, 2, 3), amps=(1, .25, .06)) for m in notes])
S = {}
# ================= P1 stinger_entry：隊伍介紹入場，≈3.0 s，128 BPM，G 大調，結尾停喺 D（V）等遊戲接 =================
b = BEAT; T = 3.0
P = []
# 小節 1（0–1.875 s）：G，拾音式上行號角節奏；小鼓輕滾由第 3 拍起漸強（16 分），向第 2 小節重拍推進
mel = [(0, D5, .5), (.5, G5, .5), (1, B5, 1), (2, D6, .75), (2.75, B5, .25), (3, D6, 1)]
for bt, m, ln in mel:
    t = bt * b
    P += [(t, horn(mtof(m), ln * b * 0.95 + .12, a=.025, r=.15), .38, -.15 + 0.1 * (m % 3 - 1)), (t, gpluck(mtof(m + 12 if m < G6 - 12 else m), .5, 5), .20, .25)]
P += [(0, thud(130, 50, .35, decay=10), .55, 0), (2 * b, thud(120, 52, .3, decay=12), .30, 0)]               # 柔和大鼓（第 1、3 拍）
for i in range(8):                                                                                         # 小鼓輕滾（第 3 拍起 16 分，漸強）
    t = 2 * b + i * b / 4 * 1.0; g = 0.10 + 0.16 * (i / 7)
    P += [(t, nrm(bp(nz(.09), 1200, 5200)) * np.exp(-tt(.09) * 40) * adsr(int(.09 * SR), .001, .02), g, ((-1) ** i) * 0.25)]
for i in range(4):                                                                                         # 第 4 拍：4 個 16 分上行鐘光
    P += [(3 * b + i * b / 4, bell(mtof([G5, B5, D6, G6][i]), .5, decay=8, a=.002), .20 + .03 * i, ((-1) ** i) * .5)]
P += [(0, pad([43, 50, 55, 59], 2.1, a=.55, r=.3), .08, 0), (0, sweep_noise(1.8, 500, 2400, a=.9, r=.12), .05, 0)]   # 氣墊 swell＋上行風聲
# 小節 2（1.875 s＝第 2 小節重拍）：D 大（V，帶 add9 E）亮和弦＋鐘頭，未解決，之後自然淡出（留位）
t2 = 4 * b
P += [(t2, horn(mtof(81), 1.05, a=.02, r=.5, decay=1.2), .34, -.12), (t2, horn(mtof(Fs5 + 12), 1.0, a=.02, r=.5, decay=1.3), .22, .15), (t2, horn(mtof(D5), 1.0, a=.02, r=.5, decay=1.3), .2, .0),
      (t2, bell(mtof(A6), 1.0, decay=3.2, a=.002), .22, .3), (t2, bell(mtof(D6), 1.0, decay=3.2, a=.002), .26, -.3), (t2, gpluck(mtof(62), .9, 3), .30, -.3),
      (t2, thud(140, 55, .4, decay=8), .60, 0), (t2, grain(3200, .02, decay=90), .25, 0),
      (t2, pad([50, 57, 62, 66, 76], 1.1, a=.04, r=.7), .10, 0)]
P += [(t2 + .30 + i * .085, bell(mtof([E6, Fs6, A6, B6, D7, A6, Fs6][i]), .6, decay=7, a=.002), .13 - .012 * i, ((-1) ** i) * .65) for i in range(7)]   # 尾段閃光瀑布
y = lr(P, T + 1.0)
y = stereo_verb(y, wet=0.24, rt=1.0, tail=0.3)[:int(T * SR)]
S['stinger_entry'] = tailfade(y, 180)
# ================= P1 sfx_countdown_tick：D5（587.3 Hz）＝GO 和弦入面嘅 D5 撥弦、低過 GO 嘅 G5/G6 頂音；0.18 s =================
d = 0.18; x = tt(d); fD = mtof(D5)
tk = (np.sin(2 * np.pi * fD * x) + .32 * np.sin(2 * np.pi * fD * 2 * x) + .08 * np.sin(2 * np.pi * fD * 3.01 * x)) * np.exp(-x * 24) * adsr(len(x), .0015, .02)
tk = seq([(0, tk, 1.0), (0, grain(1500, .012, q=(.6, 1.0), decay=160), .22), (0, thud(190, 100, .08, decay=45), .14)])[:int(d * SR)]
S['sfx_countdown_tick'] = tailfade(tk, 20)
# ================= P1 jingle_capture：結緣成功，≈2.0 s，溫暖魔法，葉片閃光 =================
T = 2.0; P = []
P += [(0.00, pad([43, 50, 55, 59, 66], 2.3, a=.5, r=.9), .10, 0), (0.00, sweep_noise(.5, 700, 3600, a=.2, r=.2), .06, .0)]  # 輕吸氣式 swell
arp = [G4, D5, G5, B5, D6]                                                                               # 快速撥弦琶音（豎琴感）
P += [(i * .065, gpluck(mtof(m), .9, 3.2), .30 - .02 * i, -.5 + .25 * i) for i, m in enumerate(arp)]
P += [(i * .065, bell(mtof(m + 12), .6, decay=6, a=.002), .12, -.5 + .25 * i) for i, m in enumerate(arp[2:])]
mel = [(0.30, B5, .38), (0.62, D6, .38), (0.94, G6, 1.15)]                                                # 簡單情感旋律：B–D–G 上行
for t, m, ln in mel:
    P += [(t, flute(mtof(m), ln, rng), .36 if m != G6 else .42, .1), (t, bell(mtof(m), ln + .3, decay=4.0, a=.003), .26, -.1)]
P += [(0.94, bell(mtof(Fs6), 1.0, decay=5.0, a=.003), .13, .3), (0.94, bell(mtof(B6), 1.0, decay=5.5, a=.003), .09, -.3), (0.94, bell(mtof(A6), .9, decay=6, a=.003), .08, .4)]  # maj9/maj7 柔和閃光
P += [(0.94, thud(110, 52, .4, decay=9), .30, 0)]
spk = [E7, G7, D7, B6, A6, E7, G7, D7, B6, Fs6, D7, B6]                                                    # 葉片閃光：疏落五聲高音，漸疏漸細
for i, m in enumerate(spk):
    t = 0.45 + i * 0.105 + float(rng.uniform(-.02, .02)); P += [(t, bell(mtof(m), .4, decay=11, a=.001), .10 * (1 - i / 14), float(rng.uniform(-.8, .8)))]
for i in range(9):                                                                                         # 葉沙沙：高頻細粒
    t = 0.12 + i * 0.16 + float(rng.uniform(-.03, .03)); P += [(t, grain(float(rng.uniform(3500, 6500)), .03, q=(.6, 1.0), decay=60), .07 * (1 - i / 11), float(rng.uniform(-.9, .9)))]
y = lr(P, T + .9); y = stereo_verb(y, wet=0.28, rt=1.1, tail=0.3, seed=9)[:int(T * SR)]
S['jingle_capture'] = tailfade(y, 220)
# ================= P2 jingle_levelup：≈1.2 s，亮、輕快上行 =================
T = 1.2; P = []
P += [(0.00, bell(mtof(D6), .35, decay=9, a=.002), .38, -.3), (0.00, gpluck(mtof(D5), .4, 6), .30, -.3),
      (0.09, bell(mtof(E6), .35, decay=9, a=.002), .38, .3), (0.09, gpluck(mtof(E5), .4, 6), .30, .3)]                # 拾音 D–E
t1 = 0.20
P += [(t1, bell(mtof(G6), 1.0, decay=3.4, a=.002), .52, 0), (t1, flute(mtof(G5), .9, rng), .30, -.1), (t1, gpluck(mtof(G5), .8, 4), .38, .2),
      (t1, bell(mtof(B6), .9, decay=4.2, a=.002), .22, -.3), (t1, bell(mtof(D6), 1.0, decay=3.6, a=.002), .30, .3), (t1, gpluck(mtof(B5), .7, 5), .28, -.2),
      (t1, thud(130, 55, .3, decay=11), .46, 0), (t1, pad([43, 55, 59, 62, 69], 1.0, a=.04, r=.5), .12, 0)]
P += [(t1 + .13 + i * .07, bell(mtof(m), .5, decay=8, a=.002), .20 - .02 * i, ((-1) ** i) * .6) for i, m in enumerate([D7, B6, E7, G7, D7])]   # 閃光上行
y = lr(P, T + .6); y = stereo_verb(y, wet=0.22, rt=.7, tail=.2, seed=11)[:int(T * SR)]
S['jingle_levelup'] = tailfade(y, 150)
# ================= P2 sfx_stamina_warn：柔和低頻心跳式單下，0.40 s =================
# 手機喇叭放唔到 <100 Hz，所以主體放喺約 70–130 Hz，再加 2–4 次諧波（≈140–280 Hz）令細喇叭都聽到「咚」；全部低通 650 Hz，冇 click
d = 0.40; x = tt(d)
th = thud(125, 70, d, decay=10.0, a=0.006, k=26)                                                          # 圓潤悶「咚」
th2 = (np.sin(2 * np.pi * 140 * x) * 0.55 + np.sin(2 * np.pi * 210 * x) * 0.32 + np.sin(2 * np.pi * 280 * x) * 0.12) * np.exp(-x * 15) * adsr(len(x), .006, .02)
body = lp(nz(d), 420) * np.exp(-x * 28) * adsr(len(x), .004, .02) * .12
S['sfx_stamina_warn'] = tailfade(lp(mixs(th, th2, body), 650), 25)
# ================= P2 sfx_stamina_empty：更重、疲憊嘅低沉嘆息＋悶撞，0.48 s =================
d = 0.48; x = tt(d)
th = thud(100, 52, d, decay=8.0, a=0.005, k=22)
th_h = (np.sin(2 * np.pi * 104 * x) * .55 + np.sin(2 * np.pi * 156 * x) * .30 + np.sin(2 * np.pi * 208 * x) * .12) * np.exp(-x * 11) * adsr(len(x), .005, .02)
th2 = np.zeros(len(x)); place(th2, 0.20, thud(86, 48, .26, decay=12, a=.006, k=20), .55)                     # 第二下拖沓嘅低沉落地
sg = sweep_noise(d, 950, 300, lo_q=.6, hi_q=1.5, a=.04, r=.2, decay=5.0) * np.linspace(.9, .4, len(x)) * .55      # 嘆息氣流（向下）
vc = np.sin(2 * np.pi * np.cumsum(260 * (190 / 260) ** (x / d)) / SR); vc = (vc + .35 * np.sin(2 * np.pi * np.cumsum(520 * (380 / 520) ** (x / d)) / SR)) * adsr(len(x), .05, .2, 3.0) * .22
S['sfx_stamina_empty'] = tailfade(lp(mixs(th, th_h, th2, sg, vc), 1800), 30)
# ================= P2 amb_wind_title：標題風聲環境，18.000 s（793,800 samples）無縫循環，立體聲 =================
LOOP = 18.0; N = int(round(LOOP * SR)); assert N == 793800
def circ_noise():
    return rng.standard_normal(N)
def circ_filter(x, shape):
    """FFT 圓周濾波：shape(f) 為各頻率增益；結果天然首尾相接"""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(N, 1 / SR); return np.fft.irfft(X * shape(f), N)
def circ_env(lo_hz, hi_hz, depth, base=1.0):
    """慢變化包絡：圓周帶通噪音 → 0.5 + …；周期＝循環長度，無接縫"""
    e = circ_filter(circ_noise(), lambda f: ((f > lo_hz) & (f < hi_hz)).astype(float)); e = e / (np.std(e) + 1e-9)
    return np.clip(base + depth * e, 0.05, None)
def wind_ch(seed_off):
    y = np.zeros(N)
    bands = [(90, 260, 1.0, .06, .22), (220, 600, 0.9, .05, .25), (500, 1400, .55, .07, .30), (1100, 2600, .22, .09, .35), (2200, 4200, .05, .10, .4)]
    for lo, hi, g, e_lo, e_hi in bands:
        w = circ_filter(circ_noise(), lambda f, lo=lo, hi=hi: np.exp(-0.5 * (np.log(np.maximum(f, 1) / np.sqrt(lo * hi)) / (np.log(hi / lo) / 2.2)) ** 2))
        y += g * nrm(w) * circ_env(0.02, 0.35, 0.28)               # 各頻段獨立慢起伏（陣風）
    # 全局陣風：整數周期（1、2、3 周期／18 s）
    t = np.arange(N) / N
    gust = 1 + 0.18 * np.sin(2 * np.pi * (1 * t + rng.uniform())) + 0.10 * np.sin(2 * np.pi * (2 * t + rng.uniform())) + 0.06 * np.sin(2 * np.pi * (3 * t + rng.uniform()))
    return y * gust
L = wind_ch(0); R = wind_ch(1)
mid = 0.3 * (L + R) / 2; L = L * .85 + mid; R = R * .85 + mid                       # 輕度相關，寬但唔空洞
def shimmer(freqs, amps):
    """微弱音調閃光：G 大調音（G5、D6、B5、G6…），頻率取 k/18 Hz 令整數周期落入循環；振幅用整數周期慢包絡；左右微失諧"""
    out = [np.zeros(N), np.zeros(N)]; t = np.arange(N) / SR
    for f, a in zip(freqs, amps):
        for ch, det in ((0, 0.9985), (1, 1.0015)):
            k = round(f * det * LOOP); fr = k / LOOP; ph = rng.uniform(0, 2 * np.pi)
            c1, c2 = int(rng.integers(1, 4)), int(rng.integers(2, 6)); p1, p2 = rng.uniform(0, 6.28, 2)
            am = np.clip(0.55 + 0.45 * np.sin(2 * np.pi * c1 * t / LOOP + p1) * 0.7 + 0.3 * np.sin(2 * np.pi * c2 * t / LOOP + p2), 0, None) ** 2
            out[ch] += a * np.sin(2 * np.pi * fr * t + ph) * am
    return out
sl, sr_ = shimmer([mtof(G5), mtof(D6), mtof(B5), mtof(G6)], [1.0, .7, .5, .25])
Lw = nrm(L); Rw = nrm(R)
yL = Lw + 0.0075 * nrm(sl) * 1.0; yR = Rw + 0.0075 * nrm(sr_) * 1.0          # 閃光約低過風聲 -42 dB（頻帶內較突出）
S['amb_wind_title'] = np.stack([yL, yR], axis=1)
for k, v in S.items():
    v = np.nan_to_num(v); sf.write(f'{OUT}/{k}.wav', v, SR, subtype='FLOAT'); print(k, round(len(v) / SR, 3), 's', v.shape)
