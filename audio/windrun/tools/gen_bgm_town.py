"""bgm_town_morningmoss_loop.ogg — 《風野競走》晨苔鎮（第一個城鎮）BGM（原創，程式合成，無取樣）。
75 BPM、4/4、24 小節 = 76.800 s = 3,386,880 samples（75 BPM → 一拍 35,280 samples，整數，循環可 sample-accurate）。
F 大調＋利底亞色彩（G 大三和弦、旋律 B♮ = #4）。結構（每段 4 小節）：A | A' | B | A | 橋 | A''。
音色：撥弦（結他／豎琴式，加法合成）、笛／口哨主旋律（氣聲＋延遲顫音）、鐘琴閃光（疏落、極輕）、柔和 pad、低音、
極輕鳥鳴（3–5.5 kHz 短啁啾）、環境風。冇鼓；主旋律集中 C5–D6（500–1100 Hz），中高頻 1–4 kHz 留位畀對話 blip。
無縫循環：全部聲音渲染到「循環長度＋6 s 尾巴」疊返落開頭；殘響／風聲用 FFT 圓周運算。
用法（喺 windrun-audio/）：PYTHONPATH=tools python tools/gen_bgm_town.py  → bgm/bgm_town_morningmoss_loop.ogg（-16 LUFS）"""
import os, re, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, lfilter
from dsp import *
from gen_bgm_race import flute          # 沿用賽中 BGM 嘅笛（import 唔會執行生成；有 __main__ 保護）
FF = os.environ.get('FF', 'ffmpeg')
BPM = 75; NBAR = 24; BEAT_N = 44100 * 60 // BPM; assert BEAT_N * BPM == 44100 * 60
# 和弦：(低音 MIDI, 琶音池 5 個升序音)
CH = {'F': (41, [53, 57, 60, 64, 69]), 'G': (43, [55, 59, 62, 64, 71]), 'Am': (45, [57, 60, 64, 67, 69]),     # G：大三和弦（B♮）＋add9 E
      'Bb': (46, [58, 62, 65, 69, 74]), 'C': (48, [55, 60, 64, 67, 72]), 'Dm': (50, [57, 62, 65, 69, 72]), 'Gm': (43, [55, 58, 62, 65, 70])}
PA = ['F', 'G', 'Am', 'Bb']; PA2 = ['F', 'G', 'Am', 'C']; PB = ['Dm', 'Bb', 'F', 'C']; PBR = ['Bb', 'Am', 'Gm', 'C']
# 主旋律：(拍, MIDI, 拍長)，每段 4 小節
MA = [[(1, 72, 1), (2, 76, 1), (3, 77, 1)], [(0, 79, 2), (2, 83, 1.5), (3.5, 81, .5)], [(0, 81, 1.5), (1.5, 79, .5), (2, 76, 2)], [(0, 77, 1), (1, 74, 1), (2, 77, 2)]]
MA2 = [[(0, 72, 1), (1, 77, 1), (2, 81, 2)], [(0, 79, 1.5), (1.5, 81, .5), (2, 83, 2)], [(0, 84, 1), (1, 81, 1), (2, 79, 1), (3, 76, 1)], [(0, 76, 2), (2, 72, 2)]]
MB = [[(0, 74, 1), (1, 77, 1), (2, 81, 1.5), (3.5, 79, .5)], [(0, 77, 2), (2, 74, 1), (3, 77, 1)], [(0, 81, 1.5), (1.5, 84, .5), (2, 86, 2)], [(0, 84, 1), (1, 79, 1), (2, 76, 2)]]
MBR = [[(0, 86, 2), (2, 84, 1), (3, 82, 1)], [(0, 81, 3), (3, 79, 1)], [(0, 77, 1.5), (1.5, 79, .5), (2, 82, 2)], [(0, 81, 1), (1, 79, 1), (2, 76, 2)]]
MA3 = [[(1, 72, 1), (2, 76, 1), (3, 81, 1)], [(0, 79, 2), (2, 83, 1), (3, 81, 1)], [(0, 81, 1), (1, 79, 1), (2, 76, 1), (3, 74, 1)], [(0, 77, 3)]]
SECTIONS = [(PA, MA, 0), (PA2, MA2, 1), (PB, MB, 1), (PA, MA, 1), (PBR, MBR, 2), (PA, MA3, 1)]    # 第 3 欄：琶音型態
ARP = {0: [0, 2, 3, 2, 4, 3, 2, 1], 1: [0, 2, 1, 3, 2, 4, 3, 2], 2: [0, 3, 2, 4, 2, 3, 1, 2]}
def gpluck(f, d, decay=3.2, rng=None):
    """結他／豎琴式撥弦：8 個泛音（1/h^1.35，高次泛音衰得快、略為拉闊）＋極短撥片噪音；整體柔和。"""
    x = tt(d); y = np.zeros(len(x))
    for h in range(1, 9):
        y += (1 / h ** 1.35) * np.sin(2 * np.pi * f * h * (1 + 0.0004 * h * h) * x) * np.exp(-x * decay * (1 + 0.9 * (h - 1) ** 1.1))
    if rng is not None:
        pk = bandnoise(rng, 0.012, 1200, 3500) * np.exp(-tt(0.012) * 300) * 0.03; y[:len(pk)] += pk
    return y * adsr(len(x), 0.002, 0.04)
