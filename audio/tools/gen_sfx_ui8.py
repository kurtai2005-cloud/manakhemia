"""《微光小圃》HD-2D UI 音效 v3（sfx_ui8_*）——按遊美 /workspace/game-design/art-pet/ui/kit_hd2d/MOTION_HD2D.md（production，2026-11-01）ms 時間軸對拍。
100% 原創程式合成（numpy/scipy），無取樣、無錄音、無第三方素材。v1／v2 備份：audio/_prev/ui8_v1/、audio/_prev/ui8_v2/。
v3 音色（HD-2D「金邊玻璃・寶石光」）：保留 chip 底（柔方波／脈衝 50／25 %，諧波只去到 ~5–6.5 kHz）＋暖三角／正弦 pad（輕微 detune chorus）＋
鋼片琴／鐘琴式鈴（celesta：1,2,3,4.2 倍；glock：1,2.76,5.4 倍，高泛音衰減快，>6.5 kHz 泛音唔生成）＋短 shimmer 閃粒＋短回聲。
音階 C 大調五聲（pad 用 C 大調和弦音），同 care BGM 相容。每粒音餘弦起音 ≥3 ms、收尾 ≥8 ms。
總線：HPF 120 Hz、LPF 9 kHz（2 階 zero-phase）、檔頭 3 ms 淡入、檔尾 15 ms 淡出＋10 ms 靜音。
響度：純增益迭代到 LUFS20 目標（解碼後 ogg 無間隔重複 20 次 → ebur128），sample peak 上限 -1.5 dBFS（編碼前）。
每個檔 0 ms ＝ hook 觸發點；檔內 ms 重音對準 MOTION_HD2D.md 關鍵幀（見各段註解）。每個聲用自己嘅隨機種子（crc32(檔名)）。
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
PENTA = [m(f'{n}{o}') for o in (5, 6, 7) for n in 'CDEGA']
rng = None
def env(n, a, r, decay=0.0):
    e = np.ones(n); na = max(int(.003 * SR), int(a * SR)); nr = max(int(.008 * SR), int(r * SR)); na = min(na, n // 2); nr = min(nr, n - na)
    e[:na] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(na) / na); e[n - nr:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(nr) / nr)
    if decay: e *= np.exp(-np.arange(n) / SR * decay)
    return e
def curve(pts, d):
    t = np.arange(int(round(d * SR))) / SR; return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
def osc(kind, d, pts, duty=.5, a=.003, r=.012, decay=0.0, vib=0.0, vibr=6.0, top=5500.0, amp=None):
    """kind 'pulse'（佔空比 duty）／'tri'／'sine'；pts＝[(秒, midi)…]；amp＝[(秒, 增益)…]。諧波去到 top 為止（逐諧波斜坡收細）。"""
    n = int(round(d * SR)); t = np.arange(n) / SR
    f = mtof(curve(pts, d)) * (1 + vib * np.sin(2 * np.pi * vibr * t)); ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == 'sine': y = np.sin(ph)
    else:
        y = np.zeros(n); N = int(top / f.min()) + 1
        for h in range(1, N + 1):
            if kind == 'tri':
                if h % 2 == 0: continue
                A = (8 / np.pi ** 2) * (-1) ** ((h - 1) // 2) / h ** 2
            else: A = (2 / (h * np.pi)) * np.sin(np.pi * h * duty)
            if abs(A) < 1e-6: continue
            y += A * np.clip((top - h * f) / 1500, 0, 1) * np.sin(h * ph)
    y = y / (np.max(np.abs(y)) + 1e-12) * env(n, a, r, decay)
    if amp: y *= curve(amp, d)
    return y
CEL = [(1, 1.0, 1.0), (2.0, .28, 1.7), (3.0, .09, 2.5), (4.2, .04, 3.5)]
GLK = [(1, 1.0, 1.0), (2.76, .22, 2.0), (5.40, .06, 3.5)]
def bell(n, d=.35, decay=9.0, kind='cel', a=.003, top=6500.0):
    """鋼片琴（cel）／鐘琴（glk）式鈴：少量泛音，高泛音衰減快；>top Hz 泛音唔生成。"""
    f = float(mtof(n)); t = np.arange(int(round(d * SR))) / SR; y = np.zeros(len(t))
    for ratio, A, dk in (CEL if kind == 'cel' else GLK):
        if f * ratio > top: continue
        y += A * np.sin(2 * np.pi * f * ratio * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t * decay * dk)
    return y / np.max(np.abs(y)) * env(len(t), a, .03)
def pad(d, notes, a=.06, r=.12, kind='sine', det=.004, amp=None):
    """暖 pad：每粒音兩把輕微 detune（±det）正弦／三角，慢起慢收。"""
    y = sum(osc(kind, d, [(0, n + s * det * 17.3), (d, n + s * det * 17.3)], a=a, r=r, top=3000) for n in notes for s in (-1, 1))
    y = y / np.max(np.abs(y))
    if amp: y *= curve(amp, d)
    return y
def glints(d, rate_pts, pool, g=1.0, dec=(14, 22), kind='cel', up=None):
    """shimmer 閃粒：Poisson 密度跟 rate_pts（[(秒, 粒/秒)…]）；up＝(lo, hi) 音高隨時間上升（取 pool 內近位）。"""
    y = np.zeros(int(round((d + .3) * SR))); t = 0.0; rates = curve(rate_pts, d)
    while t < d:
        r = max(rates[min(int(t * SR), len(rates) - 1)], 1e-3); t += rng.exponential(1 / r)
        if t >= d or rates[min(int(t * SR), len(rates) - 1)] < .5: continue
        if up: tgt = up[0] + (up[1] - up[0]) * t / d; cand = [p for p in pool if abs(p - tgt) <= 3] or pool; n = rng.choice(cand)
        else: n = rng.choice(pool)
        place(y, t, bell(n, .25, rng.uniform(*dec), kind), rng.uniform(.4, 1.0))
    return g * y
def air(d, lo, hi, amp):
    x = rng.standard_normal(int(round(d * SR))); x = sosfiltfilt(butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band', output='sos'), x)
    return x / np.max(np.abs(x)) * env(len(x), .02, .04) * curve(amp, d)
def seq(parts, tail=0.0):
    L = max(int(round(s * SR)) + len(p) for s, p, *_ in parts) + int(tail * SR); y = np.zeros(L)
    for s, p, *g in parts: place(y, s, p, g[0] if g else 1.0)
    return y
def echo(x, delay=.05, fb=.3, mix=.28, lp=3200, reps=2):
    y = np.concatenate([x, np.zeros(int(delay * SR * reps))]); out = y.copy(); tap = y.copy(); b, a = butter(1, lp / (SR / 2))
    for k in range(1, reps + 1):
        tap = lfilter(b, a, np.concatenate([np.zeros(int(delay * SR)), tap[:-int(delay * SR)]])); out += mix * (fb ** (k - 1)) * tap
    return out
def at(t_ms, x, g=1.0): return (max(0, MS(t_ms) - .003), x, g)     # 起音峰值對準 t_ms
B = {}; TGT = {}
# ===== §3 圓章掣／§7 seg：sfx_ui8_tap_a/b。0 ms pointerdown（下沉 0–60 ms）。暖 "pip"：50 % 方波 ＋ 細鈴頭 =====
def tap(n): return seq([at(0, osc('pulse', .05, [(0, n - .5), (.008, n), (.05, n)], .5, decay=20, top=4500)), at(0, bell(n + 12, .08, 30), .3)])
B['sfx_ui8_tap_a'] = lambda: tap(m('C6'))
B['sfx_ui8_tap_b'] = lambda: tap(m('A5'))
# ===== §1 Tab switch 240 ms：sfx_ui8_tab_switch_a/b（交替），0 ms＝撳中。0–60 撳中 tab 縮 .92；新 active 40–240：scale .75→1.08→1（keys [0,.7,1]）→ 180 ms overshoot。
#   0 軟 pip → 40 三角低音起＋上滑 → 180 鈴重音（overshoot）→ 240 回穩、短 shimmer 尾
def tab(lo, hi, bass):
    return echo(seq([at(0, osc('pulse', .045, [(0, lo), (.045, lo)], .5, decay=40, top=4500), .45),
                     at(40, osc('pulse', .14, [(0, lo), (.14, hi - 12)], .25, decay=10, top=5000, amp=[(0, .5), (.14, 1)]), .6),
                     at(40, osc('tri', .22, [(0, bass), (.22, bass)], a=.02, decay=4), .6),
                     at(180, bell(hi, .2, 7), 1.0), at(180, bell(hi - 5, .15, 14, 'glk'), .3),
                     at(240, bell(hi + 7, .1, 24), .22)]), .045, .25, .22, 3200, 1)
B['sfx_ui8_tab_switch_a'] = lambda: tab(m('G5'), m('C7'), m('C4'))
B['sfx_ui8_tab_switch_b'] = lambda: tab(m('A5'), m('D7'), m('D4'))
# ===== §3 Button press：sfx_ui8_btn_press_a/b（隨機），0 ms＝pointerdown；0–60 下沉（scale .97、_p frame）。up（0–120 oBack）冇 hook → 唔包回彈。
#   0–60 暖「啵」下滑（50 % 方波）→ 60 ms 到底軟三角 thump
def press(hi, lo, b):
    return seq([at(0, osc('pulse', .07, [(0, hi), (.06, lo), (.07, lo)], .5, decay=10, top=4500, amp=[(0, .8), (.06, 1.0), (.07, 1.0)])),
                at(60, osc('tri', .07, [(0, b + 7), (.07, b)], decay=30), .55), at(0, bell(hi + 12, .06, 40), .15)])
B['sfx_ui8_btn_press_a'] = lambda: press(m('A5'), m('E5'), m('A3'))
B['sfx_ui8_btn_press_b'] = lambda: press(m('G5'), m('D5'), m('G3'))
# ===== §3 主掣確認後：sfx_ui8_btn_sparkle（同 confirm 一齊播）。fx_spark ×3 喺 200 ms 內 pop ＋ fx_sweep（320 ms，§2 寫法）。
#   0／60／120 三粒鈴 G6 C7 E7（120 最亮）→ 200–520 sweep：上行細閃粒＋短回聲
B['sfx_ui8_btn_sparkle'] = lambda: echo(seq([at(0, bell(m('G6'), .2, 16), .6), at(60, bell(m('C7'), .2, 15), .8), at(120, bell(m('E7'), .25, 12), 1.0),
                                             at(200, glints(.32, [(0, 30), (.32, 12)], PENTA[8:], .35, (18, 28), 'glk', up=(m('E6'), m('A7')))),
                                             at(200, air(.32, 2500, 5000, [(0, 0), (.08, 1), (.32, 0)]), .05)]), .05, .3, .25, 3500, 1)
# ===== confirm（主掣確認／§7 委託完成 stamp 1.6→.9→1，160 ms → 80 ms 落章）：0 暖和弦起 → 80 落章 thump＋鈴重音 C7 → 尾 =====
B['sfx_ui8_confirm'] = lambda: echo(seq([at(0, pad(.3, [m('C5'), m('E5'), m('G5')], a=.01, r=.15, kind='tri'), .35),
                                         at(0, bell(m('E6'), .15, 16), .5), at(40, bell(m('G6'), .15, 16), .6),
                                         at(80, osc('tri', .1, [(0, m('G4')), (.1, m('C4'))], decay=25), .7), at(80, bell(m('C7'), .3, 8), 1.0), at(82, bell(m('G6'), .2, 12, 'glk'), .3)]), .05, .25, .22, 3200, 1)
# ===== cancel（§2「取消」掣，close 200 ms 內收）：0 G5 → 60 E5 → 下滑 C5，暖方波＋三角 =====
B['sfx_ui8_cancel'] = lambda: seq([at(0, osc('pulse', .06, [(0, m('G5'))] * 2, .5, decay=22, top=4500)), at(60, osc('pulse', .12, [(0, m('E5')), (.12, m('C5'))], .5, decay=14, top=4500), .85),
                                   at(0, osc('tri', .18, [(0, m('C4'))] * 2, decay=12), .4), at(60, bell(m('E6'), .1, 25), .15)])
# ===== error（§3 停用掣：左右震 ±1.5 ×2，160 ms → 0／80 ms）：低暖「噗噗」A3／A4，略向下彎，冇刺耳不協和 =====
def _bu(g): return seq([(0, osc('pulse', .07, [(0, m('A4')), (.07, m('A4') - .7)], .5, decay=16, top=3500)), (0, osc('tri', .07, [(0, m('A3')), (.07, m('A3') - .7)], decay=16), .8)])
B['sfx_ui8_error'] = lambda: seq([at(0, _bu(1)), at(80, _bu(1), .85)])
# ===== §2 Popup open 420 ms：sfx_ui8_popup_open，0 ms＝觸發。panel 40–360 keys [0,.55,.8,1]→[.78,1.05,.985,1] → 216 ms overshoot、296 ms .985、360 定；
#   plaque 120–300；金框外光脈衝 200–420（sin → 310 ms 最光）。
#   0 軟 pip → 40–216 暖上滑 C5→C6＋pad 漸強 → 216 鈴重音（C7＋G6）→ 296 微跌 → 200–420 shimmer 跟光脈衝（310 最密）
def popup_open():
    u = np.linspace(0, 1, 12); rise = [(.176 * x, m('C5') + 12 * (1 - (1 - x) ** 3)) for x in u]
    main = osc('pulse', .3, rise + [(MS(256), m('C6') - .5), (MS(320), m('C6')), (.3, m('C6'))], .25, decay=6, top=5000, amp=[(0, .7), (.176, 1.0), (.3, .4)])
    return echo(seq([at(0, osc('pulse', .04, [(0, m('G5'))] * 2, .5, decay=40, top=4500), .35), at(40, main, .7),
                     at(40, pad(.38, [m('C4'), m('G4'), m('E5')], a=.12, r=.15, amp=[(0, .3), (.18, 1), (.38, .6)]), .35),
                     at(216, bell(m('C7'), .3, 9), 1.0), at(218, bell(m('G6'), .25, 11, 'glk'), .35),
                     at(200, glints(.22, [(0, 6), (.11, 30), (.22, 6)], PENTA[7:13], .3, (16, 24)))]), .05, .25, .22, 3200, 1)
B['sfx_ui8_popup_open'] = popup_open
# ===== §2 Popup close 200 ms：sfx_ui8_popup_close，0 ms＝✕／背景撳（0–60 按下）。panel 0–180 scale 1→.9、α 1→0（iCubic：頭慢尾急）。
#   0 軟 pip → 0–180 下滑 C6→C5，振幅跟 1−iCubic（後段急收）＋細 air
def popup_close():
    u = np.linspace(0, 1, 10); amp = [(.18 * x, 1 - x ** 3) for x in u] + [(.19, 0)]
    return seq([at(0, osc('pulse', .04, [(0, m('A5'))] * 2, .5, decay=40, top=4500), .4),
                at(10, osc('pulse', .19, [(0, m('C6')), (.09, m('G5')), (.18, m('C5')), (.19, m('C5'))], .25, a=.006, top=4500, amp=amp)),
                at(10, osc('tri', .19, [(0, m('C5')), (.18, m('C4')), (.19, m('C4'))], amp=amp), .4),
                at(0, air(.18, 1500, 4500, [(0, .5), (.08, 1), (.18, 0)]), .06)])
B['sfx_ui8_popup_close'] = popup_close
# ===== §4 Toast in 220 ms：sfx_ui8_toast_in，0 ms＝出現。toast 0–220 oBack（overshoot 峰 ≈140 ms）；wings 80–260；icon 120–300 scale 0→1.15→1（oBack 峰 ≈234 ms）。
#   0–140 暖滑入 E5→C6 → 140 鈴（overshoot）→ 234 鈴＋閃粒（icon pop）
B['sfx_ui8_toast_in'] = lambda: echo(seq([at(0, osc('pulse', .14, [(0, m('E5')), (.14, m('C6'))], .25, a=.01, decay=6, top=5000, amp=[(0, .6), (.14, 1)]), .6),
                                          at(0, osc('tri', .2, [(0, m('C4'))] * 2, a=.02, decay=8), .4),
                                          at(140, bell(m('G6'), .2, 12), .8), at(234, bell(m('C7'), .25, 10), 1.0), at(236, bell(m('E7'), .15, 18, 'glk'), .25)]), .05, .25, .22, 3200, 1)
# ===== §4 貨幣：sfx_ui8_coin，0 ms＝toast t=140（數字 140–260 數上去、icon 峰 ≈234 → 本檔 94 ms）。
#   0 "ding" G6 → 94 "ding" C7 長鈴（icon 峰）→ 120 數字數完，細閃粒尾
B['sfx_ui8_coin'] = lambda: echo(seq([at(0, bell(m('G6'), .15, 14), .75), at(0, osc('pulse', .05, [(0, m('G6'))] * 2, .25, decay=40, top=5000), .25),
                                      at(94, bell(m('C7'), .35, 7), 1.0), at(94, osc('pulse', .08, [(0, m('C7'))] * 2, .25, decay=30, top=5000), .25),
                                      at(120, glints(.18, [(0, 25), (.18, 5)], PENTA[10:], .25, (20, 30), 'glk'))]), .05, .25, .2, 3200, 1)
# ===== §5 Red dot wiggle 360 ms：sfx_ui8_badge_wiggle，0 ms＝wiggle 起。rotate 0→−12°→10°→−6°→0（90／180／270 ms 極值）、scale 峰 1.1 喺 180 ms。
#   90 A6 → 180 C7（主，scale 峰）→ 270 G6，細鈴「bip」
B['sfx_ui8_badge_wiggle'] = lambda: seq([at(90, bell(m('A6'), .12, 18), .65), at(90, osc('pulse', .03, [(0, m('A6'))] * 2, .25, decay=60, top=5000), .2),
                                         at(180, bell(m('C7'), .15, 15), 1.0), at(180, osc('pulse', .03, [(0, m('C7'))] * 2, .25, decay=60, top=5000), .25),
                                         at(270, bell(m('G6'), .12, 20), .45)])
# ===== §7 toggle：knob 120 ms oBack（overshoot 峰 ≈76 ms）。0 tick → 0–76 滑 → 76 細鈴（落位）=====
def toggle(a_, b_, bl):
    return seq([at(0, osc('pulse', .08, [(0, a_), (.076, b_), (.08, b_)], .5, decay=18, top=4500)), at(76, bell(bl, .1, 22), .45), at(0, air(.012, 2000, 4500, [(0, 1), (.012, 0)]), .08)])
B['sfx_ui8_toggle_on'] = lambda: toggle(m('E5'), m('A5'), m('A6'))
B['sfx_ui8_toggle_off'] = lambda: toggle(m('A5'), m('E5'), m('E6'))
# ===== §6 轉場收：sfx_ui8_transition_veil_close，0 ms＝轉場 t0（撳中 tab／掣，ripple 0–200）。
#   fx_veil 160–700：α keys [0,.35,.65,1]→[0,.88,.88,0] → 160–349 漸強、349–511 全光、511–700 漸退（open 喺 420 接手）。
#   0 軟觸 → 160–349 金色 pad 漸強＋上行閃粒（光幕擴散）→ 349 鈴頂重音（全光）→ 349–420 持續 shimmer → 420 後 ~100 ms 淡走（交畀 open）
def veil_close():
    D = .52
    return echo(seq([at(0, osc('pulse', .04, [(0, m('G5'))] * 2, .5, decay=40, top=4500), .3),
                     (MS(150), pad(D - .15, [m('C4'), m('G4'), m('E5'), m('D5')], a=.18, r=.1, kind='tri', amp=[(0, .2), (.2, 1), (.27, 1), (D - .15, .3)]), .55),
                     (MS(150), air(D - .15, 1800, 5000, [(0, 0), (.2, 1), (.27, .9), (D - .15, 0)]), .05),
                     (MS(160), glints(.26, [(0, 6), (.19, 40), (.26, 30)], PENTA[3:], .38, (12, 20), 'cel', up=(m('E5'), m('C7')))),
                     at(349, bell(m('C7'), .3, 8), .75), at(350, bell(m('G6'), .25, 10, 'glk'), .3)]), .05, .3, .25, 3200, 1)
B['sfx_ui8_transition_veil_close'] = veil_close
# ===== §6 轉場開：sfx_ui8_transition_veil_open，0 ms＝轉場 t=420（新頁出現；返回亦只播呢個）。
#   新頁 0–280 scale 1.06→.99→1；veil 0–91 全光 → 91–280 漸退；卡 pop 100＋40·i（遊程用 popup_open 0.5 音量）；頁框 fx_sweep 280–480。
#   0 暖鈴和弦 bloom（C6 E6 G6＋pad）→ 0–280 下行閃粒漸疏（光幕退）→ 140 低鈴 C5「落定」→ 280–480 上行細閃粒掃（sweep）
def veil_open():
    return echo(seq([at(0, bell(m('C6'), .4, 6), .8), at(5, bell(m('E6'), .35, 7), .6), at(10, bell(m('G6'), .35, 8), .55),
                     (0, pad(.3, [m('C4'), m('G4'), m('E5')], a=.02, r=.15, kind='tri', amp=[(0, 1), (.09, .9), (.28, .2), (.3, .1)]), .5),
                     (0, glints(.28, [(0, 30), (.09, 25), (.28, 3)], PENTA[3:], .3, (12, 20), 'cel', up=(m('C7'), m('E5')))),
                     at(140, bell(m('C5'), .25, 9), .45),
                     (MS(280), glints(.2, [(0, 30), (.2, 15)], PENTA[8:], .28, (20, 30), 'glk', up=(m('E6'), m('A7')))),
                     (MS(280), air(.2, 2500, 5000, [(0, 0), (.06, 1), (.2, 0)]), .04)]), .05, .3, .25, 3200, 1)
B['sfx_ui8_transition_veil_open'] = veil_open
for k in B: TGT[k] = -16.0
for k in ['tap_a', 'tap_b', 'tab_switch_a', 'tab_switch_b', 'btn_press_a', 'btn_press_b', 'confirm']: TGT[f'sfx_ui8_{k}'] = -14.0
for k in ['transition_veil_close', 'transition_veil_open', 'badge_wiggle', 'btn_sparkle']: TGT[f'sfx_ui8_{k}'] = -18.0
MAXL = {f'sfx_ui8_{k}': d for k, d in dict(tap_a=.08, tap_b=.08, tab_switch_a=.32, tab_switch_b=.32, btn_sparkle=.55, confirm=.38, popup_open=.5, toast_in=.42, coin=.42,
        badge_wiggle=.36, toggle_on=.16, toggle_off=.16, transition_veil_close=.56, transition_veil_open=.56).items()}   # 秒（含尾淡出前），再加 10 ms 靜音
HP = butter(2, 120 / (SR / 2), 'high', output='sos'); LP = butter(2, 9000 / (SR / 2), output='sos'); CEIL = 10 ** (-1.5 / 20)
def lufs20(path):
    x, sr = sf.read(path); sf.write('/tmp/_u20.wav', np.tile(x, 20), sr, subtype='FLOAT'); return ebur('/tmp/_u20.wav')[0]
def enc(x, k):
    sf.write(f'{TMP}/{k}.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'{TMP}/{k}.wav', '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '4', '-fflags', '+bitexact', '-flags:a', '+bitexact', f'sfx/{k}.ogg'], check=True)
for k, fn in B.items():
    rng = np.random.default_rng(zlib.crc32(k.encode()))
    v = fn(); a = np.abs(v); last = np.nonzero(a > a.max() * 1e-3)[0][-1]; v = v[:last + 1]
    if k in MAXL and len(v) > int(MAXL[k] * SR):   # 長度上限（對動畫）：截到上限，尾 15 ms 淡出（下面）＋前 40 ms 先收細
        v = v[:int(MAXL[k] * SR)].copy(); nq = int(.04 * SR); v[-nq:] *= np.linspace(1, .5, nq)
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
