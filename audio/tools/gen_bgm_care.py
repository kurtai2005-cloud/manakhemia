"""bgm_care_loop.ogg — 《微光小圃》照顧場景 BGM（原創，程式合成，無取樣）。
68 BPM、4/4、20 小節 = 70.588 s。C 大調五聲音階。
無縫循環做法：所有聲音先渲染到「循環長度 + 尾巴」，尾巴疊返落開頭（overlap-add）；
殘響、噪音濾波全部用圓周（FFT）運算，所以尾端自然接回開頭，冇接縫。
用法（喺 audio/ 目錄）：PYTHONPATH=tools python tools/gen_bgm_care.py  → bgm/bgm_care_loop.ogg"""
import os, subprocess, numpy as np, soundfile as sf
from dsp import *
BPM = 68; BEAT = 60 / BPM; BAR = 4 * BEAT; NBAR = 20
N = int(round(NBAR * BAR * SR)); TAIL = int(7 * SR)
rng = np.random.default_rng(20261027)
L = np.zeros(N + TAIL); R = np.zeros(N + TAIL)
def put(x, t, gain=1.0, pan=0.0):
    """pan -1..1 equal-power"""
    if t < 0: t += N / SR     # 負時間：喺循環尾開始，尾巴會疊返落開頭
    pan = max(-1.0, min(1.0, pan)); th = (pan + 1) * np.pi / 4; place(L, t, x, gain * np.cos(th)); place(R, t, x, gain * np.sin(th))
# 和弦（C 大調）：bass, 和弦音
CH = {'C': (36, [60, 64, 67, 71]), 'Am': (33, [57, 60, 64, 67]), 'F': (41, [57, 60, 64, 65 + 12 - 12 + 0]), 'G': (43, [59, 62, 64, 67]), 'Em': (40, [59, 62, 64, 67])}
CH['F'] = (41, [57, 60, 64, 69]); CH['G'] = (43, [59, 62, 64, 67])
A_ = ['C', 'Am', 'F', 'G']; B_ = ['F', 'G', 'Em', 'Am']
prog = A_ + A_ + B_ + A_ + A_
# Pad：慢起慢收，輕微失諧，左右分開
for b, c in enumerate(prog):
    t0 = b * BAR; bass, notes = CH[c]
    for k, m in enumerate(notes):
        d = BAR + 2.4
        for det, pan in ((0.997, -0.5 - 0.1 * k), (1.003, 0.5 + 0.1 * k)):
            y = softsine(mtof(m - 12) * det, d, a=1.4, r=2.2, harm=(1, 2, 3), amps=(1, .3, .08))
            put(y, t0 - 0.2, 0.05, pan)
    put(softsine(mtof(bass), BAR * 1.0, a=0.05, r=1.2, decay=1.2, harm=(1, 2), amps=(1, .2)), t0, 0.16, 0)
    put(softsine(mtof(bass), BEAT * 1.5, a=0.05, r=0.6, decay=2.5), t0 + 2 * BEAT, 0.08, 0)
# 豎琴撥弦琶音：每拍 2 個八分音，上行再回落；少量留白同微小時值抖動
pat = [0, 1, 2, 3, 2, 1, 2, 1]
for b, c in enumerate(prog):
    bass, notes = CH[c]; ns = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[3] + 12]
    ns[3] = ns[3] if ns[3] < 84 else ns[3] - 12
    for i, p in enumerate(pat):
        if rng.random() < 0.14 and i not in (0, 4): continue
        t = b * BAR + i * BEAT / 2 + rng.normal(0, 0.006)
        v = (0.5 if i % 2 == 0 else 0.36) * (1.0 if i != 0 else 1.15)
        put(pluck(mtof(ns[p]), 2.2, decay=2.2), t, 0.07 * v * 2.2, pan=-0.6 + 1.2 * (p / 3))
