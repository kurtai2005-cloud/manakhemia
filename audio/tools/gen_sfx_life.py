"""《微光小圃》團絨生命感（精簡）：8 款 × a/b ＝ 16 個細聲小音效。原創程式合成（numpy/scipy），無取樣、無錄音。
聲線同 gen_sfx_pet2.py 一致（同一套加法共振峰 voice()、同一組母音 V、基頻區 midi 68–86），令團絨聽落係同一隻。
另加：全部 4.2 kHz 二階低通（>4 kHz 能量低）、檔頭 10 ms 餘弦淡入、檔尾 40 ms 餘弦淡出到 0＋10 ms 靜音（防 ogg 尾端殘響 click）、峰值上限 -6 dBFS。
響度：純增益迭代，目標按 LUFS20（解碼後 ogg 無間隔重複 20 次再 ebur128）。輸出 sfx/<name>.ogg（-q:a 3，單聲道 44.1 kHz）。
用法（喺 audio/）：PYTHONPATH=tools python3 tools/gen_sfx_life.py"""
import os, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
from dsp import SR, mtof, tt, bandnoise, place
from measure import ebur
FF = os.environ.get('FF', 'ffmpeg')
rng = np.random.default_rng(20261031)
TMP = 'tmp_life'; os.makedirs(TMP, exist_ok=True)
# ---- 同 gen_sfx_pet2.py 一樣嘅聲線工具（抄過嚟，唔 import，避免重跑佢嘅生成）----
def seq(parts):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def smooth(x, ms):
    n = max(1, int(ms / 1000 * SR)); k = np.ones(n) / n; return np.convolve(np.pad(x, (n, n), mode='edge'), k, 'same')[n:-n]
def contour(pts, d):
    t = tt(d); return mtof(smooth(np.interp(t, [p[0] for p in pts], [p[1] for p in pts]), 12))
