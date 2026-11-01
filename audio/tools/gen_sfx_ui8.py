"""《微光小圃》萌系 8bit／16bit UI 音效（sfx_ui8_*）。100% 原創程式合成（numpy/scipy），無取樣、無錄音、無第三方素材。
音色：加法合成「帶限」方波／脈衝波（佔空比 12.5／25／50 %，諧波只去到約 9 kHz、逐諧波斜坡收細 → 無混疊、唔刺耳）、
三角波低音、NES 式 sample-and-hold 噪音聲道（再低通）、16bit（SNES 式）低通回聲。音階：C 大調五聲（C D E G A），同 care BGM 相容。
每粒音獨立包絡：餘弦起音 ≥3 ms、餘弦收尾 ≥8 ms（防 click）。總線：HPF 120 Hz、LPF 9 kHz（2 階 zero-phase）、檔頭 3 ms 淡入、
檔尾 15 ms 淡出＋10 ms 靜音。響度：純增益迭代到 LUFS20 目標（解碼後 ogg 無間隔重複 20 次 → ebur128 integrated），sample peak 上限 -1.5 dBFS（編碼前）。
動作時間：MOTION.md（/workspace/game-design/art-pet/ui/style_ref/v2/）2026-11-01 未存在 → 用預設時間（UI ≤0.3 s、轉場約 0.8 s），之後再對拍。
用法（喺 audio/）：PYTHONPATH=tools python tools/gen_sfx_ui8.py"""
import os, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, lfilter
from dsp import SR, mtof, place
from measure import ebur
FF = os.environ.get('FF', 'ffmpeg')
rng = np.random.default_rng(20261101)
TMP = 'tmp_ui8'; os.makedirs(TMP, exist_ok=True)
NOTE = dict(C=0, D=2, E=4, G=7, A=9)
def m(s):  # 'C6' → midi
    return 12 * (int(s[1:]) + 1) + NOTE[s[0]]
