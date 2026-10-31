"""《微光小圃》H3 雨層：細雨環境聲（2 檔）。原創，程式合成（numpy/scipy），無取樣。固定亂數種子。
用法（喺 audio/）：PYTHONPATH=tools python tools/gen_amb_rain.py   → amb/amb_rain_light_loop.ogg、amb/amb_rain_light_short.ogg
- 全部喺「圓周」（FFT）域合成：底噪、雨粒紋理、疏落雨滴（尾巴繞返開頭）、殘響都係圓周運算 → loop sample-accurate 無縫。
- v2（2026-10-31，遊測：v1 1–8 kHz 只 39–43 %，似悶雨／遠雷）：雨床高通 320 Hz、主力 2–6 kHz 細密雨粒；
  目標 1–8 kHz ≥60 %、<250 Hz ≤10 %、寵物聲 400–1500 Hz ≤12 %、>8 kHz <5 %。冇雷。v1 備份喺 _prev/rain_v1/。
- loop：7 小節 @68 BPM = 24.706 s → 1,089,529 samples（最接近整數樣本）。short：6.0 s（264,600 samples），淡入 1.5 s／淡出 2.0 s。
- 響度：純增益迭代（解碼後 ogg 量 ebur128）至 -27 LUFS；TP ≤ -1 dBTP。ogg Vorbis -q:a 4，-fflags +bitexact。"""
import os, re, subprocess, numpy as np, soundfile as sf
from dsp import SR
FF = os.environ.get('FF', 'ffmpeg'); TMP = 'tmp'; os.makedirs(TMP, exist_ok=True); os.makedirs('amb', exist_ok=True)
TARGET = -27.0
# v2 調音參數（v1：低帶 150–380 主導、雨粒 450/s、bed:tex = 1:0.55 → 1–8 kHz 只 38–41 %，似悶雨／遠雷）
LOW_A, MID_A = 12.0, 0.06      # 低帶／中頻相對電平
TEX_RATE = 1400                # 雨粒微脈衝密度（/s/聲道）
W_BED, W_TEX, W_DROP = 0.55, 0.75, 0.28

def bp(f, lo, hi, n=2, nh=None):
    f = np.maximum(f, 1e-6); nh = n if nh is None else nh
    return 1 / np.sqrt(1 + (lo / f) ** (2 * n)) / np.sqrt(1 + (f / hi) ** (2 * nh))

def H_rain(f):
    """雨聲整體頻譜形狀（v2，2026-10-31 依遊測）：雨床高通 300 Hz（低帶 4 階＋總 HPF 250 Hz 4 階，150–250 Hz 大幅減）＋ 300–420 Hz 細低帶（上沿 6 階）；
    主力 2–6 kHz 細密雨粒；中頻（0.5–2 kHz）凹低避開寵物聲；>7 kHz 4 階陡降（>8 kHz <5 %）。"""
    low = LOW_A * bp(f, 300, 420, 4, 6)
    high = 1.00 * bp(f, 2000, 6000, 3, 3)
    mid = MID_A * bp(f, 600, 2000, 1)
    return (low + high + mid) * bp(f, 250, 7000, 4)

def cfilt(x, H):
    return np.fft.irfft(np.fft.rfft(x, axis=0) * H[:, None], len(x), axis=0)

def cenv(N, rng, comps):
    """圓周慢速強弱（整數週期 → 無縫），comps=[(週期數, 深度 dB)]"""
    t = np.arange(N) / N; g = np.zeros(N)
    for k, db in comps: g += db * np.sin(2 * np.pi * k * t + rng.uniform(0, 2 * np.pi))
    return 10 ** (g / 20)

def drop_shape(rng, kind):
    """單粒雨滴（單聲道），長度 ≤ 0.12 s"""
    L = int(0.12 * SR); t = np.arange(L) / SR; y = np.zeros(L)
    if kind == 'leaf':      # 葉面「滴」：高音極短 tick
        f = rng.uniform(3200, 5200); dk = rng.uniform(90, 180)
        y += np.sin(2 * np.pi * f * t) * np.exp(-t * dk)
        y += 0.4 * rng.standard_normal(L) * np.exp(-t * 400)
    elif kind == 'tile':    # 瓦面「答」：高 tick ＋ 細細低頻「卜」
        f = rng.uniform(2900, 4400); dk = rng.uniform(70, 120)
        y += 0.8 * np.sin(2 * np.pi * f * t) * np.exp(-t * dk)
        f0 = rng.uniform(240, 360); ph = 2 * np.pi * np.cumsum(f0 * (0.75 + 0.25 * np.exp(-t * 40))) / SR
        y += 0.6 * np.sin(ph) * np.exp(-t * 45)
    else:                   # 'plop'：較大粒、低頻下滑
        f0 = rng.uniform(190, 330); ph = 2 * np.pi * np.cumsum(f0 * (0.7 + 0.3 * np.exp(-t * 30))) / SR
        y += np.sin(ph) * np.exp(-t * 32)
        y += 0.35 * np.sin(2 * np.pi * rng.uniform(3300, 4800) * t) * np.exp(-t * 140)
    y *= np.minimum(1, t / 0.0015)            # 1.5 ms 起音，唔 click
    return y

