"""《微光小圃》方案 A（週1）：①寵物聲（團絨）＋②事件提示音。原創，程式合成（numpy/scipy），無取樣、無人聲錄音。
寵物聲 = 加法式「共振峰」合成：基頻曲線 × 母音共振峰（細體型，共振峰偏高）→ 似細小生物嘅 coo／啾，唔係人聲錄音。
輸出 tmp/<name>.wav（未歸一）。固定亂數種子。用法（喺 audio/）：PYTHONPATH=tools python tools/gen_sfx_pet2.py"""
import os, numpy as np, soundfile as sf
from scipy.signal import butter, lfilter
from dsp import *
rng = np.random.default_rng(20261030)
os.makedirs('tmp', exist_ok=True)
S = {}
def seq(parts):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def mixs(*a):
    y = np.zeros(max(len(x) for x in a))
    for x in a: y[:len(x)] += x
    return y
def smooth(x, ms):
    n = max(1, int(ms / 1000 * SR)); k = np.ones(n) / n; return np.convolve(np.pad(x, (n, n), mode='edge'), k, 'same')[n:-n]
def contour(pts, d):
    """pts=[(秒, midi)]：喺 midi（對數頻率）內線性內插再平滑 → Hz"""
    t = tt(d); T = [p[0] for p in pts]; M = [p[1] for p in pts]
    return mtof(smooth(np.interp(t, T, M), 12))