def env(n, a, r, decay=0.0):
    e = np.ones(n); na = max(int(.003 * SR), int(a * SR)); nr = max(int(.008 * SR), int(r * SR)); na = min(na, n // 2); nr = min(nr, n - na)
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na); e[n - nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    if decay: e *= np.exp(-np.arange(n) / SR * decay)
    return e
def curve(pts, d):
    t = np.arange(int(round(d * SR))) / SR; return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
def osc(kind, d, pts, duty=.25, a=.003, r=.01, decay=0.0, vib=0.0, vibr=9.0, top=9000.0):
    """kind: 'pulse'（佔空比 duty）／'tri'。pts：[(t, midi)…] 音高曲線（可滑音）。"""
    n = int(round(d * SR)); t = np.arange(n) / SR
    f = mtof(curve(pts, d)) * (1 + vib * np.sin(2 * np.pi * vibr * t)); ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros(n); N = int(top / f.min()) + 1
    for h in range(1, N + 1):
        if kind == 'tri':
            if h % 2 == 0: continue
            A = (8 / np.pi ** 2) * (-1) ** ((h - 1) // 2) / h ** 2
        else:
            A = (2 / (h * np.pi)) * np.sin(np.pi * h * duty)
        if abs(A) < 1e-6: continue
        y += A * np.clip((top - h * f) / 2000, 0, 1) * np.sin(h * ph)
    return y / (np.max(np.abs(y)) + 1e-12) * env(n, a, r, decay)
def noise(d, clock=12000, lp=6000, hp=600, a=.003, r=.02, decay=0.0, clock_end=None):
    """NES 式噪音：隨機 ±1 以 clock Hz sample-and-hold（可由 clock 掃到 clock_end），再帶通。"""
    n = int(round(d * SR)); c = np.geomspace(clock, clock_end or clock, n); idx = np.floor(np.cumsum(c / SR)).astype(int)
    bits = rng.choice([-1.0, 1.0], idx[-1] + 2); y = bits[idx]
    y = sosfiltfilt(butter(2, [hp / (SR / 2), lp / (SR / 2)], 'band', output='sos'), y)
    return y / np.max(np.abs(y)) * env(n, a, r, decay)
def seq(parts, tail=0.0):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts) + int(tail * SR); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def echo(x, delay=.075, fb=.32, mix=.35, lp=3500, reps=4):
    """16bit（SNES 式）回聲：延遲線，每次重複低通。"""
    y = np.concatenate([x, np.zeros(int(delay * SR * reps))]); out = y.copy(); tap = y.copy(); b, a = butter(1, lp / (SR / 2))
    for k in range(1, reps + 1):
        tap = lfilter(b, a, np.concatenate([np.zeros(int(delay * SR)), tap[:-int(delay * SR)]])); out += mix * (fb ** (k - 1)) * tap
    return out
def arp(notes, step, d, duty=.125, decay=18, gains=None, kind='pulse', **kw):
    return seq([(i * step, osc(kind, d, [(0, n), (d, n)], duty, decay=decay, **kw), (gains[i] if gains else 1.0)) for i, n in enumerate(notes)])
S = {}; TGT = {}; SYNC = {}
# ---- 底部分頁切換（彈跳）：兩粒上行跳音＋落地小彈；a/b 唔同音 ----
S['sfx_ui8_tab_switch_a'] = seq([(0, osc('pulse', .05, [(0, m('G5')), (.012, m('C6')), (.05, m('C6'))], .25, decay=25)),
                                 (.05, osc('pulse', .07, [(0, m('G6')), (.015, m('C7')), (.07, m('C7'))], .25, decay=30), .8)])
S['sfx_ui8_tab_switch_b'] = seq([(0, osc('pulse', .05, [(0, m('A5')), (.012, m('D6')), (.05, m('D6'))], .25, decay=25)),
                                 (.05, osc('pulse', .07, [(0, m('A6')), (.015, m('D7')), (.07, m('D7'))], .25, decay=30), .8)])
# ---- 掣按壓（壓扁）：短「啵」下滑（50 % 方波＋三角低音＋極輕噪音 tick）----
S['sfx_ui8_btn_press_a'] = seq([(0, osc('pulse', .09, [(0, m('A5')), (.09, m('E5'))], .5, decay=10)), (0, osc('tri', .09, [(0, m('A4')), (.09, m('E4'))], decay=10), .35),
                                (0, noise(.02, 9000, 5000, 1500, r=.012), .12)])
S['sfx_ui8_btn_press_b'] = seq([(0, osc('pulse', .09, [(0, m('G5')), (.09, m('D5'))], .5, decay=10)), (0, osc('tri', .09, [(0, m('G4')), (.09, m('D4'))], decay=10), .35),
                                (0, noise(.02, 8000, 4500, 1400, r=.012), .12)])
# ---- 閃光（壓扁後回彈）：12.5 % 細脈衝高音琶音＋回聲 ----
S['sfx_ui8_btn_sparkle'] = echo(arp([m('E6'), m('G6'), m('C7'), m('E7')], .03, .06, .125, decay=30, gains=[.7, .8, .9, 1]), .06, .3, .3, 4000, 2)
# ---- 彈窗貼紙彈出：上行「啵—嚶」滑音（帶 vibrato）＋頂音小琶音 ----
S['sfx_ui8_popup_open'] = echo(seq([(0, osc('pulse', .11, [(0, m('C5')), (.09, m('C6')), (.11, m('C6'))], .25, decay=8, vib=.004)),
                                    (.1, arp([m('E6'), m('G6')], .035, .07, .25, decay=25), .7)]), .06, .25, .22, 3500, 1)
# ---- 彈窗撕走（peel）：噪音由高掃低（撕貼紙「嘶」）＋下行方波滑音 ----
S['sfx_ui8_popup_close'] = seq([(0, noise(.14, 16000, 7000, 1800, a=.008, r=.05, clock_end=3000), .35),
                                (.03, osc('pulse', .14, [(0, m('G5')), (.14, m('C5'))], .25, decay=12))])
# ---- toast 跳落：三粒下行（C7 G6 E6）＋落地「噗」小彈（C6→E6）----
S['sfx_ui8_toast_in'] = seq([(0, arp([m('C7'), m('G6'), m('E6')], .035, .05, .25, decay=30, gains=[.6, .7, .8])),
                             (.11, osc('tri', .05, [(0, m('C5')), (.05, m('G4'))], decay=30), .7),
                             (.12, osc('pulse', .08, [(0, m('C6')), (.02, m('E6')), (.08, m('E6'))], .5, decay=25), .8)])
# ---- 紅點抖：A6/G6 快顫（12.5 %）× 6，4 下抖動 ----
S['sfx_ui8_badge_wiggle'] = seq([(i * .035, osc('pulse', .04, [(0, m('A6') if i % 2 == 0 else m('G6'))] * 2, .125, decay=35), 1 - .1 * i) for i in range(6)])
# ---- 心形關閘轉場：下行五聲琶音（C7→C5）＋三角低音 C4，尾段「噗」關門 ----
cl = [m(s) for s in ['C7', 'A6', 'G6', 'E6', 'D6', 'C6', 'A5', 'G5', 'E5', 'C5']]
S['sfx_ui8_transition_heart_close'] = echo(seq([(0, arp(cl, .055, .09, .25, decay=14, gains=list(np.linspace(.9, .6, len(cl))))),
                                                (.0, osc('tri', .6, [(0, m('C4')), (.6, m('C4'))], a=.03, r=.2, decay=2), .45),
                                                (.56, osc('tri', .12, [(0, m('G4')), (.12, m('C4'))], decay=18), .8),
                                                (.56, noise(.05, 4000, 2500, 400, r=.03), .15)]), .08, .3, .3, 3000, 2)
# ---- 心形開閘轉場：三角低音上行＋上行五聲琶音，尾端閃光 ----
op = [m(s) for s in ['C5', 'E5', 'G5', 'A5', 'C6', 'D6', 'E6', 'G6', 'A6', 'C7']]
S['sfx_ui8_transition_heart_open'] = echo(seq([(0, osc('tri', .14, [(0, m('C4')), (.14, m('G4'))], decay=10), .7),
                                               (.05, arp(op, .05, .09, .25, decay=14, gains=list(np.linspace(.6, .9, len(op))))),
                                               (.55, arp([m('E7'), m('C7'), m('G7')], .03, .06, .125, decay=30), .5)]), .08, .3, .3, 3500, 2)
# ---- 確認：C6 E6 G6 → C7（長尾，帶回聲）----
S['sfx_ui8_confirm'] = echo(seq([(0, arp([m('C6'), m('E6'), m('G6')], .04, .05, .25, decay=25)), (.12, osc('pulse', .12, [(0, m('C7'))] * 2, .25, decay=14, vib=.003), .9),
                                 (0, osc('tri', .16, [(0, m('C5'))] * 2, decay=15), .5)]), .06, .25, .22, 3500, 1)
# ---- 取消：G5 → C5 兩粒下行（50 %，柔）----
S['sfx_ui8_cancel'] = seq([(0, osc('pulse', .06, [(0, m('G5'))] * 2, .5, decay=25)), (.06, osc('pulse', .1, [(0, m('C5')), (.1, m('A4'))], .5, decay=18), .9),
                           (0, osc('tri', .16, [(0, m('C4'))] * 2, decay=15), .4)])
# ---- 錯誤：低「噗噗」兩下（A4，50 %＋三角，略向下彎，唔用刺耳不協和）----
bu = lambda: seq([(0, osc('pulse', .08, [(0, m('A4')), (.08, m('A4') - .8)], .5, decay=15)), (0, osc('tri', .08, [(0, m('A3')), (.08, m('A3') - .8)], decay=15), .7)])
S['sfx_ui8_error'] = seq([(0, bu()), (.12, bu(), .85)])
# ---- 開關：on 上行滑 E6→A6；off 下行 A6→E6 ----
S['sfx_ui8_toggle_on'] = seq([(0, osc('pulse', .07, [(0, m('E6')), (.03, m('A6')), (.07, m('A6'))], .25, decay=30)), (0, noise(.012, 10000, 6000, 2000, r=.008), .1)])
S['sfx_ui8_toggle_off'] = seq([(0, osc('pulse', .07, [(0, m('A6')), (.03, m('E6')), (.07, m('E6'))], .25, decay=30)), (0, noise(.012, 10000, 6000, 2000, r=.008), .1)])
for k in S: TGT[k] = -16.0
for k in ['tab_switch_a', 'tab_switch_b', 'btn_press_a', 'btn_press_b', 'confirm']: TGT[f'sfx_ui8_{k}'] = -14.0
for k in ['transition_heart_close', 'transition_heart_open', 'badge_wiggle', 'btn_sparkle']: TGT[f'sfx_ui8_{k}'] = -18.0
# ---- 總線＋編碼＋響度 ----
HP = butter(2, 120 / (SR / 2), 'high', output='sos'); LP = butter(2, 9000 / (SR / 2), output='sos'); CEIL = 10 ** (-1.5 / 20)
def lufs20(path):
    x, sr = sf.read(path); sf.write('/tmp/_u20.wav', np.tile(x, 20), sr, subtype='FLOAT'); return ebur('/tmp/_u20.wav')[0]
def enc(x, k):
    sf.write(f'{TMP}/{k}.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{TMP}/{k}.wav', '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '4', '-fflags', '+bitexact', '-flags:a', '+bitexact', f'sfx/{k}.ogg'], check=True)
for k, v in S.items():
    # 修剪：回聲尾去到 -60 dB 以下就截
    a = np.abs(v); last = np.nonzero(a > a.max() * 1e-3)[0][-1]; v = v[:last + 1]
    v = sosfiltfilt(LP, sosfiltfilt(HP, v - np.mean(v)))
    na = int(.003 * SR); v[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na)
    nf = int(.015 * SR); v[-nf:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nf) / nf); v = np.concatenate([v, np.zeros(int(.01 * SR))])
    v = v / np.max(np.abs(v)) * 0.3; g = 0.0
    for _ in range(6):
        y = v * 10 ** (g / 20)
        if np.max(np.abs(y)) > CEIL: y = y / np.max(np.abs(y)) * CEIL
        enc(y, k); x, _ = sf.read(f'sfx/{k}.ogg')
        if np.max(np.abs(x)) > 10 ** (-1.1 / 20): g -= 20 * np.log10(np.max(np.abs(x)) / CEIL) + .1; continue
        L = lufs20(f'sfx/{k}.ogg')
        if abs(L - TGT[k]) <= .15 or (L < TGT[k] and np.max(np.abs(y)) >= CEIL * .999): break
        g += TGT[k] - L
    print(f'{k:34s} {len(y)/SR:6.3f}s target {TGT[k]:6.1f}  LUFS20 {L:6.1f}')
import shutil; shutil.rmtree(TMP, ignore_errors=True)
print(len(S), 'ui8 sfx generated')