def rain(N, seed):
    rng = np.random.default_rng(seed); f = np.fft.rfftfreq(N, 1 / SR)
    # 1) 底噪：L/R 各自噪音＋少少共有成分（闊而唔散）
    c = rng.standard_normal(N); w = rng.standard_normal((N, 2))
    bed = 0.45 * c[:, None] + w
    bed = cfilt(bed, H_rain(f))                                   # v2：底噪唔再壓暗（去低頻悶感）
    # 2) 雨粒紋理：細密微脈衝（v2：≈1400/s，Rayleigh 振幅）→ 2–6.5 kHz 濾波 ＝ 細粒、柔、隨機密集 patter
    tex = np.zeros((N, 2))
    for ch in range(2):
        k = rng.poisson(TEX_RATE * N / SR); idx = rng.integers(0, N, k)
        np.add.at(tex[:, ch], idx, rng.rayleigh(1.0, k) * rng.choice([-1, 1], k))
    tex = cfilt(tex, H_rain(f) * bp(f, 2000, 6500, 2))
    # 3) 疏落雨滴（Poisson，平均 2.6 粒/s；圓周放置，尾巴繞返開頭）
    drops = np.zeros((N, 2)); k = rng.poisson(2.6 * N / SR)
    for _ in range(k):
        kind = rng.choice(['leaf', 'tile', 'plop'], p=[0.55, 0.30, 0.15])
        s = drop_shape(rng, kind) * rng.lognormal(0, 0.45) * {'leaf': 0.5, 'tile': 0.55, 'plop': 0.6}[kind]
        i = rng.integers(0, N); pan = rng.uniform(0.12, 0.88)
        idx = (i + np.arange(len(s))) % N
        drops[idx, 0] += s * np.sqrt(1 - pan); drops[idx, 1] += s * np.sqrt(pan)
    # 圓周殘響（雨滴落喺園入面嘅少少空間感）
    L = int(0.9 * SR); t = np.arange(L) / SR; ir = np.zeros((N, 2))
    for ch in range(2):
        r = rng.standard_normal(L) * np.exp(-t * 6.9 / 0.7); ir[:L, ch] = r / np.sqrt(np.sum(r ** 2))
    IR = np.fft.rfft(ir, axis=0) * bp(f, 120, 4500, 1)[:, None]
    drops = drops + 0.35 * np.fft.irfft(np.fft.rfft(drops, axis=0) * IR, N, axis=0)
    drops = cfilt(drops, bp(f, 280, 6800, 3))                     # v2：雨滴「卜」低頻亦高通
    # 混音（相對電平；總響度之後先調）
    bed = bed / np.std(bed); tex = tex / np.std(tex); drops = drops / (np.std(drops) + 1e-12)
    y = W_BED * bed * cenv(N, rng, [(2, 1.2), (3, 0.8), (5, 0.5)])[:, None] \
        + W_TEX * tex * cenv(N, rng, [(3, 1.5), (7, 0.8)])[:, None] \
        + W_DROP * drops
    return y - y.mean(axis=0)

def enc(x, out):
    sf.write(f'{TMP}/_rain.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{TMP}/_rain.wav', '-ac', '2', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '4',
                    '-fflags', '+bitexact', '-flags:a', '+bitexact', out], check=True)
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', out, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])

def normalize(x, out):
    g = 0.05
    for _ in range(6):
        I, TP = enc(x * g, out)
        if abs(I - TARGET) < 0.05: break
        g *= 10 ** ((TARGET - I) / 20)
    assert TP <= -1.0, (out, TP)
    print(f'{out}: I={I} LUFS TP={TP} dBTP gain={g:.5f}')

# ---- loop：7 小節 @68 BPM ----
N_LOOP = int(round(7 * 240 / 68 * SR))            # 1,089,529
normalize(rain(N_LOOP, 20261131), 'amb/amb_rain_light_loop.ogg')
# ---- short：6.0 s，同一配方（另一種子），淡入 1.5 s（等功率正弦）／淡出 2.0 s（餘弦） ----
N_S = int(6.0 * SR); y = rain(N_S, 20261132); t = np.arange(N_S) / SR
fin = np.sin(0.5 * np.pi * np.clip(t / 1.5, 0, 1)) ** 2
fout = np.cos(0.5 * np.pi * np.clip((t - (6.0 - 2.0)) / 2.0, 0, 1)) ** 2
normalize(y * (fin * fout)[:, None], 'amb/amb_rain_light_short.ogg')
os.remove(f'{TMP}/_rain.wav')
