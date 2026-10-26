"""bgm_race_loop.ogg / bgm_race_final_loop.ogg — 《風野競走》賽中 BGM（原創，程式合成，無取樣）。
主循環：128 BPM、4/4、20 小節 = 37.500 s（1,653,750 samples）。
末段循環：144 BPM（+12.5%）、4/4、12 小節 = 20.000 s（882,000 samples），同一套和弦／旋律，加一層疊加（見 README）。
G 大調（五聲＋少量經過音）。和弦 G–D–Em–C（I–V–vi–IV）；B 段 G–D–C–D；結尾 C–D–Em–D（轉回 G）。
無縫循環：所有聲音先渲染到「循環長度＋尾巴」，尾巴疊返落開頭；殘響／噪音全部圓周（FFT）運算。
用法（喺 windrun-audio/）：PYTHONPATH=tools python tools/gen_bgm_race.py  → bgm/*.ogg（-16 LUFS 迭代增益）"""
import os, re, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, lfilter
from dsp import *
FF = os.environ.get('FF', 'ffmpeg')
CH = {'G': (43, [67, 71, 74, 79]), 'D': (50, [66, 69, 74, 78]), 'Em': (40, [64, 67, 71, 76]), 'C': (48, [64, 67, 72, 76])}
P1 = ['G', 'D', 'Em', 'C']; P2 = ['G', 'D', 'C', 'D']; P3 = ['C', 'D', 'Em', 'D']
# 主旋律（笛）：(拍, MIDI, 拍長)，每段 4 小節
M1 = [[(0, 71, 1), (1, 74, 1), (2, 79, 2)], [(0, 78, 1.5), (1.5, 76, .5), (2, 74, 2)], [(0, 76, 1), (1, 79, 1), (2, 83, 1.5), (3.5, 81, .5)], [(0, 79, 1.5), (1.5, 76, .5), (2, 72, 1), (3, 74, 1)]]
M2 = [[(0, 79, 1), (1, 83, 1), (2, 81, 1), (3, 79, 1)], [(0, 78, 1), (1, 81, 1), (2, 78, 1.5), (3.5, 76, .5)], [(0, 76, .5), (.5, 79, .5), (1, 83, 1), (2, 86, 2)], [(0, 84, 1), (1, 81, 1), (2, 79, 1), (3, 76, 1)]]
MB = [[(0, 74, 2), (2, 79, 1), (3, 83, 1)], [(0, 81, 1.5), (1.5, 78, .5), (2, 81, 1), (3, 78, 1)], [(0, 79, 1), (1, 84, 1), (2, 83, 1), (3, 79, 1)], [(0, 78, 1), (1, 74, 1), (2, 78, 1), (3, 81, 1)]]
M3 = [[(0, 79, 2), (2, 76, 1), (3, 72, 1)], [(0, 74, 1), (1, 78, 1), (2, 81, 2)], [(0, 83, 1.5), (1.5, 81, .5), (2, 79, 1), (3, 76, 1)], [(0, 74, .5), (.5, 78, .5), (1, 81, 1), (2, 78, 1.5), (3.5, 74, .5)]]
M0 = [[(0, 74, 4)], [(0, 78, 4)], [(0, 76, 4)], [(0, 79, 3), (3, 76, 1)]]      # 開頭段：只有長音，輕
def gpluck(f, d, decay=4.0):
    """撥弦：4 個泛音、1/h^1.6 衰減（柔和，少高頻）"""
    x = tt(d); y = sum((1 / h ** 1.6) * np.sin(2 * np.pi * f * h * x) * np.exp(-x * decay * (1 + .7 * (h - 1))) for h in range(1, 5))
    return y * adsr(len(x), 0.004, 0.03)
def flute(f, d, rng):
    """笛：基音＋弱泛音、延遲顫音、起音氣聲；低通 3.2 kHz"""
    x = tt(d); vib = 0.0045 * np.minimum(1, x / 0.25) * np.sin(2 * np.pi * 5.3 * x)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib)) / SR
    y = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    br = bandnoise(rng, d, 1800, 4200) * 0.05 * np.exp(-x * 14) + bandnoise(rng, d, 800, 3000) * 0.012
    y = (y + br) * adsr(len(x), 0.035, 0.14)
    b, a = butter(2, 3200 / (SR / 2)); return lfilter(b, a, y)
def kick():
    x = tt(0.3); f = 46 + 70 * np.exp(-x * 38); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 14) * adsr(len(x), 0.001, 0.02)
