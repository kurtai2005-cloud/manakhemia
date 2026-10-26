"""《風野競走》晨苔鎮／冒險層 SFX（腳步 9、對話 blip 3、對話／互動／選單／報名／拾取／換區 12，共 24 個）— 原創程式合成（numpy/scipy），無取樣。
輸出 tmp/sfx_<name>.wav（float，單聲道，未標準化；之後由 norm_town.py 設響度、encode_sfx.py 編碼）。固定亂數種子，可重現。
設計：起音 ≤10 ms（音畫同步）；頻密音（腳步、blip、menu_move）細聲、少高頻、唔刺耳。"""
import os, numpy as np, soundfile as sf
from scipy.signal import butter, lfilter, sosfilt, sosfilt_zi
from dsp import *
os.makedirs('tmp', exist_ok=True)
def N_(d): return len(tt(d))
def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2)); return lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def nrm(x): return x / (np.std(x) + 1e-9)
def env(n, a=0.004, r=0.03, decay=0.0): return adsr(n, a, r, decay)
def fade_end(y, ms=5): n = int(ms / 1000 * SR); y = y.copy(); y[-n:] *= np.linspace(1, 0, n); return y
def thud(f0, f1, d, decay=30, a=0.001, k=30):
    x = tt(d); f = f1 + (f0 - f1) * np.exp(-x * k); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * decay) * env(len(x), a, 0.01)
def tick(rng, fc, d=0.02, q=(0.6, 1.0), decay=140):
    n = nrm(bp(rng.standard_normal(N_(d) + 400), fc * q[0], fc * q[1]))[:N_(d)]; return n * np.exp(-tt(d) * decay) * env(len(n), 0.0005, 0.004)
def mode(f, d, decay, a=0.0008): x = tt(d); return np.sin(2 * np.pi * f * x) * np.exp(-x * decay) * env(len(x), a, 0.01)
def seq(parts, total=0):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(max(L, int(total * SR)))
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
OUT = {}
def save(name, y): OUT[name] = np.asarray(y, float)
# ---------- 腳步（每個 3 變體：音高／亮度／雙腳間距／碎粒位置微變）----------
VAR = {'a': dict(p=1.00, br=1.00, gap=0.060, s=1), 'b': dict(p=0.91, br=0.88, gap=0.068, s=2), 'c': dict(p=1.09, br=1.12, gap=0.054, s=3)}
def step_cobble(v):
    r = np.random.default_rng(1000 + v['s']); p = v['p']; br = v['br']
    heel = seq([(0, thud(120 * p, 70 * p, 0.12, 38), 0.55), (0, tick(r, 2300 * p * br, 0.022, decay=110), 0.50), (0.001, mode(780 * p, 0.05, 70), 0.16)])
    toe = seq([(0, thud(140 * p, 85 * p, 0.09, 50), 0.28), (0, tick(r, 3000 * p * br, 0.016, decay=150), 0.26)])
    return fade_end(lp(seq([(0, heel), (v['gap'], toe, 0.8)], 0.17), 5500))
def step_grass(v):
    r = np.random.default_rng(2000 + v['s']); p = v['p']; br = v['br']; d = 0.2
    x = tt(d); sw = nrm(bp(r.standard_normal(len(x)), 900 * p * br, 3800 * br)) * (np.exp(-x * 17) * np.minimum(1, x / 0.012))
    y = np.zeros(len(x)); place(y, 0, sw, 0.55); place(y, 0, thud(95 * p, 62 * p, 0.12, 35), 0.38)
    for k in range(3): place(y, r.uniform(0.012, 0.09), tick(r, r.uniform(2400, 4200) * br, 0.012, decay=220), r.uniform(.12, .24))
    place(y, v['gap'] + 0.01, nrm(bp(r.standard_normal(N_(0.09)), 1000 * p, 3200)) * np.exp(-tt(0.09) * 25) * np.minimum(1, tt(0.09) / 0.01), 0.22)
    return fade_end(lp(y, 5200))
def step_wood(v):
    r = np.random.default_rng(3000 + v['s']); p = v['p']; br = v['br']
    def knock(g):
        return g * seq([(0, thud(205 * p, 125 * p, 0.14, 26, k=45), 0.55), (0, mode(310 * p, 0.12, 38), 0.26), (0, mode(545 * p * 1.03, 0.09, 55), 0.12), (0, mode(930 * p, 0.05, 90), 0.05 * br),
                        (0, tick(r, 1700 * br, 0.014, decay=170), 0.18)])
    return fade_end(lp(seq([(0, knock(1.0)), (v['gap'] + 0.01, knock(0.45))], 0.2), 4500))