def whistle_note(f, d, rng):
    """口哨／笛：flute()（氣聲起音＋延遲顫音），再低通 2.8 kHz"""
    y = flute(f, d, rng); b, a = butter(2, 2800 / (SR / 2)); return lfilter(b, a, y)
def chirp(rng, f0, f1, d, wob=0.0):
    x = tt(d); f = f0 + (f1 - f0) * (x / d) ** 0.7; f = f * (1 + wob * np.sin(2 * np.pi * rng.uniform(25, 45) * x))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.12 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return y * np.sin(np.pi * x / d) ** 1.6
def render(seed=20261101):
    BEAT = BEAT_N / SR; BAR = 4 * BEAT; N = NBAR * 4 * BEAT_N; TAIL = int(6 * SR); rng = np.random.default_rng(seed)
    bus = [np.zeros(N + TAIL), np.zeros(N + TAIL)]; air_b = [np.zeros(N + TAIL), np.zeros(N + TAIL)]
    def put(buf, x, t, gain=1.0, pan=0.0):
        if t < 0: t += N / SR
        pan = max(-1.0, min(1.0, pan)); th = (pan + 1) * np.pi / 4; place(buf[0], t, x, gain * np.cos(th)); place(buf[1], t, x, gain * np.sin(th))
    prog = []; lead = []; arpt = []; sec_of = []
    for si, (P, M, at) in enumerate(SECTIONS):
        for b in range(4): prog.append(P[b]); lead.append(M[b]); arpt.append(at); sec_of.append(si)
    assert len(prog) == NBAR
    for b, c in enumerate(prog):
        t0 = b * BAR; bass, pool = CH[c]
        # 柔和 pad：三個和弦音，慢起慢收，左右失諧
        for k, m in enumerate(pool[1:4]):
            for det, pan in ((0.997, -0.55), (1.003, 0.55)):
                put(bus, softsine(mtof(m) * det, BAR + 2.0, a=1.3, r=1.8, harm=(1, 2), amps=(1, .12)), t0 - 0.5, 0.020, pan + 0.1 * (k - 1))
        # 低音：第 1、3 拍（第 3 拍較輕），柔和
        put(bus, softsine(mtof(bass), BEAT * 1.9, a=0.012, r=0.2, decay=1.5, harm=(1, 2), amps=(1, .3)), t0, 0.13, 0)
        put(bus, softsine(mtof(bass + (7 if c in ('F', 'Bb', 'Dm') else 12)), BEAT * 1.4, a=0.012, r=0.2, decay=2.0, harm=(1, 2), amps=(1, .25)), t0 + 2 * BEAT, 0.07, 0)
        # 撥弦琶音：八分音；段 0（intro）和橋較疏
        for i, p in enumerate(ARP[arpt[b]]):
            if (sec_of[b] == 0 and i % 2 == 1) or (sec_of[b] == 4 and i in (1, 5, 7)): continue
            m = pool[p]; v = (1.0 if i % 4 == 0 else 0.62 if i % 2 == 0 else 0.5) * rng.uniform(0.9, 1.08)
            put(bus, gpluck(mtof(m), 1.6, 3.2, rng), t0 + i * BEAT / 2 + rng.normal(0, 0.0025), 0.062 * v, -0.45 + 0.9 * p / 4)
        # 笛／口哨主旋律
        for (bt, m, du) in lead[b]:
            put(bus, whistle_note(mtof(m), du * BEAT + 0.14, rng), t0 + bt * BEAT, 0.082 if sec_of[b] != 4 else 0.07, 0.15)
        # 鐘琴閃光：每 2 小節 1–2 粒，極輕，落喺和弦音／利底亞音（B♮ = 95）
        if b % 2 == 1 or sec_of[b] == 2:
            for k in range(1 + (rng.random() < 0.5)):
                m = int(rng.choice([m + 12 for m in pool[2:]] + ([95] if c in ('G', 'F') else []))); m = m + 12 if m < 83 else m
                put(bus, bell(mtof(m), 1.2, decay=5, a=0.002, r=0.05), t0 + rng.choice([0.5, 1.5, 2.5, 3.0, 3.5]) * BEAT + rng.uniform(0, 0.02), 0.022, rng.uniform(-0.6, 0.6))
    # 鳥鳴：約 9 組，3–5.5 kHz，極輕、疏落（分佈喺循環內）
    for tb in np.linspace(5, N / SR - 6, 9) + rng.uniform(-1.5, 1.5, 9):
        pan = rng.uniform(-0.8, 0.8); nn = rng.integers(2, 5); f0 = rng.uniform(3000, 4600)
        for k in range(nn):
            d = rng.uniform(0.045, 0.09); up = rng.random() < 0.6
            put(air_b, chirp(rng, f0 * (1 if up else 1.12), f0 * (1.18 if up else 0.92) * rng.uniform(.97, 1.03), d, 0.01), tb + k * rng.uniform(0.11, 0.16), 0.016, pan)
    # 環境風：圓周濾波噪音＋慢 LFO
    f = np.fft.rfftfreq(N, 1 / SR); tN = np.arange(N) / SR
    for ch, sd in ((0, 1), (1, 2)):
        x = np.random.default_rng(seed + sd).standard_normal(N); X = np.fft.rfft(x)
        H = (1 / (1 + (250 / np.maximum(f, 1e-9)) ** 2)) * (1 / (1 + (f / 1100) ** 4)); air = np.fft.irfft(X * H, N); air /= np.std(air)
        bus[ch][:N] += 0.017 * air * (0.5 + 0.5 * np.sin(2 * np.pi * tN / (6 * BAR) + 1.3 * sd))
    def fold(buf): y = buf[:N].copy(); tl = buf[N:]; y[:len(tl)] += tl; return y
    M = [fold(bus[0]), fold(bus[1])]; A = [fold(air_b[0]), fold(air_b[1])]
    def circ_verb(x, sd, wet, rt):
        r = np.random.default_rng(sd); ir = verb_ir(r, rt=rt, pre=0.015, damp=4000, length=min(rt * 1.6, 6)); irp = np.zeros(N); irp[:len(ir)] = ir
        return (1 - wet * 0.5) * x + wet * np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(irp), N)
    y = np.stack([circ_verb(M[0], seed + 11, 0.34, 2.0) + circ_verb(A[0], seed + 31, 0.5, 1.6),
                  circ_verb(M[1], seed + 12, 0.34, 2.0) + circ_verb(A[1], seed + 32, 0.5, 1.6)], axis=1)
    Y = np.fft.rfft(y, axis=0); Y *= (1 / (1 + (40 / np.maximum(f, 1e-9)) ** 4))[:, None]; y = np.fft.irfft(Y, N, axis=0)
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
    name = 'bgm_town_morningmoss_loop'; y, N = render(); g = 0.1
    for it in range(8):
        I, TP = encode(y, f'tmp/{name}.wav', f'bgm/{name}.ogg', g)
        if abs(I + 16) < 0.05 and TP <= -1.0: break
        g *= 10 ** ((-16 - I) / 20)
    print(name, 'bpm', BPM, 'bars', NBAR, 'gain', round(g, 4), 'LUFS', I, 'TP', TP, 'loop sec', N / SR, 'samples', N)
    if TP > -1.0: raise SystemExit('TP > -1 dBTP: 需要降低增益／加限幅')
