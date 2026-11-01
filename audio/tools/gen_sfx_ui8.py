"""《微光小圃》萌系 8bit／16bit UI 音效 v2（sfx_ui8_*）——按遊美 MOTION.md v2（/workspace/game-design/art-pet/ui/style_ref/v2/MOTION.md，2026-11-01）ms 時間軸對拍。
100% 原創程式合成（numpy/scipy），無取樣、無錄音、無第三方素材。v1 備份：audio/_prev/ui8_v1/。
音色：帶限加法方波／脈衝波（佔空比 12.5／25／50 %，諧波只到約 9 kHz 並逐諧波收細）、三角波低音、NES 式 sample-and-hold 噪音、16bit（SNES 式）低通回聲。
音階 C 大調五聲（C D E G A），同 care BGM 相容。每粒音餘弦起音 ≥3 ms、收尾 ≥8 ms。總線：HPF 120 Hz、LPF 9 kHz、檔頭 3 ms 淡入、檔尾 15 ms 淡出＋10 ms 靜音。
響度：純增益迭代到 LUFS20 目標（解碼後 ogg 無間隔重複 20 次 → ebur128），sample peak 上限 -1.5 dBFS（編碼前）。
v2：每個聲嘅 0 ms ＝ 對應 hook 觸發點（見 HOOK 註解）；檔案內 ms 重音點對應動畫關鍵幀。每個聲用自己嘅隨機種子（crc32(檔名)），互不影響。
用法（喺 audio/）：PYTHONPATH=tools python tools/gen_sfx_ui8.py"""
import os, zlib, subprocess, numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, lfilter
from dsp import SR, mtof, place
from measure import ebur
FF = os.environ.get('FF', 'ffmpeg')
TMP = 'tmp_ui8'; os.makedirs(TMP, exist_ok=True)
NOTE = dict(C=0, D=2, E=4, G=7, A=9)
def m(s): return 12 * (int(s[1:]) + 1) + NOTE[s[0]]
MS = lambda x: x / 1000.0
rng = None
def env(n, a, r, decay=0.0):
    e = np.ones(n); na = max(int(.003 * SR), int(a * SR)); nr = max(int(.008 * SR), int(r * SR)); na = min(na, n // 2); nr = min(nr, n - na)
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na); e[n - nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    if decay: e *= np.exp(-np.arange(n) / SR * decay)
    return e
def curve(pts, d):
    t = np.arange(int(round(d * SR))) / SR; return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
def osc(kind, d, pts, duty=.25, a=.003, r=.01, decay=0.0, vib=0.0, vibr=9.0, top=9000.0, amp=None):
    """kind 'pulse'（佔空比 duty）／'tri'；pts＝[(秒, midi)…] 音高曲線；amp＝[(秒, 增益)…] 額外振幅曲線。"""
    n = int(round(d * SR)); t = np.arange(n) / SR
    f = mtof(curve(pts, d)) * (1 + vib * np.sin(2 * np.pi * vibr * t)); ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.zeros(n); N = int(top / f.min()) + 1
    for h in range(1, N + 1):
        if kind == 'tri':
            if h % 2 == 0: continue
            A = (8 / np.pi ** 2) * (-1) ** ((h - 1) // 2) / h ** 2
        else: A = (2 / (h * np.pi)) * np.sin(np.pi * h * duty)
        if abs(A) < 1e-6: continue
        y += A * np.clip((top - h * f) / 2000, 0, 1) * np.sin(h * ph)
    y = y / (np.max(np.abs(y)) + 1e-12) * env(n, a, r, decay)
    if amp: y *= curve(amp, d)
    return y
def noise(d, clock=12000, lp=6000, hp=600, a=.003, r=.02, decay=0.0, clock_end=None, amp=None):
    n = int(round(d * SR)); c = np.geomspace(clock, clock_end or clock, n); idx = np.floor(np.cumsum(c / SR)).astype(int)
    bits = rng.choice([-1.0, 1.0], idx[-1] + 2); y = bits[idx]
    y = sosfiltfilt(butter(2, [hp / (SR / 2), lp / (SR / 2)], 'band', output='sos'), y)
    y = y / np.max(np.abs(y)) * env(n, a, r, decay)
    if amp: y *= curve(amp, d)
    return y
def seq(parts, tail=0.0):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts) + int(tail * SR); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def echo(x, delay=.075, fb=.32, mix=.35, lp=3500, reps=4):
    y = np.concatenate([x, np.zeros(int(delay * SR * reps))]); out = y.copy(); tap = y.copy(); b, a = butter(1, lp / (SR / 2))
    for k in range(1, reps + 1):
        tap = lfilter(b, a, np.concatenate([np.zeros(int(delay * SR)), tap[:-int(delay * SR)]])); out += mix * (fb ** (k - 1)) * tap
    return out
def note(t_ms, n, d=.05, duty=.25, decay=25, g=1.0, kind='pulse', **kw):
    """一粒音，起音峰值對準 t_ms（起音 3 ms → 提早 3 ms 開始）。"""
    return (max(0, MS(t_ms) - .003), osc(kind, d, [(0, n), (d, n)], duty, decay=decay, **kw), g)
B = {}   # name → builder（每個用自己 rng）
TGT = {}
# ===== HOOK sfx_tap：任何 tap ripple 開始（0 ms）。短 "pip" 方波 ~40 ms =====
B['sfx_ui8_tap_a'] = lambda: seq([(0, osc('pulse', .045, [(0, m('C7') - .7), (.008, m('C7')), (.045, m('C7'))], .25, decay=40))])
B['sfx_ui8_tap_b'] = lambda: seq([(0, osc('pulse', .045, [(0, m('A6') - .7), (.008, m('A6')), (.045, m('A6'))], .25, decay=40))])
# ===== HOOK sfx_tab_pop：新 active 泡泡起點（tap 後 40 ms）＝ 0 ms。squash-pop 360 ms：
#   126 ms sx 峰 1.25（pop overshoot）／ 216 ms sy 峰 1.12 ／ 288 ms 回穩；dy 小跳頂 129 ms、落地 257 ms。
#   "pi"（0 ms）→ "pu" 上行重音（126 ms）→ 落地軟 tick（257 ms）
def tab(lo, hi, land):
    return seq([(0, osc('pulse', .07, [(0, lo - .8), (.012, lo), (.09, lo)], .25, decay=14), .9),
                note(126, hi, .12, .25, decay=12, g=1.0, vib=.004),
                (MS(126) - .003, osc('tri', .08, [(0, land + 12), (.08, land + 12)], decay=30), .35),
                (MS(257) - .003, osc('tri', .05, [(0, land + 7), (.05, land)], decay=40), .45),
                (MS(257) - .003, noise(.015, 7000, 4000, 1200, r=.01), .06)])
B['sfx_ui8_tab_switch_a'] = lambda: tab(m('G6'), m('C7'), m('C4'))
B['sfx_ui8_tab_switch_b'] = lambda: tab(m('A6'), m('D7'), m('D4'))
# ===== HOOK sfx_button_squish：按鈕 squish 起點（0 ms）。380 ms：76 ms 壓扁到底（sy .84）／ 190 ms 拉高（sy 1.1）／ 285 ms 回穩。
#   0→76 ms 下滑「啵」＋底部軟 thump（76 ms 重音）→ 190 ms 回彈小上滑 → 285 ms 極輕尾
def press(hi, lo, b):
    return seq([(0, osc('pulse', .08, [(0, hi), (.076, lo), (.08, lo)], .5, decay=8, amp=[(0, .7), (.07, 1.0), (.08, 1.0)])),
                (MS(76) - .003, osc('tri', .07, [(0, b + 7), (.07, b)], decay=30), .5),
                (MS(76) - .003, noise(.02, 8000, 4500, 1300, r=.012), .1),
                (MS(190) - .025, osc('pulse', .09, [(0, lo + 2), (.025, hi + 3), (.09, hi + 3)], .25, decay=16), .55),
                note(285, hi + 7, .04, .125, decay=40, g=.3)])
B['sfx_ui8_btn_press_a'] = lambda: press(m('A5'), m('E5'), m('A3'))
B['sfx_ui8_btn_press_b'] = lambda: press(m('G5'), m('D5'), m('G3'))
# ===== HOOK sfx_sparkle：burst 起點（0 ms）。500–550 ms：粒子 scale 峰 1.1 喺 u=.25（≈130 ms），alpha 1−u² 漸淡。
#   上行 E6 G6 C7（0/40/80 ms）→ E7 最亮（130 ms）→ 閃爍尾 G7 C7 E7（220/310/400 ms）漸弱，約 0.53 s 收
B['sfx_ui8_btn_sparkle'] = lambda: echo(seq([note(0, m('E6'), .05, .125, 30, .55), note(40, m('G6'), .05, .125, 30, .7), note(80, m('C7'), .05, .125, 30, .85),
                                           note(130, m('E7'), .08, .125, 22, 1.0), note(220, m('G7'), .05, .125, 35, .5), note(310, m('C7'), .05, .125, 35, .32),
                                           note(400, m('E7'), .045, .125, 40, .18)]), .06, .3, .25, 4000, 1)
# ===== HOOK sfx_popup_open：彈窗 pop 起點（tap 後 80 ms）＝ 0 ms。sticker pop 420 ms：189 ms scale 1.1（overshoot）／294 ms .96／357 ms 1.02／420 ms 1。
#   "boing" 上滑 C5→C6（0–189 ms，oCubic 快起慢收）→ 189 ms「啵」頂音 → 音高跟 wobble：294 ms 微跌、357 ms 微升，420 ms 定
def popup_open():
    u = np.linspace(0, 1, 12); rise = [(MS(189) * x, m('C5') + 12 * (1 - (1 - x) ** 3)) for x in u]
    pts = rise + [(MS(294), m('C6') - .7), (MS(357), m('C6') + .35), (MS(420), m('C6')), (.44, m('C6'))]
    main = osc('pulse', .44, pts, .25, decay=4, amp=[(0, .8), (MS(189), 1.0), (MS(420), .35), (.44, .3)])
    return echo(seq([(0, main, .85), note(189, m('G6'), .07, .125, 25, .7), note(189, m('C5'), .08, 0, 25, .45, kind='tri')]), .06, .25, .2, 3500, 1)
B['sfx_ui8_popup_open'] = popup_open
# ===== HOOK sfx_popup_peel：peel 起點（tap ✕ 後 150 ms）＝ 0 ms。450 ms：摺角 d＝oCubic(u/.55) → 0–248 ms 撕開（頭快尾慢）；
#   fly 由 203 ms 開始（iBack：先少少後縮、再加速飛走）到 450 ms，alpha 1−iCubic。
#   紙聲 noise 由高掃低（0–248 ms，振幅跟撕開速度遞減）→ 203 ms 起下行滑音（先微升再加速跌）＋輕風聲，450 ms 收
def peel():
    tear = noise(.26, 16000, 7500, 1800, a=.004, r=.04, clock_end=3500, amp=[(0, 1), (.1, .7), (.2, .35), (.26, .15)])
    fl = .26; ptsf = [(0, m('G5')), (.05, m('G5') + .6), (.12, m('E5')), (.2, m('A4')), (fl, m('E4'))]
    fly = osc('pulse', fl, ptsf, .25, a=.006, r=.03, amp=[(0, 1), (.12, .85), (.2, .45), (fl, .1)])
    wind = noise(.25, 6000, 3000, 500, a=.03, r=.06, clock_end=2000, amp=[(0, .3), (.1, 1), (.25, .2)])
    return seq([(0, tear, .55), (MS(203), fly, 1.0), (MS(203), wind, .2)])
B['sfx_ui8_popup_close'] = peel
# ===== HOOK sfx_toast_drop：toast 落到第一下彈（spring z=.32 f=2.4：t0 後 133 ms 第一次到位）＝ 0 ms。
#   之後：+87 ms 最大過衝（向下 31 px）／+220 ms 第二次到位／+439 ms 第三次到位（細）。
#   "dun"（三角低音 G4→C4）＋小鈴（12.5 % C7＋G7）喺 0 ms → +220 ms 細「dun」＋細鈴 → +439 ms 極細鈴
def toast():
    def dun(g): return [(0, osc('tri', .12, [(0, m('G4')), (.04, m('C4')), (.12, m('C4'))], decay=18), .45 * g), (0, osc('pulse', .07, [(0, m('C5'))] * 2, .5, decay=25), .25 * g)]
    def bell(t, g): return [note(t, m('C7'), .22, .25, 7, g), note(t + 2, m('G7'), .14, .125, 12, .35 * g)]
    p = dun(1.0) + bell(4, .8) + [(MS(220) + s, x, gg) for s, x, gg in dun(.4)] + bell(224, .45) + bell(443, .2)
    return seq(p)
B['sfx_ui8_toast_in'] = toast
# ===== HOOK sfx_coin（新）：chip pop 起點（toast t0 後 2000 ms）＝ 0 ms。chip scale [1,1.18,.95,1] 350 ms：117 ms 峰 1.18／233 ms .95。
#   經典收錢 "ding-ding"：G6（0 ms）→ C7 長音（117 ms 重音），233 ms 微 vibrato 跌回，約 0.42 s 收
B['sfx_ui8_coin'] = lambda: echo(seq([note(0, m('G6'), .1, .25, 30, .8), (MS(117) - .003, osc('pulse', .28, [(0, m('C7'))] * 2, .25, decay=9, vib=.004, vibr=8), 1.0),
                                    note(117, m('C6'), .1, 0, 20, .35, kind='tri')]), .06, .22, .18, 3500, 1)
# ===== HOOK sfx_reddot：每次 jiggle 起點（週期 1400 ms，jiggle 520 ms）＝ 0 ms。關鍵：78 ms scale 1.35／rot −14°；182 ms .85／+12°；286 ms 1.12／−7°；390 ms .96／+3°。
#   極輕 12.5 % "bip"：A6（78 ms 主）→ G6（182）→ A6（286）→ G6（390），漸弱
B['sfx_ui8_badge_wiggle'] = lambda: seq([note(78, m('A6'), .05, .125, 25, 1.0), note(182, m('G6'), .05, .125, 28, .75), note(286, m('A6'), .045, .125, 30, .55), note(390, m('G6'), .04, .125, 35, .35)])
# ===== HOOK sfx_iris_close：iris 收起點（tap 後 100 ms）＝ 0 ms。R＝360·(1−iCubic(u))，400 ms（頭慢尾急）→ 400 ms 全遮；
#   中心大心 pop：keys [0,1.2,.95,1.05] → 400／450（峰 1.2）／500／550 ms。
#   下行五聲琶音 C7→C5（音距由疏到密，跟 iCubic 加速）＋漸強低通風聲 → 400 ms 關閘「噗」→ 450 ms 心形「啵」頂音（C6→E6）→ 500／550 ms 細 wobble
def iris_close():
    cl = [m(s) for s in ['C7', 'A6', 'G6', 'E6', 'D6', 'C6', 'A5', 'G5', 'E5', 'C5']]
    N = len(cl); ts = [400 * (1 - (1 - k / N) ** 1.6) for k in range(N)]   # 間距遞減
    p = [note(t, n, .08, .25, 16, .55 + .35 * k / (N - 1)) for k, (t, n) in enumerate(zip(ts, cl))]
    p += [(0, osc('tri', .4, [(0, m('C4')), (.4, m('C4'))], a=.04, r=.03, decay=0), .3),
          (0, noise(.4, 5000, 2500, 400, a=.1, r=.02, clock_end=2500, amp=[(0, .2), (.3, .6), (.4, 1)]), .12),
          (MS(400) - .003, osc('tri', .12, [(0, m('G4')), (.12, m('C4'))], decay=18), 1.0), (MS(400) - .003, noise(.04, 4000, 2500, 400, r=.025), .15),
          (MS(400), osc('pulse', .16, [(0, m('C6')), (.05, m('E6') + .5), (.1, m('E6') - .3), (.15, m('E6')), (.16, m('E6'))], .25, decay=14), .75)]
    return echo(seq(p), .07, .28, .25, 3000, 1)
B['sfx_ui8_transition_heart_close'] = iris_close
# ===== HOOK sfx_iris_open：iris 開起點（tap 後 650 ms）＝ 0 ms。R＝360·oCubic(u)，450 ms（頭急尾慢）；大心頭 30 %（0–135 ms）縮走；
#   最後 30 %（315–450 ms）cover 淡出；手帳卡 pop 由 +100 ms 起每張 +60 ms（各自 ≈ +127 ms 峰）。
#   0 ms 細「啾」下滑（大心縮走）＋三角低音 C4→G4 → 上行五聲琶音 C5→C7（音距由密到疏，跟 oCubic 減速，0–380 ms）→ 尾閃光 E7 G7（420／450 ms）
def iris_open():
    op = [m(s) for s in ['C5', 'E5', 'G5', 'A5', 'C6', 'D6', 'E6', 'G6', 'A6', 'C7']]
    N = len(op); ts = [380 * (k / (N - 1)) ** 1.6 for k in range(N)]       # 間距遞增
    p = [note(t, n, .08, .25, 16, .9 - .3 * k / (N - 1)) for k, (t, n) in enumerate(zip(ts, op))]
    p += [(0, osc('pulse', .12, [(0, m('E6')), (.12, m('C6') - 2)], .125, decay=20), .35),
          (0, osc('tri', .2, [(0, m('C4')), (.12, m('G4')), (.2, m('G4'))], decay=10), .55),
          note(420, m('E7'), .05, .125, 35, .45), note(450, m('G7'), .06, .125, 35, .35)]
    return echo(seq(p), .07, .28, .25, 3500, 1)
B['sfx_ui8_transition_heart_open'] = iris_open
# ===== 無 MOTION hook（v1 設計不變）：confirm／cancel／error／toggle_on／toggle_off =====
B['sfx_ui8_confirm'] = lambda: echo(seq([(0, seq([(i * .04, osc('pulse', .05, [(0, n), (.05, n)], .25, decay=25), 1.0) for i, n in enumerate([m('C6'), m('E6'), m('G6')])])),
                                        (.12, osc('pulse', .12, [(0, m('C7'))] * 2, .25, decay=14, vib=.003), .9), (0, osc('tri', .16, [(0, m('C5'))] * 2, decay=15), .5)]), .06, .25, .22, 3500, 1)
B['sfx_ui8_cancel'] = lambda: seq([(0, osc('pulse', .06, [(0, m('G5'))] * 2, .5, decay=25)), (.06, osc('pulse', .1, [(0, m('C5')), (.1, m('A4'))], .5, decay=18), .9),
                                   (0, osc('tri', .16, [(0, m('C4'))] * 2, decay=15), .4)])
def _bu(): return seq([(0, osc('pulse', .08, [(0, m('A4')), (.08, m('A4') - .8)], .5, decay=15)), (0, osc('tri', .08, [(0, m('A3')), (.08, m('A3') - .8)], decay=15), .7)])
B['sfx_ui8_error'] = lambda: seq([(0, _bu()), (.12, _bu(), .85)])
B['sfx_ui8_toggle_on'] = lambda: seq([(0, osc('pulse', .07, [(0, m('E6')), (.03, m('A6')), (.07, m('A6'))], .25, decay=30)), (0, noise(.012, 10000, 6000, 2000, r=.008), .1)])
B['sfx_ui8_toggle_off'] = lambda: seq([(0, osc('pulse', .07, [(0, m('A6')), (.03, m('E6')), (.07, m('E6'))], .25, decay=30)), (0, noise(.012, 10000, 6000, 2000, r=.008), .1)])
for k in B: TGT[k] = -16.0
for k in ['tap_a', 'tap_b', 'tab_switch_a', 'tab_switch_b', 'btn_press_a', 'btn_press_b', 'confirm']: TGT[f'sfx_ui8_{k}'] = -14.0
for k in ['transition_heart_close', 'transition_heart_open', 'badge_wiggle', 'btn_sparkle']: TGT[f'sfx_ui8_{k}'] = -18.0
HP = butter(2, 120 / (SR / 2), 'high', output='sos'); LP = butter(2, 9000 / (SR / 2), output='sos'); CEIL = 10 ** (-1.5 / 20)
def lufs20(path):
    x, sr = sf.read(path); sf.write('/tmp/_u20.wav', np.tile(x, 20), sr, subtype='FLOAT'); return ebur('/tmp/_u20.wav')[0]
def enc(x, k):
    sf.write(f'{TMP}/{k}.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{TMP}/{k}.wav', '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '4', '-fflags', '+bitexact', '-flags:a', '+bitexact', f'sfx/{k}.ogg'], check=True)
for k, fn in B.items():
    rng = np.random.default_rng(zlib.crc32(k.encode()))
    v = fn(); a = np.abs(v); last = np.nonzero(a > a.max() * 1e-3)[0][-1]; v = v[:last + 1]
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
print(len(B), 'ui8 sfx generated')