def renv(n, a, r):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)[:n]; e[-nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    return e
V = dict(u=(330, 900), o=(470, 1050), a=(820, 1650), e=(520, 2300), i=(360, 2700), n=(300, 1500))
def voice(d, pts, vow, a=0.015, r=0.05, vib=0.008, vibr=6.0, breath=0.04, am=0.0, amr=0.0, jit=0.003, harm=1.6):
    n = int(round(SR * d)); t = np.arange(n) / SR
    f0 = contour(pts, d); wob = smooth(rng.standard_normal(n), 25) * 0.02 * jit / 0.003 * 0.25
    f0 = f0 * (1 + vib * np.sin(2 * np.pi * vibr * t) * np.clip(t / 0.12, 0, 1) + wob)
    ph = 2 * np.pi * np.cumsum(f0) / SR; pos = np.linspace(0, 1, n); xs = [v[0] for v in vow]
    F1 = np.interp(pos, xs, [V[v[1]][0] for v in vow]); F2 = np.interp(pos, xs, [V[v[1]][1] for v in vow])
    y = np.zeros(n)
    for h in range(1, 19):
        fh = h * f0; g = 0.12 + np.exp(-0.5 * ((fh - F1) / 140) ** 2) + 0.7 * np.exp(-0.5 * ((fh - F2) / 260) ** 2)
        y += g * np.clip((9000 - fh) / 3000, 0, 1) / h ** harm * np.sin(h * ph)
    env = renv(n, a, r)
    if am: env = env * (1 - am + am * (0.5 + 0.5 * np.sin(2 * np.pi * amr * t)))
    y = y / np.max(np.abs(y))
    if breath: b = bandnoise(rng, d, 1200, 6500); y = y + breath * b / np.max(np.abs(b))
    return y * env
def puff(d, lo, hi, a=0.01, r=0.05, g=0.3):
    x = bandnoise(rng, d, lo, hi); return g * x / np.max(np.abs(x)) * renv(len(x), a, r)
def thump(f0, f1, d, decay, a=0.008, g=1.0):
    """軟身體落地：低頻下滑正弦（2 次諧波少少），指數衰減。"""
    x = tt(d); f = f0 * (f1 / f0) ** (x / d); ph = 2 * np.pi * np.cumsum(f) / SR
    return g * (np.sin(ph) + 0.25 * np.sin(2 * ph)) * np.exp(-x * decay) * renv(len(x), a, 0.02)
def inhale(d, lo, hi, g=1.0, hitch=None):
    n = int(round(d * SR)); x = bandnoise(rng, d, lo, hi); x = x / np.max(np.abs(x)); e = np.sin(np.pi * np.arange(n) / n) ** 2 * np.linspace(.35, 1, n)
    if hitch: e = e * (1 - 0.7 * np.exp(-0.5 * ((np.arange(n) / SR - hitch) / 0.012) ** 2))   # 中途一下「抽」
    return g * x * e
S = {}; TGT = {}
# 1. 噴嚏：吸氣（漸升）→ 一下停頓 →「啾」（短噪音爆＋高短 voice 'i'→'u' 下滑）
S['sfx_pet_sneeze_a'] = seq([(0, inhale(.17, 700, 2600, .35)), (.215, puff(.045, 1400, 3800, .004, .03, .5)), (.22, voice(.13, [(0, 83), (.13, 77)], [(0, 'i'), (1, 'u')], a=.006, r=.07, breath=.12))])
S['sfx_pet_sneeze_b'] = seq([(0, inhale(.2, 800, 2900, .35, hitch=.09)), (.245, puff(.04, 1500, 4000, .004, .028, .45)), (.25, voice(.11, [(0, 85), (.11, 79.5)], [(0, 'i'), (1, 'e')], a=.006, r=.06, breath=.12)),
                            (.39, voice(.07, [(0, 76), (.07, 74)], [(0, 'n'), (1, 'u')], a=.01, r=.04, breath=.05), .3)])     # b：吸氣中途抽一下＋尾後細細「嗯」
# 2. 抓癢沙沙：柔和帶通噪音短擦，有節奏（a ≈ 11 Hz × 6 下；b ≈ 9 Hz × 5 下，較低較厚）
def scratch(n, rate, lo, hi, d=.05, jitter=.006):
    return seq([(i / rate + rng.uniform(-jitter, jitter) + .005, puff(d, lo * rng.uniform(.9, 1.1), hi, .008, d * .6, 1.0), .7 + .3 * np.sin(np.pi * (i + .5) / n)) for i in range(n)])
S['sfx_pet_scratch_a'] = scratch(6, 11, 900, 3300)
S['sfx_pet_scratch_b'] = scratch(5, 9, 650, 2600, d=.065)
# 3. 蹦跳腳步：軟彈「噗」—— 低頻下滑落地＋細細擠壓氣聲＋極輕上揚「彈」
S['sfx_pet_step_hop_a'] = seq([(0, thump(210, 120, .14, 28)), (.003, puff(.04, 500, 2000, .004, .03, .18)), (.02, thump(300, 420, .08, 35, a=.006, g=.12))])
S['sfx_pet_step_hop_b'] = seq([(0, thump(240, 135, .13, 32)), (.003, puff(.035, 600, 2300, .004, .025, .16)), (.018, thump(340, 470, .07, 40, a=.006, g=.1))])
# 4. 拖步腳步：慢、軟擦地 —— 輕落地＋0.3 s 低頻擦地噪音（先升後落）
def drag(f, d, lo, hi, g=.5):
    n = int(round(d * SR)); x = bandnoise(rng, d, lo, hi); x = x / np.max(np.abs(x)); t = np.arange(n) / n
    return g * x * (np.sin(np.pi * t) ** 1.5 * (0.8 + 0.2 * np.sin(2 * np.pi * f * t * d)))
S['sfx_pet_step_drag_a'] = seq([(0, thump(170, 110, .12, 30, g=.6)), (.04, drag(14, .34, 300, 1600))])
S['sfx_pet_step_drag_b'] = seq([(0, thump(150, 100, .12, 26, g=.55)), (.06, drag(10, .4, 250, 1300, .55))])
# 5. 回頭「咦？」：短鼻音起 → 上揚（a：e→i；b：先輕跌再升，問得更好奇）
S['sfx_pet_turn_huh_a'] = voice(.28, [(0, 76), (.08, 76.5), (.28, 83.5)], [(0, 'n'), (.25, 'e'), (1, 'i')], a=.012, r=.08, vib=.006, breath=.03)
S['sfx_pet_turn_huh_b'] = voice(.32, [(0, 78), (.09, 76.5), (.32, 84.5)], [(0, 'e'), (.4, 'e'), (1, 'i')], a=.012, r=.09, vib=.008, breath=.03)
# 6. 蹭手呼嚕：同 sfx_pet_content 同一種「唔嚕」（u/o 母音＋約 20 Hz 振幅調變），首尾長淡入淡出，可連播
S['sfx_pet_nuzzle_purr_a'] = voice(.58, [(0, 71), (.25, 72.5), (.58, 70.5)], [(0, 'u'), (.5, 'o'), (1, 'u')], a=.09, r=.16, vib=.005, vibr=5, breath=.07, am=.45, amr=21)
S['sfx_pet_nuzzle_purr_b'] = voice(.56, [(0, 72), (.3, 73.5), (.56, 71)], [(0, 'o'), (.5, 'u'), (1, 'o')], a=.1, r=.16, vib=.005, vibr=4.5, breath=.08, am=.5, amr=18)
# 7. 久未見開心叫：急促上行「啾啾啾—！」（比 sfx_pet_happy 更快更高）
S['sfx_pet_reunion_happy_a'] = seq([(0, voice(.08, [(0, 79), (.08, 82)], [(0, 'i'), (1, 'e')], a=.008, r=.03)), (.1, voice(.08, [(0, 81), (.08, 84)], [(0, 'i'), (1, 'e')], a=.008, r=.03), .92),
                                    (.2, voice(.08, [(0, 83), (.08, 86)], [(0, 'i'), (1, 'e')], a=.008, r=.03), .9), (.3, voice(.25, [(0, 84), (.08, 87.5), (.25, 85)], [(0, 'e'), (1, 'a')], vib=.014, vibr=9, a=.01, r=.1), .88)])
S['sfx_pet_reunion_happy_b'] = seq([(0, voice(.1, [(0, 78), (.1, 83)], [(0, 'e'), (1, 'i')], a=.008, r=.035)), (.13, voice(.09, [(0, 82), (.09, 85)], [(0, 'i'), (1, 'e')], a=.008, r=.035), .92),
                                    (.25, voice(.3, [(0, 83), (.07, 86.5), (.18, 87), (.3, 84)], [(0, 'i'), (.4, 'e'), (1, 'a')], vib=.016, vibr=10, a=.01, r=.12), .9)])
# 8. 拍蟲：軟「啪」（短低通噪音＋悶響）→ 細微反應（a：「噗」短鼻音；b：細細「咿」上揚）
def pat(g=1.0, f=260):
    return seq([(0, puff(.03, 400, 2400, .003, .022, .6)), (0, thump(f, f * .65, .07, 45, g=.5))]) * g
S['sfx_pet_bug_pat_a'] = seq([(0, pat()), (.17, voice(.1, [(0, 77), (.1, 74)], [(0, 'o'), (1, 'n')], a=.012, r=.05, breath=.03), .4)])
S['sfx_pet_bug_pat_b'] = seq([(0, pat(1.0, 300)), (.07, pat(.45, 330)), (.2, voice(.12, [(0, 79), (.12, 82)], [(0, 'e'), (1, 'i')], a=.012, r=.06, breath=.03), .35)])
for k in S: TGT[k] = -20.0
for k in ['scratch', 'step_hop', 'step_drag', 'bug_pat']:
    for v in 'ab': TGT[f'sfx_pet_{k}_{v}'] = -22.0
for v in 'ab': TGT[f'sfx_pet_reunion_happy_{v}'] = -18.0
# ---- 後處理＋編碼＋響度 ----
LP = butter(2, 4200 / (SR / 2), output='sos'); CEIL = 10 ** (-6 / 20)
def lufs20(path):
    x, sr = sf.read(path); sf.write('/tmp/_l20.wav', np.tile(x, 20), sr, subtype='FLOAT'); return ebur('/tmp/_l20.wav')[0]
def enc(x, k):
    sf.write(f'{TMP}/{k}.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{TMP}/{k}.wav', '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '3', '-fflags', '+bitexact', '-flags:a', '+bitexact', f'sfx/{k}.ogg'], check=True)
for k, v in S.items():
    assert len(v) <= int(.59 * SR), (k, len(v) / SR)
    v = sosfiltfilt(LP, v - np.mean(v))
    na = int(.010 * SR); v[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nf = int(.04 * SR); v[-nf:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf); v = np.concatenate([v, np.zeros(int(.01 * SR))])
    v = v / np.max(np.abs(v)) * 0.25; g = 0.0
    for _ in range(5):
        y = v * 10 ** (g / 20)
        if np.max(np.abs(y)) > CEIL: y = y / np.max(np.abs(y)) * CEIL
        enc(y, k); x, _ = sf.read(f'sfx/{k}.ogg')
        if np.max(np.abs(x)) > CEIL * 1.02: g -= 20 * np.log10(np.max(np.abs(x)) / CEIL) + .1; continue
        L = lufs20(f'sfx/{k}.ogg')
        if abs(L - TGT[k]) <= .15 or (L < TGT[k] and np.max(np.abs(y)) >= CEIL * .999): break
        g += TGT[k] - L
    print(f'{k:28s} target {TGT[k]:6.1f}  LUFS20 {L:6.1f}')
import shutil; shutil.rmtree(TMP, ignore_errors=True)
print(len(S), 'life sfx generated')
