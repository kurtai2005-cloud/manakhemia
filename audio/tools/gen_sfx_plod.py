"""《微光小圃》團絨重步（plod）：sfx_pet_step_plod_a/b。原創程式合成，無取樣。取代遊程借用 step_hop（volume 0.5、rate 0.82）嘅做法。
風格同 gen_sfx_life.py 一致（同一個 thump()／puff() 做法、4.2 kHz 低通、10 ms 餘弦淡入、40 ms 淡出＋10 ms 靜音、峰值上限 -6 dBFS、
純增益迭代到 LUFS20 目標 -24）。內容：慢、重、軟肉墊踩落泥／草：
  ① 肉墊先輕觸（細高 thump）→ ② 身體重量壓落（低頻下滑 thump 140→70 Hz，2 次諧波＋260–520 Hz「身」令手機喇叭聽到）
  ③ 泥土細碎（300–1400 Hz 疏落短顆粒）④ 草葉輕擦（1.5–3.5 kHz 好細）⑤ 尾段極輕「噗」離地。
用法（喺 audio/）：PYTHONPATH=tools python tools/gen_sfx_plod.py"""
import os, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
from dsp import SR, tt, bandnoise, place
from measure import ebur
FF = os.environ.get('FF', 'ffmpeg')
rng = np.random.default_rng(20261102)
TMP = 'tmp_plod'; os.makedirs(TMP, exist_ok=True)
def seq(parts):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def renv(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)[:n]; e[-nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e
def puff(d, lo, hi, a=0.01, r=0.05, g=0.3):
    x = bandnoise(rng, d, lo, hi); return g * x / np.max(np.abs(x)) * renv(len(x), a, r)
def thump(f0, f1, d, decay, a=0.008, g=1.0, h2=.25, body=0.0):
    x = tt(d); f = f0 * (f1 / f0) ** (x / d); ph = 2 * np.pi * np.cumsum(f) / SR
    return g * (np.sin(ph) + h2 * np.sin(2 * ph) + body * np.sin(3.7 * ph)) * np.exp(-x * decay) * renv(len(x), a, 0.02)
def soil(d, n, lo, hi, g):
    return seq([(rng.uniform(0, d), puff(rng.uniform(.008, .02), lo * rng.uniform(.8, 1.2), hi, .002, .008, rng.uniform(.4, 1.0) * g)) for _ in range(n)] + [(d, np.zeros(10))])
def plod(f0, f1, dec, pre, soil_n, grass_g, lift_t, var):
    return seq([(0, thump(f0 * 2.1, f0 * 1.6, .05, 45, a=.008, g=.18)),                                     # ① 肉墊輕觸
                (pre, thump(f0, f1, .3, dec, a=.012, g=1.0, h2=.8, body=.4)),                              # ② 重量壓落
                (pre, puff(.09, 260, 900, .01, .06, .45)),                                                   #    壓扁氣聲（身）
                (pre + .005, soil(.12, soil_n, 300, 1400, .12)),                                             # ③ 泥土細碎
                (pre + .01, puff(.16, 1500, 3500, .02, .1, grass_g)),                                        # ④ 草葉輕擦
                (lift_t, thump(f0 * 1.9 * var, f0 * 2.3 * var, .06, 40, a=.01, g=.12))])                     # ⑤ 離地小「噗」
S = {'sfx_pet_step_plod_a': plod(140, 70, 13, .035, 7, .05, .3, 1.0),
     'sfx_pet_step_plod_b': plod(125, 64, 11, .045, 9, .06, .33, .94)}
TGT = -24.0
LP = butter(2, 4200 / (SR / 2), output='sos'); CEIL = 10 ** (-6 / 20)
def lufs20(path):
    x, sr = sf.read(path); sf.write('/tmp/_p20.wav', np.tile(x, 20), sr, subtype='FLOAT'); return ebur('/tmp/_p20.wav')[0]
def enc(x, k):
    sf.write(f'{TMP}/{k}.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{TMP}/{k}.wav', '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '3', '-fflags', '+bitexact', '-flags:a', '+bitexact', f'sfx/{k}.ogg'], check=True)
for k, v in S.items():
    assert len(v) <= int(.49 * SR), (k, len(v) / SR)
    v = sosfiltfilt(LP, v - np.mean(v))
    na = int(.010 * SR); v[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nf = int(.04 * SR); v[-nf:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf); v = np.concatenate([v, np.zeros(int(.01 * SR))])
    v = v / np.max(np.abs(v)) * 0.25; g = 0.0
    for _ in range(6):
        y = v * 10 ** (g / 20)
        if np.max(np.abs(y)) > CEIL: y = y / np.max(np.abs(y)) * CEIL
        enc(y, k); x, _ = sf.read(f'sfx/{k}.ogg')
        if np.max(np.abs(x)) > CEIL * 1.02: g -= 20 * np.log10(np.max(np.abs(x)) / CEIL) + .1; continue
        L = lufs20(f'sfx/{k}.ogg')
        if abs(L - TGT) <= .15 or (L < TGT and np.max(np.abs(y)) >= CEIL * .999): break
        g += TGT - L
    print(f'{k:28s} {len(y)/SR:6.3f}s target {TGT:6.1f}  LUFS20 {L:6.1f}')
import shutil; shutil.rmtree(TMP, ignore_errors=True)