def renv(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)[:n]; e[-nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e
# 母音（細體型：共振峰偏高）(F1, F2) Hz
V = dict(u=(330, 900), o=(470, 1050), a=(820, 1650), e=(520, 2300), i=(360, 2700), n=(300, 1500))
def voice(d, pts, vow, a=0.015, r=0.05, vib=0.008, vibr=6.0, breath=0.04, am=0.0, amr=0.0, jit=0.003, amp=None, harm=1.6):
    """vow = [(0..1 位置, 母音名)]；am/amr = 振幅調變（呼嚕／粗糙感）"""
    n = int(round(SR * d)); t = np.arange(n) / SR
    f0 = contour(pts, d)
    wob = smooth(rng.standard_normal(n), 25) * 0.02 * jit / 0.003 * 0.25   # 慢速隨機音高飄
    f0 = f0 * (1 + vib * np.sin(2 * np.pi * vibr * t) * np.clip(t / 0.12, 0, 1) + wob)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    pos = np.linspace(0, 1, n); xs = [v[0] for v in vow]
    F1 = np.interp(pos, xs, [V[v[1]][0] for v in vow]); F2 = np.interp(pos, xs, [V[v[1]][1] for v in vow])
    y = np.zeros(n)
    for h in range(1, 19):
        fh = h * f0
        g = 0.12 + np.exp(-0.5 * ((fh - F1) / 140) ** 2) + 0.7 * np.exp(-0.5 * ((fh - F2) / 260) ** 2)
        g = g * np.clip((9000 - fh) / 3000, 0, 1) / h ** harm
        y += g * np.sin(h * ph)
    env = renv(n, a, r) if amp is None else amp
    if am: env = env * (1 - am + am * (0.5 + 0.5 * np.sin(2 * np.pi * amr * t)))
    y = y / np.max(np.abs(y))
    if breath:
        b = bandnoise(rng, d, 1200, 6500); b = b / np.max(np.abs(b)); y = y + breath * b
    return y * env
def chime(m, d, decay=10, g=1.0): return g * bell(mtof(m), d, decay=decay)
def pat(f=300, g=0.5): return g * glide(f, f * 0.6, 0.06, a=0.003, r=0.03, decay=40)
def puff(d, lo, hi, a=0.01, r=0.05, g=0.3):
    x = bandnoise(rng, d, lo, hi); return g * x * renv(len(x), a, r)
def flutter(d, rate, lo=2500, hi=7000, g=0.2):
    x = bandnoise(rng, d, lo, hi); n = len(x); t = np.arange(n) / SR
    return g * x * (0.5 + 0.5 * np.sin(2 * np.pi * rate * t + 1.5)) ** 1.5 * renv(n, 0.06, 0.15)
def tw(f, d, decay=40, g=1.0):
    x = tt(d); return g * np.sin(2 * np.pi * f * x) * np.exp(-x * decay) * adsr(len(x), 0.002, 0.01)
def padchord(ms, d, a, r, amp=1.0):
    y = 0
    for m in ms: y = y + softsine(mtof(m), d, a=a, r=r, harm=(1, 2), amps=(1, .25)) + softsine(mtof(m) * 1.003, d, a=a, r=r, harm=(1,), amps=(.6,))
    return y * amp / len(ms)
# ---------------- ① 寵物聲（團絨）----------------
# 開心：三音上行「啾啾啾～」
S['sfx_pet_happy'] = seq([(0, voice(.11, [(0, 76), (.11, 79)], [(0, 'i'), (1, 'e')])),
                          (.14, voice(.11, [(0, 79), (.11, 81)], [(0, 'i'), (1, 'e')]), .9),
                          (.28, voice(.22, [(0, 81), (.1, 84.5), (.22, 83.2)], [(0, 'e'), (1, 'a')], vib=.012, vibr=8, r=.1), .85)])
# 滿足：低而暖嘅呼嚕「唔嚕～」
S['sfx_pet_content'] = voice(.85, [(0, 71.5), (.3, 74), (.6, 72), (.85, 70.5)], [(0, 'u'), (.6, 'o'), (1, 'u')], a=.12, r=.3, vib=.006, vibr=5, breath=.08, am=.4, amr=21)
# 肚餓：兩聲哀怨「啾～啾～」（帶抖音，音高先升後垂）
S['sfx_pet_hungry'] = seq([(0, voice(.34, [(0, 76), (.1, 79), (.34, 77)], [(0, 'e'), (.5, 'a'), (1, 'o')], vib=.016, vibr=7, a=.03, r=.12)),
                           (.42, voice(.4, [(0, 75.5), (.12, 78.5), (.4, 74.5)], [(0, 'e'), (.5, 'a'), (1, 'o')], vib=.02, vibr=7, a=.03, r=.18), .9)])
# 睏：氣聲緩降「呼～」
S['sfx_pet_sleepy'] = voice(1.0, [(0, 79), (.25, 78), (.7, 74), (1.0, 70)], [(0, 'u'), (1, 'u')], a=.15, r=.45, vib=.005, vibr=4.5, breath=.38)
# 不適：低緩下垂嘅嗚咽「嗚…嗚」（抖音、微粗糙，唔嚇人）
S['sfx_pet_uncomfortable'] = seq([(0, voice(.46, [(0, 69), (.15, 70.2), (.46, 66.5)], [(0, 'o'), (1, 'u')], vib=.03, vibr=5.5, a=.05, r=.2, am=.15, amr=30)),
                                  (.5, voice(.26, [(0, 67), (.26, 63.5)], [(0, 'o'), (1, 'u')], vib=.03, vibr=5.5, a=.04, r=.14, am=.15, amr=30), .8)])
# 好奇：短「噗」＋上揚疑問「嚕～？」
S['sfx_pet_curious'] = seq([(0, voice(.1, [(0, 74), (.1, 75)], [(0, 'o'), (1, 'o')], a=.01, r=.04)),
                            (.14, voice(.38, [(0, 74), (.12, 74.5), (.38, 83)], [(0, 'u'), (1, 'i')], a=.03, r=.1, vib=.006, breath=.03), .95)])
# 呵欠：吸氣 → 上揚張口「啊～」→ 長長下滑 → 一下嘆氣
n_in = int(.36 * SR)
inh = bandnoise(rng, .36, 500, 2600) * np.sin(np.pi * np.arange(n_in) / n_in) ** 2 * np.linspace(.4, 1, n_in)
S['sfx_pet_yawn'] = seq([(0, inh, .22), (.3, voice(1.0, [(0, 78), (.18, 81.5), (.4, 80.5), (1.0, 69)], [(0, 'u'), (.3, 'a'), (.7, 'o'), (1, 'u')], a=.12, r=.4, vib=.01, vibr=5, breath=.22)),
                         (1.28, puff(.3, 600, 3000, .06, .2, .12))])
# 摸摸：兩個變體（避免重複）
S['sfx_pet_touch_a'] = voice(.23, [(0, 76), (.08, 79), (.23, 78)], [(0, 'u'), (1, 'o')], a=.02, r=.1, vib=.008, breath=.03)
S['sfx_pet_touch_b'] = voice(.21, [(0, 78), (.08, 81), (.21, 79.5)], [(0, 'n'), (.5, 'e'), (1, 'o')], a=.015, r=.09, vib=.008, breath=.03)
# 連點發脾氣：「噗！噗！噗嚕～」鼻音、微粗、下垂
S['sfx_pet_grumpy'] = seq([(0, puff(.03, 800, 3500, .002, .02, .25)), (.005, voice(.11, [(0, 72), (.11, 69)], [(0, 'e'), (1, 'n')], a=.008, r=.04, am=.3, amr=50, breath=.02)),
                           (.16, puff(.03, 800, 3500, .002, .02, .25)), (.165, voice(.11, [(0, 71), (.11, 68)], [(0, 'e'), (1, 'n')], a=.008, r=.04, am=.3, amr=50, breath=.02), .95),
                           (.32, voice(.26, [(0, 70), (.08, 70.5), (.26, 63.5)], [(0, 'e'), (1, 'o')], a=.01, r=.12, vib=.02, vibr=11, am=.35, amr=45, breath=.03), .9)])
# 睡眠呼吸（可循環）：週期 = 1 小節 @68 BPM = 4×(60/68) s，周期性包絡＋圓周濾波 → 無縫
NB = int(round(4 * 60 / 68 * SR)); tb = np.arange(NB) / NB
def cnoise(lo, hi):
    X = np.fft.rfft(rng.standard_normal(NB)); f = np.fft.rfftfreq(NB, 1 / SR)
    H = np.exp(-0.5 * ((np.log(np.maximum(f, 1)) - np.log(np.sqrt(lo * hi))) / (0.5 * np.log(hi / lo) / 1.2)) ** 2)
    y = np.fft.irfft(X * H, NB); return y / np.std(y)
bump = lambda a, b: np.where((tb > a) & (tb < b), np.sin(np.pi * (tb - a) / (b - a)) ** 2, 0.0)
e_in, e_out = bump(.02, .44), bump(.50, .96)
tt_ = tb * NB / SR
tone = np.zeros(NB); fcur = mtof(66 - 2.5 * np.clip((tb - .5) / .46, 0, 1))        # 呼氣時一點點氣聲「咘」（極輕）
tone = np.sin(2 * np.pi * np.cumsum(np.where(tb > .5, fcur, 0)) / SR) * e_out ** 1.5
S['sfx_pet_sleep_breath_loop'] = 0.55 * cnoise(350, 2200) * e_in + 0.45 * cnoise(250, 1500) * e_out + 0.05 * tone + 0.015 * cnoise(80, 300)
# ---------------- ② 事件提示音 ----------------
S['sfx_event_gift_return'] = verb(seq([(i * .1 - (i * i) * .002, pat(300 + 15 * i, .45 + .06 * i)) for i in range(5)] +
    [(.55, puff(.3, 3000, 8000, .05, .15, .12)),
     (.62, voice(.1, [(0, 79), (.1, 83)], [(0, 'i'), (1, 'e')], r=.04)), (.76, voice(.2, [(0, 83), (.08, 86), (.2, 85)], [(0, 'e'), (1, 'a')], r=.08), .9),
     (.92, chime(91, .5, 9), .7), (1.02, chime(96, .6, 8), .6), (1.12, chime(100, .8, 7), .45),
     (1.0, padchord([72, 79, 88], 1.0, .05, .6), .35)]), rng, wet=.22, rt=.8, tail=.1)[:int(1.9 * SR)]
bf = seq([(0, flutter(.5, 22), 1), (.55, flutter(.45, 25, g=.7))] +
         [(.12 + i * .16, chime(m, .6, 12) * (0.75 + 0.25 * np.sin(2 * np.pi * 11 * tt(.6))), .5) for i, m in enumerate([88, 91, 93, 96])] +
         [(.85, chime(100, 1.0, 8), .45), (.85, chime(91 + 12, .9, 9), .2), (.92, chime(96, 1.0, 8), .2)])
S['sfx_event_butterfly_visit'] = verb(bf, rng, wet=.3, rt=.9, tail=.15)[:int(1.8 * SR)]
tm = tt(.6); fm = 3500 * (880 / 3500) ** (tm / .6)
whoosh = (np.sin(2 * np.pi * np.cumsum(fm) / SR) * np.exp(-tm * 3.5) + 0.3 * np.sin(2 * np.pi * np.cumsum(fm * 2.01) / SR) * np.exp(-tm * 6)) * renv(len(tm), .02, .2)
trail = bandnoise(rng, .7, 4000, 10000); trail = trail * np.exp(-np.arange(len(trail)) / SR * 4) * renv(len(trail), .04, .3)
S['sfx_event_meteor_night'] = verb(seq([(0, whoosh, .6), (.02, trail, .1)] +
    [(.5 + i * .12, chime(m, .5, 14), .45 * (0.8 ** i)) for i, m in enumerate([100, 96, 91, 93, 88])] +
    [(1.15, chime(m, 1.2, 4.5), .55) for m in (84, 91)] + [(1.17, chime(100, 1.1, 5), .3), (1.15, padchord([72, 79], 1.2, .1, .7), .25)]),
    rng, wet=.3, rt=1.4, tail=.3)[:int(2.4 * SR)]
rn = seq([(t0, chime(m, .18, 28), g) for t0, m, g in [(0, 91, .35), (.11, 96, .3), (.2, 88, .3), (.33, 93, .25)]] +
         [(.55 + i * .085, chime(m, .6, 8), .45 + .03 * i) for i, m in enumerate([72, 74, 76, 79, 81, 84, 86, 88, 91, 93])] +
         [(.55, padchord([72, 79, 88], 1.8, .6, .9), .5)] + [(1.45 + i * .06, chime(m, 1.0, 5), .3) for i, m in enumerate([96, 100, 103])] +
         [(1.4, chime(96, 1.0, 3.5), .4)])
S['sfx_event_rainbow'] = verb(rn, rng, wet=.3, rt=1.2, tail=.3)[:int(2.4 * SR)]
S['sfx_event_dream_talk'] = verb(seq([(0, voice(.36, [(0, 67), (.15, 69), (.36, 66)], [(0, 'u'), (.5, 'a'), (1, 'o')], a=.06, r=.15, vib=.012, vibr=4, breath=.3)),
    (.44, voice(.5, [(0, 70), (.2, 72), (.5, 67)], [(0, 'n'), (.4, 'o'), (1, 'u')], a=.05, r=.25, vib=.012, vibr=4, breath=.3), .9),
    (1.0, voice(.3, [(0, 63), (.3, 60.5)], [(0, 'u'), (1, 'u')], a=.06, r=.15, breath=.4), .45),
    (1.3, chime(91, .5, 10), .12), (1.45, chime(88, .6, 10), .1)]), rng, wet=.25, rt=1.0, tail=.2)[:int(1.8 * SR)]
S['sfx_event_sulk'] = seq([(0, puff(.14, 600, 3200, .01, .08, .55)),
    (.2, voice(.15, [(0, 66), (.15, 63)], [(0, 'n'), (1, 'o')], a=.01, r=.05, am=.3, amr=45, breath=.03)),
    (.42, voice(.3, [(0, 65), (.1, 65.5), (.3, 59.5)], [(0, 'n'), (1, 'u')], a=.015, r=.15, vib=.02, vibr=9, am=.3, amr=40, breath=.04), .9),
    (.8, tw(150, .15, 22, .8)), (.97, tw(140, .15, 22, .7)), (1.1, puff(.2, 500, 2500, .02, .12, .15))])
snf = lambda: puff(.07, 2200, 6500, .01, .03, 1.0)
dig = lambda: puff(.07, 700, 3800, .006, .04, 1.0)
S['sfx_event_treasure_hunt'] = verb(seq([(.12 * i, snf(), .8) for i in range(3)] + [(.5 + .1 * i, dig(), .9) for i in range(5)] +
    [(1.1, chime(91, .5, 10), .6), (1.2, chime(96, .5, 9), .6), (1.3, chime(100, .7, 8), .55), (1.42, voice(.25, [(0, 83), (.1, 86), (.25, 85)], [(0, 'e'), (1, 'a')], r=.1), .6),
     (1.62, chime(84, 1.0, 4), .45), (1.64, chime(88, 1.0, 4), .34), (1.66, chime(91, 1.0, 4), .34), (1.55, padchord([72, 79], 1.0, .1, .6), .3)]),
    rng, wet=.25, rt=1.0, tail=.2)[:int(2.5 * SR)]
# 閃光日（≤3s 例外）：最長、最閃、最特別 —— 光暈 pad 漸強 + 上行豎琴／鐘琴瀑布 + 滿佈高頻閃粒 + 長和弦 + 下行餘光
pent = [60, 62, 64, 67, 69]; up = [p + 12 * o for o in range(0, 4) for p in pent if p + 12 * o <= 100]
up = [m for m in up if m >= 72][:15]
sh = [(0, padchord([72, 79, 88, 93], 3.0, .9, 1.2), 1.0), (.15, puff(1.4, 5000, 12000, 1.1, .3, 1.0), .05)]
sh += [(.1 + i * .065, chime(m, .9, 6), .6 + .02 * i) for i, m in enumerate(up)]                       # 上行瀑布
sh += [(1.15, chime(m, 1.8, 2.8), .38) for m in (72, 79, 84, 88, 91)] + [(1.17, chime(m, 1.6, 3.5), .28) for m in (96, 100)]  # 長和弦
sh += [(1.6 + i * .08, chime(m, .9, 7), .3 - .012 * i) for i, m in enumerate(up[::-1][:10])]               # 下行餘光
for t0 in np.sort(rng.uniform(.3, 2.6, 64)): sh.append((t0, tw(float(mtof(rng.choice([96, 100, 103, 105, 108]))), .22, 16, 1.0), rng.uniform(.12, .3)))  # 閃粒
S['sfx_event_shiny_day'] = verb(seq(sh), rng, wet=.32, rt=1.5, tail=.4)[:int(3.0 * SR)]
for k, v in S.items():
    v = v - np.mean(v); nf = int(0.04 * SR)
    if k != 'sfx_pet_sleep_breath_loop': v[-nf:] *= np.linspace(1, 0, nf)       # 循環檔唔做尾端淡出
    v = v / np.max(np.abs(v)) * 0.8
    sf.write(f'tmp/{k}.wav', v, SR, subtype='PCM_16' if k != 'sfx_pet_sleep_breath_loop' else 'FLOAT')
print(len(S), 'pet2 sfx generated')