def tok(f=620):
    x = tt(0.09); return (np.sin(2 * np.pi * f * x) + .5 * np.sin(2 * np.pi * f * 1.58 * x)) * np.exp(-x * 55) * adsr(len(x), 0.001, 0.01)
def snare(rng):
    x = tt(0.16); n = bandnoise(rng, 0.16, 900, 5000) * np.exp(-x * 26); b = np.sin(2 * np.pi * 190 * x) * np.exp(-x * 30)
    return (0.8 * n + 0.5 * b) * adsr(len(x), 0.001, 0.02)
def shaker(rng, d=0.07):
    n = bandnoise(rng, d, 5500, 11000); x = tt(d); return n * adsr(len(x), 0.008, 0.02) * np.exp(-x * 45)

def render(name, BPM, NBAR, sections, final, seed):
    BEAT = 60 / BPM; BAR = 4 * BEAT; N = int(round(NBAR * BAR * SR)); TAIL = int(6 * SR); STEP = BEAT / 4
    rng = np.random.default_rng(seed)
    mel = [np.zeros(N + TAIL), np.zeros(N + TAIL)]; drm = [np.zeros(N + TAIL), np.zeros(N + TAIL)]
    def put(bus, x, t, gain=1.0, pan=0.0):
        if t < 0: t += N / SR     # 負時間：喺循環尾開始，尾巴疊返落開頭
        pan = max(-1.0, min(1.0, pan)); th = (pan + 1) * np.pi / 4; place(bus[0], t, x, gain * np.cos(th)); place(bus[1], t, x, gain * np.sin(th))
    prog = []; lead = []; sec_of = []
    for si, (P, M) in enumerate(sections):
        for b in range(4): prog.append(P[b]); lead.append(M[b] if M else []); sec_of.append(si)
    assert len(prog) == NBAR
    for b, c in enumerate(prog):
        t0 = b * BAR; bass, notes = CH[c]
        # 氣墊 pad：慢起慢收、輕微失諧、左右分開
        for k, m in enumerate(notes[:3]):
            for det, pan in ((0.997, -0.5 - 0.1 * k), (1.003, 0.5 + 0.1 * k)):
                y = softsine(mtof(m - 12) * det, BAR + 1.6, a=0.9 * BEAT * 2, r=1.4, harm=(1, 2, 3), amps=(1, .25, .06))
                put(mel, y, t0 - 0.3, 0.032, pan)
        # 低音：八分音撥彈（末段每八分都彈）
        pat = [(0, 1.0), (1, .0), (2, .7), (3, .6), (4, .85), (5, 0), (6, .65), (7, .55)]
        if final: pat = [(0, 1.0), (1, .5), (2, .75), (3, .6), (4, .9), (5, .5), (6, .7), (7, .6)]
        for i, v in pat:
            if v == 0: continue
            m = bass + (12 if i in (3, 7) else 0)
            y = softsine(mtof(m), BEAT * 0.9, a=0.004, r=0.08, decay=4.5, harm=(1, 2, 3), amps=(1, .35, .1))
            put(mel, y, t0 + i * BEAT / 2, 0.105 * v, 0.0)
        # 撥弦琶音：八分音，輪流喺和弦音（弱拍輕、帶方向感）
        ns = [n - 12 if n > 78 else n for n in notes]
        arp = [0, 1, 2, 1, 3, 2, 1, 2]
        for i, p in enumerate(arp):
            if sec_of[b] == 0 and i % 2 == 1: continue         # 開頭段較疏
            if rng.random() < 0.08 and i not in (0, 4): continue
            v = (1.0 if i % 2 == 1 else 0.7) * (1.15 if i == 0 else 1.0)
            put(mel, gpluck(mtof(ns[p]), 0.7, 4.5), t0 + i * BEAT / 2 + rng.normal(0, 0.0012), 0.125 * v, -0.55 + 1.1 * p / 3)
        # 笛主旋律
        for (bt, m, du) in lead[b]:
            put(mel, flute(mtof(m), du * BEAT + 0.12, rng), t0 + bt * BEAT, 0.13 if sec_of[b] else 0.09, 0.12)
        # 末段額外一層：八度鐘琴閃光（十六分音上行）＋十六分 muted 撥弦
        if final:
            top = [n + 12 for n in notes]
            for i in range(8):
                put(mel, bell(mtof(top[[0, 2, 1, 3, 2, 1, 3, 2][i]]), 0.5, decay=9, a=0.002, r=0.05), t0 + i * BEAT / 2 + BEAT / 4, 0.035, 0.5 * (-1) ** i)
        # 打擊
        for s in range(16):
            t = t0 + s * STEP
            if s in (0, 8) or (final and s in (4, 12)) or (not final and s == 10 and b % 4 == 3): put(drm, kick(), t, 0.40 if s != 10 else 0.22, 0)
            if sec_of[b] >= 1 and s in (4, 12): put(drm, snare(rng), t, 0.07 if not final else 0.085, 0.05)
            if s in (2, 6, 10, 14) or (final and s % 2 == 1): put(drm, shaker(rng), t, 0.085 if s % 4 == 2 else 0.055, 0.3 * (-1) ** (s // 2))
            if sec_of[b] >= 1 and s in (3, 11): put(drm, tok(620 if s == 3 else 780), t, 0.09, -0.25 if s == 3 else 0.25)
        # 過門：每 4 小節（末段每 4 小節）最後一拍十六分 roll
        if b % 4 == 3 and sec_of[b] >= 1:
            for k in range(4): put(drm, snare(rng), t0 + (12 + k) * STEP, 0.03 + 0.016 * k, 0)
    # 循環尾：風聲 swell 衝返落下一圈第 1 拍
    sw = bandnoise(rng, BAR * 0.9, 900, 5500); xs = tt(BAR * 0.9); sw = sw * (xs / xs[-1]) ** 2.0 * adsr(len(xs), 0.1, 0.004)
    put(mel, sw, N / SR - BAR * 0.9, 0.045, 0.0)
    # 環境風：圓周濾波噪音＋慢 LFO（每 4 小節一個週期）
    f = np.fft.rfftfreq(N, 1 / SR); tN = np.arange(N) / SR
    for ch, sd in ((0, 1), (1, 2)):
        x = np.random.default_rng(seed + sd).standard_normal(N); X = np.fft.rfft(x)
        H = (1 / (1 + (220 / np.maximum(f, 1e-9)) ** 2)) * (1 / (1 + (f / 1500) ** 4)); air = np.fft.irfft(X * H, N); air /= np.std(air)
        mel[ch][:N] += 0.016 * air * (0.55 + 0.45 * np.sin(2 * np.pi * tN / (4 * BAR) + 1.1 * sd))
    def fold(buf): y = buf[:N].copy(); tl = buf[N:]; y[:len(tl)] += tl; return y
    M = [fold(mel[0]), fold(mel[1])]; D = [fold(drm[0]), fold(drm[1])]
    def circ_verb(x, sd, wet=0.30, rt=1.6):
        r = np.random.default_rng(sd); ir = verb_ir(r, rt=rt, pre=0.012, damp=4200, length=min(rt * 1.6, 6)); irp = np.zeros(N); irp[:len(ir)] = ir
        return (1 - wet * 0.5) * x + wet * np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(irp), N)
    def circ_verb_d(x, sd): return circ_verb(x, sd, wet=0.12, rt=0.7)
    y = np.stack([circ_verb(M[0], seed + 11) + circ_verb_d(D[0], seed + 21), circ_verb(M[1], seed + 12) + circ_verb_d(D[1], seed + 22)], axis=1)
    Y = np.fft.rfft(y, axis=0); Y *= (1 / (1 + (35 / np.maximum(f, 1e-9)) ** 4))[:, None]; y = np.fft.irfft(Y, N, axis=0)
    return y, N

def meas(p):
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
def encode(y, wav, out, g):
    sf.write(wav, y * g, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-ac', '2', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '5', out], check=True)
    return meas(out)
if __name__ == '__main__':
    os.makedirs('tmp', exist_ok=True); os.makedirs('bgm', exist_ok=True)
    jobs = [('bgm_race_loop', 128, 20, [(P1, M0), (P1, M1), (P2, MB), (P1, M2), (P3, M3)], False, 20261028),
            ('bgm_race_final_loop', 144, 12, [(P1, M2), (P2, MB), (P3, M3)], True, 20261029)]
    for name, bpm, nb, secs, fin, seed in jobs:
        y, N = render(name, bpm, nb, secs, fin, seed); g = 0.1
        for it in range(8):
            I, TP = encode(y, f'tmp/{name}.wav', f'bgm/{name}.ogg', g)
            if abs(I + 16) < 0.1: break
            g *= 10 ** ((-16 - I) / 20)
        print(name, 'bpm', bpm, 'bars', nb, 'gain', round(g, 4), 'LUFS', I, 'TP', TP, 'loop sec', N / SR, 'samples', N)