# 賽珞／音樂盒主旋律 + 附點八分回音
MEL = [
    [(0, 76, 2), (2, 79, 1), (3, 76, 1), (4, 74, 2), (6, 72, 2)],
    [(0, 72, 1.5), (1.5, 74, .5), (2, 76, 2), (4, 79, 2), (6, 76, 2)],
    [(0, 81, 2), (2, 79, 1), (3, 76, 1), (5, 79, 1), (6, 76, 2)],
    [(0, 74, 2), (2, 76, 1), (3, 74, 1), (4, 72, 2), (6, 69, 2)],
    [(0, 79, 1), (1, 81, 1), (2, 84, 2), (4, 81, 2), (6, 79, 2)],
    [(0, 76, 2), (2, 79, 1), (3, 81, 1), (4, 79, 2), (6, 76, 2)],
    [(0, 76, 2), (2, 79, 1), (3, 76, 1), (4, 74, 2), (6, 79, 2)],
    [(0, 72, 2), (2, 76, 1), (3, 79, 1), (4, 76, 2), (6, 74, 2)],
    [(0, 79, 2), (2, 76, 2), (4, 74, 1), (5, 76, 1), (6, 79, 2)],
    [(0, 76, 2), (2, 74, 2), (4, 72, 2), (6, 67, 2)]]
for blk, notes in enumerate(MEL):
    for (bt, m, dur) in notes:
        t = blk * 2 * BAR + bt * BEAT + rng.normal(0, 0.004); pan = rng.uniform(-0.25, 0.25)
        y = bell(mtof(m), 3.0, decay=3.2, a=0.004, r=0.3)
        put(y, t, 0.17, pan)
        for k, g in ((1, 0.30), (2, 0.12)):
            put(y, t + k * 0.75 * BEAT, 0.17 * g, -pan + 0.35 * (-1) ** k)    # 附點八分回音（左右跳）
# 環境：空氣（圓周濾波噪音 + 慢速 LFO）、蟋蟀（遠處，極輕）
def circ_band(lo, hi, seed):
    r = np.random.default_rng(seed); x = r.standard_normal(N); X = np.fft.rfft(x); f = np.fft.rfftfreq(N, 1 / SR)
    H = (1 / (1 + (lo / np.maximum(f, 1e-9)) ** 2)) * (1 / (1 + (f / hi) ** 4)); return np.fft.irfft(X * H, N)
tN = np.arange(N) / SR
for ch, seed in ((L, 1), (R, 2)):
    air = circ_band(250, 1800, seed); air /= np.std(air)
    lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (tN / (N / SR)) * 5 + 1.3 * seed)       # 5 個週期 / 循環 → 週期銜接
    ch[:N] += 0.012 * air * lfo
def cricket(t0, f=4300, pan=0.0, n=3):
    for i in range(n):
        d = 0.03; x = tt(d); y = np.sin(2 * np.pi * f * x) * adsr(len(x), 0.006, 0.01); put(y, t0 + i * 0.055, 0.0035, pan)
for t0 in np.sort(rng.uniform(1.0, NBAR * BAR - 1.0, 18)):
    cricket(t0, f=rng.choice([4100, 4300, 4600]), pan=rng.choice([-0.7, 0.7]), n=int(rng.integers(2, 5)))
# 疊返尾巴落開頭
def fold(buf):
    y = buf[:N].copy(); tl = buf[N:]; y[:len(tl)] += tl; return y
dry = [fold(L), fold(R)]
# 圓周殼層殘響（立體聲，左右 IR 唔同）
def circ_verb(x, seed, wet=0.38, rt=3.0):
    r = np.random.default_rng(seed); ir = verb_ir(r, rt=rt, pre=0.025, damp=3000, length=min(rt * 1.6, 9)); irp = np.zeros(N); irp[:len(ir)] = ir
    return (1 - wet * 0.5) * x + wet * np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(irp), N)
y = np.stack([circ_verb(dry[0], 11), circ_verb(dry[1], 12)], axis=1)
# 圓周高通 30 Hz
Y = np.fft.rfft(y, axis=0); f = np.fft.rfftfreq(N, 1 / SR); Y *= (1 / (1 + (30 / np.maximum(f, 1e-9)) ** 4))[:, None]; y = np.fft.irfft(Y, N, axis=0)
os.makedirs('tmp', exist_ok=True); os.makedirs('bgm', exist_ok=True)
FF = os.environ.get('FF', 'ffmpeg')
import re
def meas(p):
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
def enc(g):
    sf.write('tmp/bgm.wav', y * g, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', 'tmp/bgm.wav', '-ac', '2', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '5', 'bgm/bgm_care_loop.ogg'], check=True)
    return meas('bgm/bgm_care_loop.ogg')
g = 0.1
for it in range(6):                           # 迭代增益：量度「編碼後」嘅 ogg，直至 -16 LUFS
    I, TP = enc(g)
    if abs(I + 16) < 0.15: break
    g *= 10 ** ((-16 - I) / 20)
print('gain', round(g, 4), 'LUFS', I, 'TP', TP, 'loop sec', N / SR, 'samples', N)
