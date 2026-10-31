"""方案 A ③：時段 BGM 變奏（早／晚／深夜）— 原創，程式合成，無取樣。
由 gen_bgm_care.py 嘅同一套和弦／旋律／小節網格派生：68 BPM、4/4、C 大調五聲音階、1 小節 = 3.5294 s。
第 k 小節嘅和弦同 bgm_care_loop 第 k 小節完全一樣（A A B A A 嘅頭 16／12 小節），所以可以喺小節線上 crossfade。
正午 = 現有 bgm_care_loop.ogg（唔重生）。
無縫循環：同 gen_bgm_care.py 一樣——渲染「循環長度 + 尾巴」→ 尾巴疊返落開頭；噪音濾波／殘響用圓周 FFT 運算。
用法（喺 audio/）：PYTHONPATH=tools python tools/gen_bgm_tod.py [morning|evening|night ...]  → bgm/bgm_care_<x>_loop.ogg
固定亂數種子。"""
import os, re, sys, subprocess, numpy as np, soundfile as sf
from dsp import *
BPM = 68; BEAT = 60 / BPM; BAR = 4 * BEAT
CH = {'C': (36, [60, 64, 67, 71]), 'Am': (33, [57, 60, 64, 67]), 'F': (41, [57, 60, 64, 69]), 'G': (43, [59, 62, 64, 67]), 'Em': (40, [59, 62, 64, 67])}
A_ = ['C', 'Am', 'F', 'G']; B_ = ['F', 'G', 'Em', 'Am']
PROG20 = A_ + A_ + B_ + A_ + A_                 # 同 bgm_care_loop
MEL = [  # 同 bgm_care_loop：每 2 小節一組 (拍, midi, 拍長)
    [(0, 76, 2), (2, 79, 1), (3, 76, 1), (4, 74, 2), (6, 72, 2)],
    [(0, 72, 1.5), (1.5, 74, .5), (2, 76, 2), (4, 79, 2), (6, 76, 2)],
    [(0, 81, 2), (2, 79, 1), (3, 76, 1), (5, 79, 1), (6, 76, 2)],
    [(0, 74, 2), (2, 76, 1), (3, 74, 1), (4, 72, 2), (6, 69, 2)],
    [(0, 79, 1), (1, 81, 1), (2, 84, 2), (4, 81, 2), (6, 79, 2)],
    [(0, 76, 2), (2, 79, 1), (3, 81, 1), (4, 79, 2), (6, 76, 2)],
    [(0, 76, 2), (2, 79, 1), (3, 76, 1), (4, 74, 2), (6, 79, 2)],
    [(0, 72, 2), (2, 76, 1), (3, 79, 1), (4, 76, 2), (6, 74, 2)]]
FF = os.environ.get('FF', 'ffmpeg')
PENTA = [74, 76, 79, 81]    # D E G A（鳥仔 chirp 用，升高 2–3 個八度）