for nm, fn in (('step_town_cobble', step_cobble), ('step_grass_path', step_grass), ('step_wood_floor', step_wood)):
    for k, v in VAR.items(): save(f'sfx_{nm}_{k}', fn(v))
# ---------- 對話 blip（≤0.06 s；3 個說話者音高）----------
def blip(f, h2, h3, bend, d=0.055):
    x = tt(d); fr = f * (1 + bend * np.exp(-x * 70)); ph = 2 * np.pi * np.cumsum(fr) / SR
    y = np.sin(ph) + h2 * np.sin(2 * ph + 0.6) + h3 * np.sin(3 * ph)
    e = np.minimum(1, x / 0.004) * np.exp(-x * 26); e[-N_(0.012):] *= np.linspace(1, 0, N_(0.012)); return y * e
save('sfx_dialog_blip_a', blip(174.6, 0.45, 0.12, 0.05))     # F3：低、暖（長者／村長）
save('sfx_dialog_blip_b', blip(293.7, 0.30, 0.08, 0.04))     # D4：中（主角／一般 NPC）
save('sfx_dialog_blip_c', blip(440.0, 0.22, 0.05, 0.06))     # A4：高、輕（年輕／店員）
# ---------- 對話框／互動／選單 ----------
def pl(f, d=0.5, decay=6, amp=1.0): return amp * (0.6 * bell(f, d, decay=decay, a=0.002, r=0.04) + 0.4 * pluck(f, d, decay=decay * 0.6))
save('sfx_dialog_open', fade_end(lp(seq([(0, pl(mtof(79), 0.3, 11), 0.8), (0.06, pl(mtof(86), 0.3, 11), 0.65)]), 6000)))      # G5→D6 輕上行
save('sfx_dialog_next', fade_end(lp(pl(mtof(88), 0.11, 22), 5500)))                                                         # E6 極短 tick
save('sfx_dialog_close', fade_end(lp(seq([(0, pl(mtof(86), 0.3, 11), 0.7), (0.06, pl(mtof(79), 0.3, 11), 0.8)]), 6000)))     # D6→G5 輕下行
save('sfx_interact_confirm', fade_end(lp(seq([(0, pl(mtof(83), 0.3, 12), 0.7), (0.07, pl(mtof(88), 0.4, 10), 0.9)]), 6500)))   # B5→E6
def door():
    r = np.random.default_rng(4001)
    latch = seq([(0, tick(r, 1400, 0.012, decay=200), 0.5), (0.002, mode(240, 0.05, 60), 0.35)])
    cx = tt(0.36); fc = 260 + 90 * np.sin(np.pi * cx / 0.36) + 40 * np.sin(2 * np.pi * 17 * cx)
    creak = np.sin(2 * np.pi * np.cumsum(fc) / SR) * (1 + 0.5 * np.sin(2 * np.pi * 31 * cx)) * np.sin(np.pi * cx / 0.36) ** 2
    creak = lp(creak + 0.5 * np.sin(4 * np.pi * np.cumsum(fc * 1.01) / SR), 1100)
    close = seq([(0, thud(150, 70, 0.2, 18), 0.9), (0, nrm(lp(r.standard_normal(N_(0.1)), 900)) * np.exp(-tt(0.1) * 45), 0.25)])
    return fade_end(lp(seq([(0, latch), (0.05, creak, 0.28), (0.4, close, 0.6)], 0.62), 4500))
save('sfx_interact_door', door())
def menu_move():
    x = tt(0.06); return fade_end(lp(np.sin(2 * np.pi * 740 * x) * np.exp(-x * 60) * np.minimum(1, x / 0.002) + 0.2 * np.sin(2 * np.pi * 1480 * x) * np.exp(-x * 110), 4000), 4)
save('sfx_menu_move', menu_move())
# ---------- 報名處 ----------
def reg_open():
    r = np.random.default_rng(5001)
    ding = sum(a * np.sin(2 * np.pi * f * tt(0.7)) * np.exp(-tt(0.7) * dk) for f, a, dk in [(1568, 1.0, 6), (1568 * 2.76, 0.25, 11), (1568 * 5.4, 0.06, 20)]) * env(N_(0.7), 0.001, 0.05)
    paper = nrm(bp(r.standard_normal(N_(0.28)), 1500, 4500)) * np.exp(-tt(0.28) * 11) * (0.5 + 0.5 * np.sin(2 * np.pi * 19 * tt(0.28) + 1)) ** 2 * np.minimum(1, tt(0.28) / 0.01)
    wood = mode(190, 0.1, 40) * 0.5
    return fade_end(lp(verb(seq([(0, wood, 0.5), (0.0, paper, 0.12), (0.09, ding, 0.5)]), np.random.default_rng(5002), wet=0.18, rt=0.5, tail=0.2), 6000))