def render(name, nbar, target, seed, style):
    N = int(round(nbar * BAR * SR)); TAIL = int(7 * SR); dur = N / SR
    rng = np.random.default_rng(seed); prog = PROG20[:nbar]
    ML = np.zeros(N + TAIL); MR = np.zeros(N + TAIL)     # 音樂 bus
    AL = np.zeros(N + TAIL); AR = np.zeros(N + TAIL)     # 環境 bus（蟋蟀、鳥）
    def put(x, t, gain=1.0, pan=0.0, bus='m'):
        if t < 0: t += dur       # 負時間：喺循環尾開始，尾巴會疊返落開頭
        l, r = (ML, MR) if bus == 'm' else (AL, AR)
        pan = max(-1.0, min(1.0, pan)); th = (pan + 1) * np.pi / 4; place(l, t, x, gain * np.cos(th)); place(r, t, x, gain * np.sin(th))
    # --- pad：慢起慢收 ---
    pad_g = dict(morning=0.045, evening=0.060, night=0.075)[style]
    for b, c in enumerate(prog):
        t0 = b * BAR; bass, notes = CH[c]
        for k, m in enumerate(notes):
            d = BAR + 2.4
            for det, pan in ((0.997, -0.5 - 0.1 * k), (1.003, 0.5 + 0.1 * k)):
                if style == 'morning':   # 較亮：pad 上移一個八度嘅一半（m-5 ≈ 保持同和弦轉位），多啲高次諧波
                    y = softsine(mtof(m - 12 + (12 if k >= 2 else 0)) * det, d, a=1.0, r=2.0, harm=(1, 2, 3, 4), amps=(1, .38, .16, .05))
                elif style == 'evening':  # 偏低偏暖：少諧波
                    y = softsine(mtof(m - 12) * det, d, a=1.8, r=2.6, harm=(1, 2), amps=(1, .14))
                else:                     # night：極柔，最少諧波，更慢嘅起收
                    y = softsine(mtof(m - 12) * det, d, a=2.2, r=3.0, harm=(1, 2), amps=(1, .08))
                put(y, t0 - 0.2, pad_g, pan)
        if style == 'evening':
            put(softsine(mtof(bass), BAR, a=0.1, r=1.6, decay=0.9, harm=(1, 2), amps=(1, .15)), t0, 0.17, 0)
        elif style == 'morning':
            put(softsine(mtof(bass), BAR, a=0.05, r=1.2, decay=1.4, harm=(1, 2), amps=(1, .2)), t0, 0.12, 0)
        # night：冇低音、冇鼓（低頻衰減）
    # --- 琶音 ---
    if style == 'morning':
        pat = [0, 1, 2, 3, 2, 1, 2, 1]
        for b, c in enumerate(prog):
            bass, notes = CH[c]; ns = [n + 12 for n in notes]; ns[3] = ns[3] if ns[3] < 84 else ns[3] - 12
            for i, p in enumerate(pat):
                if rng.random() < 0.20 and i not in (0, 4): continue
                t = b * BAR + i * BEAT / 2 + rng.normal(0, 0.006)
                v = (0.5 if i % 2 == 0 else 0.36) * (1.0 if i != 0 else 1.15)
                put(bell(mtof(ns[p] + 12 if p == 3 else ns[p]), 1.6, decay=4.0, a=0.003, r=0.15), t, 0.036 * v, pan=-0.6 + 1.2 * (p / 3))
    elif style == 'evening':   # 疏啲：每拍一個（四分音符），撥弦較柔、較長
        pat = [0, 2, 1, 3]
        for b, c in enumerate(prog):
            bass, notes = CH[c]; ns = [n + 12 for n in notes]
            for i, p in enumerate(pat):
                if rng.random() < 0.38 and i != 0: continue
                t = b * BAR + i * BEAT + rng.normal(0, 0.008)
                put(pluck(mtof(ns[p] - (12 if p == 3 else 0)), 3.0, decay=1.5, a=0.004), t, 0.07 * (0.9 if i else 1.1) * 2.0, pan=-0.5 + 1.0 * (p / 3))
    # --- 主旋律 ---
    nblk = nbar // 2
    if style == 'morning':    # 升高八度，鐘琴多（原音區輕輕疊一層）
        for blk in range(nblk):
            for (bt, m, dur_) in MEL[blk]:
                t = blk * 2 * BAR + bt * BEAT + rng.normal(0, 0.004); pan = rng.uniform(-0.3, 0.3)
                mh = m + 12 if m + 12 <= 93 else m
                y = bell(mtof(mh), 3.0, decay=3.4, a=0.003, r=0.3, bright=1.3)
                put(y, t, 0.15, pan)
                put(bell(mtof(m), 3.0, decay=3.2, a=0.004, r=0.3), t, 0.06, -pan * 0.5)
                for k, g in ((1, 0.32), (2, 0.14)):
                    put(y, t + k * 0.75 * BEAT, 0.15 * g, -pan + 0.35 * (-1) ** k)
    elif style == 'evening':  # 撥弦代替鐘琴
        for blk in range(nblk):
            for (bt, m, dur_) in MEL[blk]:
                t = blk * 2 * BAR + bt * BEAT + rng.normal(0, 0.006); pan = rng.uniform(-0.25, 0.25)
                y = pluck(mtof(m - 12 if m >= 79 else m), 3.2, decay=1.6, a=0.004, r=0.2)
                put(y, t, 0.16, pan)
                for k, g in ((1, 0.30), (2, 0.12)):
                    put(y, t + k * 0.75 * BEAT, 0.16 * g, -pan + 0.35 * (-1) ** k)
    else:                      # night：每 2 小節一個單音鐘琴（低八度，長殘響）
        for blk in range(nblk):
            m = MEL[blk][0][1] - 12
            put(bell(mtof(m), 4.5, decay=1.6, a=0.02, r=0.6, bright=0.4), blk * 2 * BAR + 0.15, 0.22, rng.uniform(-0.25, 0.25))
    # --- 環境：空氣（圓周濾波噪音，整數個 LFO 週期）---
    def circ_band(lo, hi, sd):
        r = np.random.default_rng(sd); x = r.standard_normal(N); X = np.fft.rfft(x); f = np.fft.rfftfreq(N, 1 / SR)
        H = (1 / (1 + (lo / np.maximum(f, 1e-9)) ** 2)) * (1 / (1 + (f / hi) ** 4)); return np.fft.irfft(X * H, N)
    tN = np.arange(N) / SR
    ahi = dict(morning=2600, evening=1400, night=900)[style]; ag = dict(morning=0.011, evening=0.011, night=0.014)[style]
    cyc = max(2, nbar // 4)
    for ch, sd in ((ML, 1), (MR, 2)):
        air = circ_band(250, ahi, sd + seed % 100); air /= np.std(air)
        ch[:N] += ag * air * (0.55 + 0.45 * np.sin(2 * np.pi * (tN / dur) * cyc + 1.3 * sd))
    # 蟋蟀（evening 開始出現，night 較多較遠）
    def cricket(t0, f, pan, n, g):
        for i in range(n):
            x = tt(0.03); put(np.sin(2 * np.pi * f * x) * adsr(len(x), 0.006, 0.01), t0 + i * 0.055, g, pan, 'a')
    ncr = dict(morning=0, evening=int(nbar * 1.4), night=int(nbar * 1.6))[style]
    cg = dict(morning=0, evening=0.0035, night=0.0030)[style]
    for t0 in np.sort(rng.uniform(1.0, dur - 1.0, ncr)):
        cricket(t0, rng.choice([4100, 4300, 4600]), rng.choice([-0.8, -0.6, 0.6, 0.8]), int(rng.integers(2, 5)), cg)
    # 鳥鳴（morning）：細小 chirp 短句，疏落、輕
    if style == 'morning':
        def chirp(f0, f1, d):
            x = tt(d); f = f0 * (f1 / f0) ** (x / d) * (1 + 0.012 * np.sin(2 * np.pi * 38 * x))
            return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * np.arange(len(x)) / len(x)) ** 1.5
        for t0 in np.sort(rng.uniform(1.5, dur - 2.0, 11)):
            pan = rng.uniform(-0.8, 0.8); n = int(rng.integers(2, 5)); base = mtof(rng.choice(PENTA) + 24)
            for i in range(n):
                fr = base * rng.choice([1.0, 1.122, 1.26, 1.498]); up = rng.random() < 0.6
                put(chirp(fr * (0.9 if up else 1.1), fr * (1.1 if up else 0.9), rng.uniform(0.06, 0.11)), t0 + i * rng.uniform(0.11, 0.16), 0.030, pan, 'a')
    # --- 音樂 bus 色調（圓周，低通；night 另加高通）---
    def fold(buf):
        y = buf[:N].copy(); tl = buf[N:]; y[:len(tl)] += tl; return y
    f = np.fft.rfftfreq(N, 1 / SR)
    def tone(x, lp=None, hp=None, order=2):
        X = np.fft.rfft(x); H = np.ones_like(f)
        if lp: H = H / (1 + (f / lp) ** (2 * order))
        if hp: H = H / (1 + (hp / np.maximum(f, 1e-9)) ** (2 * order))
        return np.fft.irfft(X * H, N)
    lp = dict(morning=None, evening=3200, night=2200)[style]; hp = dict(morning=None, evening=None, night=110)[style]
    mus = [tone(fold(ML), lp, hp), tone(fold(MR), lp, hp)]; amb = [fold(AL), fold(AR)]
    dry = [mus[0] + amb[0], mus[1] + amb[1]]
    wet, rt = dict(morning=(0.34, 2.6), evening=(0.40, 3.2), night=(0.46, 3.8))[style]
    def circ_verb(x, sd):
        r = np.random.default_rng(sd); ir = verb_ir(r, rt=rt, pre=0.025, damp=3000 if style != 'night' else 2200, length=min(rt * 1.6, 9)); irp = np.zeros(N); irp[:len(ir)] = ir
        return (1 - wet * 0.5) * x + wet * np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(irp), N)
    y = np.stack([circ_verb(dry[0], 11), circ_verb(dry[1], 12)], axis=1)
    Y = np.fft.rfft(y, axis=0); Y *= (1 / (1 + (30 / np.maximum(f, 1e-9)) ** 4))[:, None]; y = np.fft.irfft(Y, N, axis=0)
    # --- 編碼 + 迭代增益（量度編碼後 ogg）---
    os.makedirs('tmp', exist_ok=True); os.makedirs('bgm', exist_ok=True)
    out = f'bgm/{name}.ogg'
    def meas(p):
        o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
        return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
    def enc(g):
        sf.write(f'tmp/{name}.wav', y * g, SR, subtype='FLOAT')
        subprocess.run([FF, '-y', '-v', 'error', '-i', f'tmp/{name}.wav', '-ac', '2', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '5', out], check=True)
        return meas(out)
    g = 0.1
    for it in range(8):
        I, TP = enc(g)
        if abs(I - target) < 0.12: break
        g *= 10 ** ((target - I) / 20)
    print(f'{name}: gain {g:.4f} LUFS {I} TP {TP} bars {nbar} sec {dur:.3f} samples {N}')

SPEC = dict(morning=('bgm_care_morning_loop', 16, -16.0, 20261101), evening=('bgm_care_evening_loop', 16, -16.0, 20261102), night=('bgm_care_night_loop', 12, -22.0, 20261103))
if __name__ == '__main__':
    for k in (sys.argv[1:] or ['morning', 'evening', 'night']):
        nm, nb, tg, sd = SPEC[k]; render(nm, nb, tg, sd, k)