save('sfx_register_open', reg_open())
def reg_confirm():     # 報名成功 ≤1.5 s：G 大調上行琶音（G5 B5 D6 G6）＋ add9 長音 + 閃光
    notes = [(0, 79), (0.11, 83), (0.22, 86), (0.33, 91)]
    parts = [(t, pl(mtof(m), 0.9, 6), 0.55 + 0.1 * i) for i, (t, m) in enumerate(notes)]
    parts += [(0.33, pl(mtof(m), 1.0, 5), 0.35) for m in (79, 83, 86)] + [(0.33, pl(mtof(93), 0.8, 7), 0.18), (0.50, bell(mtof(98), 0.6, decay=9), 0.06), (0.62, bell(mtof(95), 0.6, decay=9), 0.05)]
    y = verb(seq(parts), np.random.default_rng(5003), wet=0.2, rt=0.7, tail=0.35)[:N_(1.3)]; return fade_end(lp(y, 6500), 30)
save('sfx_register_confirm', reg_confirm())
def reg_denied():      # 溫和：兩下柔和下行（E5→A4）；圓潤正弦
    def soft(f, d): x = tt(d); return (np.sin(2 * np.pi * f * x) + 0.18 * np.sin(4 * np.pi * f * x)) * np.minimum(1, x / 0.008) * np.exp(-x * 9) * env(len(x), 0.008, 0.06)
    y = seq([(0, soft(mtof(76), 0.28), 0.8), (0.0, mode(300, 0.06, 50), 0.1), (0.17, soft(mtof(69), 0.4), 0.8)])
    return fade_end(lp(verb(y, np.random.default_rng(5004), wet=0.15, rt=0.4, tail=0.1), 3500), 20)
save('sfx_register_denied', reg_denied())
# ---------- 拾取 ----------
def leafcoin():
    r = np.random.default_rng(6001)
    c = seq([(0, pl(mtof(88), 0.45, 9), 0.7), (0.07, pl(mtof(95), 0.45, 8), 0.75)])
    leaf = nrm(bp(r.standard_normal(N_(0.16)), 2500, 6000)) * np.exp(-tt(0.16) * 22) * np.minimum(1, tt(0.16) / 0.006)
    return fade_end(lp(seq([(0, c), (0.0, leaf, 0.06)]), 7000), 15)
save('sfx_leafcoin_get', leafcoin())
def item_get():
    notes = [(0, 84), (0.09, 88), (0.18, 91), (0.30, 96)]
    y = verb(seq([(t, pl(mtof(m), 0.6, 7), 0.6 + 0.08 * i) for i, (t, m) in enumerate(notes)] + [(0.30, pl(mtof(84), 0.7, 5), 0.25)]), np.random.default_rng(6002), wet=0.18, rt=0.6, tail=0.25)
    return fade_end(lp(y[:N_(0.9)], 7000), 25)
save('sfx_item_get', item_get())
# ---------- 換區 whoosh ----------
def zone_enter():
    r = np.random.default_rng(7001); d = 0.9; n = r.standard_normal(N_(d)); x = tt(d)
    # 柔和風掃：帶通中心 350→1800→700 Hz（高斯形狀），15 ms 分塊濾波（保留狀態）近似時變
    fc = 350 * np.exp(np.log(1800 / 350) * np.exp(-((x - 0.4) / 0.28) ** 2)); y = np.zeros(len(n)); B = int(0.015 * SR); zi = None
    for i in range(0, len(n), B):
        c = fc[min(i, len(fc) - 1)]; sos = butter(2, [c * 0.6 / (SR / 2), min(c * 1.5, 9000) / (SR / 2)], 'band', output='sos')
        if zi is None: zi = sosfilt_zi(sos) * 0
        seg, zi = sosfilt(sos, n[i:i + B], zi=zi); y[i:i + B] = seg
    y = nrm(y) * np.sin(np.pi * np.minimum(1, x / d)) ** 1.8
    chime = seq([(0.3, pl(mtof(86), 0.5, 8), 0.12), (0.4, pl(mtof(91), 0.5, 8), 0.09)])
    return fade_end(lp(seq([(0, y, 0.5), (0, chime, 1.0)], d), 5000), 40)
save('sfx_zone_enter', zone_enter())
for k, v in OUT.items():
    v = v - np.mean(v); sf.write(f'tmp/{k}.wav', v, SR, subtype='FLOAT'); print(k, round(len(v) / SR, 3), 's')
