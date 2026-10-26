#!/usr/bin/env python3
"""decay_weiguang.py — 《微光小圃》需求衰減／離線推算／CQ 分支 模擬（遊測）

數值全部取自 pet-one-pager.md v1（第 4、5、7、14 節）。一頁設計冇寫明嘅地方，用 ASSUME_* 標明，屬「遊測假設」，唔係設計事實。
  python3 decay_weiguang.py [--runs 300] [--out out/decay_results.md]
純 Python 3（無套件）。亂數固定種子，可重現。

模型：步長 0.25h。session＝玩家開 app 嘅瞬間（1–3 分鐘，視為瞬間）；兩次 session 之間＝離線。
 離線權重 w（等效 E 公式）：離線 <8h → 1；8–24h → 0.25；>24h → 0。需求衰減、便便、睡眠回復、成長都按 w 縮放。
 離線保底：離線時需求唔會被「離線推算」降到 20 以下（原本已 <20 就唔再降）。
 離線成長：只按 w×50%。（⇒ 每日 5 次 session 嘅玩家，成長其實長期只有 50% 速度，詳見報告）
"""
import argparse, os, random, statistics as S, math

# ---------- 設計數值（pet-one-pager v1） ----------
D = dict(
    decay=dict(hunger=6.0, mood=4.0, clean=3.0, energy=5.0),   # 清醒時 /h
    sleep_regen=12.0, sleep_mult=0.3,
    poop_every=3.0, poop_cap=3, poop_clean_extra=1.0,
    feed=dict(snack=20, meal=40), play=15, minigame=(8, 20), wash=50,
    good=60, warn=30, ill=15,
    sick_low_h=2.0, sick_p=0.40, sick_poops=3, weak_after_h=24.0, weak_growth=0.7,
    off_full=8.0, off_rate=0.25, off_cap=24.0, off_floor=20.0, off_growth=0.5,
    stage_h=dict(egg=10 / 60, chick=24, teen=72, adult=168, elder=96),
    cq_up=60, cq_down=30, branch=(70, 40),
)
# ---------- 遊測假設（設計未寫明） ----------
ASSUME = dict(
    cq0=50,            # ASSUME_CQ0：每階段開始 CQ 初值（設計只寫 0–100，冇寫初值／是否重置）
    sick_reroll_h=2.0, # ASSUME：病條件持續時，每 2h 再擲一次 40%
    mg_mood=14,        # ASSUME：迷你遊戲平均回心情（及格 +8／高分 +20，取中間）
    minutes_per_action=0.15, minutes_minigame=0.8,
    poop_asleep='none', floor_on=True,
    lights_off_after=21.0,  # ASSUME：玩家當日最後一次 session 若 ≥21:00 就關燈睡覺
)
DT = 0.25

PROFILES = {
    # 名稱: (session 時間點（時），錯過機率, 行動門檻（need ≤ 此值先處理）, 是否按時關燈)
    '勤力（6 次/日）':   ([8.0, 10.5, 13.0, 16.5, 19.5, 22.5], 0.05, 70, True),
    '一般（4 次/日）':   ([8.0, 12.5, 18.5, 22.0], 0.10, 55, True),
    '上班族（3 次/日：朝、晚、夜）': ([7.5, 19.0, 22.5], 0.10, 55, True),
    '輕度（2 次/日）':   ([8.5, 21.5], 0.15, 45, True),
    '週末失蹤（每 2 日 1 次）': ([20.0], 0.0, 55, True),   # 特別處理：隔日先有 session
}

def w_of(T, P):
    if T < P['off_full']: return 1.0
    if T < P['off_cap']: return P['off_rate']
    return 0.0

def simulate(profile, rng, P=D, A=ASSUME, max_days=120, every_other_day=False):
    times, miss, thr, lights = profile
    s = dict(hunger=80.0, mood=80.0, clean=80.0, energy=80.0)
    poops, poop_t = 0, 0.0
    asleep, sick, cure_pending = False, False, False
    low_t, sick_t, last_roll = 0.0, 0.0, 0.0
    weak = False
    stage_order = ['chick', 'teen', 'adult', 'elder']
    si, growth, cq = 0, 0.0, A['cq0']
    stage_wall = {k: 0.0 for k in stage_order}
    teen_cq = None
    good_h = tot_h = 0.0; teen_ratio = None
    last_sess = 0.0
    t = 0.0
    m = dict(warn_h=0.0, ill_h=0.0, awake_h=0.0, sick_h=0.0, sick_ep=0, actions=0, minutes=0.0, notif_trigger_days={}, sessions=0, open_n=0, open_warn=0, open_floor=0, open_sick=0)
    next_sess = []
    day = 0
    # session 時間表（含 jitter、錯過）
    def day_sessions(d):
        if every_other_day and d % 2 == 1: return []
        out = []
        for h in times:
            if rng.random() < miss: continue
            out.append(d * 24 + h + rng.uniform(-0.5, 0.5))
        return sorted(out)
    sess = day_sessions(0)
    lastday = {}
    while t < max_days * 24 and si < len(stage_order):
        d = int(t // 24)
        if d != day:
            day = d; sess += day_sessions(day)
        # session?
        while sess and sess[0] <= t:
            st_t = sess.pop(0)
            m['sessions'] += 1
            mn = min(s.values()); m['open_n'] += 1
            if mn < P['warn']: m['open_warn'] += 1
            if mn <= P['off_floor'] + 1e-6: m['open_floor'] += 1
            if sick: m['open_sick'] += 1
            # --- session 行動 ---
            acts = 0; mg = 0
            if sick:
                acts += 1; cure_pending = True       # 暖湯（日常可得）＋之後睡一次
            if poops > 0 or s['clean'] <= thr:
                acts += 1; poops = 0; s['clean'] = min(100, s['clean'] + P['wash'])
            for _ in range(2):
                if s['hunger'] <= thr:
                    s['hunger'] = min(100, s['hunger'] + (P['feed']['meal'] if s['hunger'] <= 45 else P['feed']['snack'])); acts += 1
            for _ in range(2):
                if s['mood'] <= thr:
                    if mg == 0 and s['mood'] <= thr - 10:
                        s['mood'] = min(100, s['mood'] + A['mg_mood']); mg += 1
                    else:
                        s['mood'] = min(100, s['mood'] + P['play'])
                    acts += 1
            hr = (st_t % 24)
            if asleep and s['energy'] >= 100: asleep = False
            if (not asleep) and ((lights and hr >= A['lights_off_after']) or s['energy'] <= 25 or cure_pending):
                asleep = True; acts += 1
            m['actions'] += acts; m['minutes'] += 0.25 + acts * A['minutes_per_action'] + mg * A['minutes_minigame']
            last_sess = st_t
        T = t - last_sess
        w = w_of(T, P)
        online = (T < DT)  # 只喺 session 當刻
        # --- 衰減 ---
        mult = P['sleep_mult'] if asleep else 1.0
        extra = poops * P['poop_clean_extra']
        old = dict(s)
        s['hunger'] -= P['decay']['hunger'] * mult * DT * w
        s['mood'] -= P['decay']['mood'] * mult * DT * w
        s['clean'] -= (P['decay']['clean'] + extra) * mult * DT * w
        if asleep:
            s['energy'] = min(100.0, s['energy'] + P['sleep_regen'] * DT * w)
            if s['energy'] >= 100:
                asleep = False
                if cure_pending and sick: sick = False; sick_t = 0.0; weak = False
                cure_pending = False
        else:
            s['energy'] -= P['decay']['energy'] * DT * w
        # 離線保底（設計 7.3）：離線推算唔會令需求降到 off_floor 以下（原本已低過就唔再降）
        for k in s:
            if A.get('floor_on', True):
                s[k] = max(s[k], min(old[k], P['off_floor']))
            s[k] = max(0.0, s[k])
        # 便便（A['poop_asleep']：'full'＝睡眠中照計（字面解讀）；'none'＝睡眠中暫停（遊測假設）；'slow'＝×0.3）
        pm = 1.0 if not asleep else {'full': 1.0, 'none': 0.0, 'slow': P['sleep_mult']}[A['poop_asleep']]
        poop_t += DT * w * pm
        if poop_t >= P['poop_every']:
            poop_t -= P['poop_every']; poops = min(P['poop_cap'], poops + 1)
        # 生病
        if not sick:
            if min(s.values()) < P['ill']: low_t += DT * w
            else: low_t = 0.0
            cond = (low_t >= P['sick_low_h']) or (poops >= P['sick_poops'])
            if cond and w > 0 and (t - last_roll) >= A['sick_reroll_h']:
                last_roll = t
                if rng.random() < P['sick_p']: sick = True; sick_t = 0.0; m['sick_ep'] += 1
        else:
            sick_t += DT * w
            if sick_t >= P['weak_after_h']: weak = True
        # 統計
        avg = sum(s.values()) / 4
        if not asleep: m['awake_h'] += DT
        if min(s.values()) < P['warn'] and not asleep: m['warn_h'] += DT
        if min(s.values()) < P['ill'] and not asleep: m['ill_h'] += DT
        if sick: m['sick_h'] += DT
        hr = t % 24
        if 9 <= hr < 22 and min(s.values()) < P['warn']:
            m['notif_trigger_days'][d] = m['notif_trigger_days'].get(d, 0) + DT
        # CQ（每小時結算；按 w 縮放）
        dcq = (1 if avg >= P['cq_up'] else (-1 if avg < P['cq_down'] else 0))
        if sick: dcq -= 1
        cq = min(100.0, max(0.0, cq + dcq * DT * w))
        if stage_order[si] == 'teen':
            tot_h += DT * w; good_h += DT * w * (1 if (avg >= P['cq_up'] and not sick) else 0)
        # 成長
        g = P['off_growth'] * w * DT
        if sick: g = 0.0
        elif weak: g *= P['weak_growth']
        growth += g
        stage_wall[stage_order[si]] += DT
        if growth >= P['stage_h'][stage_order[si]]:
            if stage_order[si] == 'teen': teen_cq = cq; teen_ratio = 100 * good_h / max(tot_h, 1e-9)
            si += 1; growth = 0.0; cq = A['cq0']
        t += DT
    m['days'] = t / 24
    m['stage_wall'] = stage_wall; m['teen_cq'] = teen_cq; m['teen_ratio'] = teen_ratio; m['finished'] = si >= len(stage_order)
    return m

def prev_ok(k, s, P):  # 離線保底簡化：需求 <20 且係離線衰減造成 → 夾返 20（只對剛由 >=20 跌落嘅情況）
    return False

def run_profile(name, prof, runs, P=D, A=ASSUME, seed=1):
    rng = random.Random(seed)
    eod = name.startswith('週末')
    res = [simulate(prof, rng, P, A, every_other_day=eod) for _ in range(runs)]
    return res

def summarize(res, P=D):
    n = len(res)
    days = [r['days'] for r in res]
    awake = [max(r['awake_h'] if 'awake_h' in r else 1, 1) for r in res]
    warn = S.mean(r['warn_h'] / max(r['awake_h'], 1) for r in res) * 100
    ill = S.mean(r['ill_h'] / max(r['awake_h'], 1) for r in res) * 100
    sick_pd = S.mean(r['sick_ep'] / r['days'] for r in res)
    sick_h = S.mean(r['sick_h'] / (r['days'] * 24) for r in res) * 100
    act_pd = S.mean(r['actions'] / r['days'] for r in res)
    min_pd = S.mean(r['minutes'] / r['days'] for r in res)
    notif = S.mean(sum(1 for v in r['notif_trigger_days'].values() if v > 0) / r['days'] for r in res) * 100
    cqs = [r['teen_cq'] for r in res if r['teen_cq'] is not None]
    hi = 100 * sum(1 for c in cqs if c >= P['branch'][0]) / max(len(cqs), 1)
    lo = 100 * sum(1 for c in cqs if c < P['branch'][1]) / max(len(cqs), 1)
    mid = 100 - hi - lo
    rts = [r['teen_ratio'] for r in res if r['teen_ratio'] is not None]
    rhi = 100 * sum(1 for c in rts if c >= P['branch'][0]) / max(len(rts), 1); rlo = 100 * sum(1 for c in rts if c < P['branch'][1]) / max(len(rts), 1)
    open_warn = 100 * sum(r['open_warn'] for r in res) / max(sum(r['open_n'] for r in res), 1)
    open_floor = 100 * sum(r['open_floor'] for r in res) / max(sum(r['open_n'] for r in res), 1)
    sw = {k: S.mean(r['stage_wall'][k] / 24 for r in res) for k in ('chick', 'teen', 'adult', 'elder')}
    return dict(warn=warn, ill=ill, sick_pd=sick_pd, sick_h=sick_h, act=act_pd, minutes=min_pd, notif=notif,
                cq=(S.mean(cqs) if cqs else float('nan')), ratio=(S.mean(rts) if rts else float('nan')), rhi=rhi, rlo=rlo, open_warn=open_warn, open_floor=open_floor, hi=hi, mid=mid, lo=lo, stage=sw, total=sum(sw.values()))

# ---------- 靜態：需求「由滿到空」時間 ----------
def static_table(P=D):
    L = ['| 需求 | 衰減/h | 100→30（警告） | 100→15（不適） | 100→0 | 睡眠中 100→30 |', '|---|---|---|---|---|---|']
    nm = dict(hunger='飽腹', mood='心情', clean='清潔', energy='精力')
    for k, r in P['decay'].items():
        if k == 'energy':
            L.append('| %s | %.1f | %.1fh | %.1fh | %.1fh | 睡眠 +%.0f/h（回滿約 %.1fh） |' % (nm[k], r, 70 / r, 85 / r, 100 / r, P['sleep_regen'], 100 / P['sleep_regen']))
        else:
            L.append('| %s | %.1f | %.1fh | %.1fh | %.1fh | %.1fh |' % (nm[k], r, 70 / r, 85 / r, 100 / r, 70 / (r * P['sleep_mult'])))
    r = P['decay']['clean']
    L.append('| 清潔（已有 3 個便便） | %.1f | %.1fh | %.1fh | %.1fh | — |' % (r + 3, 70 / (r + 3), 85 / (r + 3), 100 / (r + 3)))
    return '\n'.join(L)

def daily_need(P=D):
    """每日（16h 清醒＋8h 睡眠）需求總損耗與最少行動數（理論）"""
    awake, sl = 16, 8
    rows = ['| 需求 | 每日損耗 | 對應最少行動 |', '|---|---|---|']
    h = P['decay']['hunger'] * (awake + sl * P['sleep_mult'])
    mo = P['decay']['mood'] * (awake + sl * P['sleep_mult'])
    cl = P['decay']['clean'] * (awake + sl * P['sleep_mult']) + P['poop_clean_extra'] * 1.5 * 24 * 0.8
    rows.append('| 飽腹 | −%.1f | 約 %.1f 次正餐（+40）或 %.1f 次小點 |' % (h, h / 40, h / 20))
    rows.append('| 心情 | −%.1f | 約 %.1f 次逗玩（+15）或 %.1f 次迷你遊戲（+14） |' % (mo, mo / 15, mo / 14))
    rows.append('| 清潔 | −%.1f（含便便） | 約 %.1f 次沖洗（+50） |' % (cl, cl / 50))
    rows.append('| 精力 | 清醒 −%d／睡 +%d | 每日睡約 %.1fh（%.0f→100） |' % (P['decay']['energy'] * awake, P['sleep_regen'] * sl, P['decay']['energy'] * awake / P['sleep_regen'], 100 - P['decay']['energy'] * awake))
    return '\n'.join(rows)

def fmt(sm_by_profile):
    L = ['| 玩家類型 | 開 app 時有需求<30% | 開 app 時有需求跌到保底 20% | 警告(<30)佔清醒時間% | 生病次/日 | 行動/日 | 分鐘/日 | 通知觸發日% | 跳跳期末 CQ(累加制) | ≥70 燦光 | 40–69 柔光 | <40 微塵 | 良好時數比例（替代制） | 替代制 ≥70／<40 |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for name, x in sm_by_profile.items():
        L.append('| %s | %.0f | %.0f | %.1f | %.3f | %.1f | %.1f | %.0f | %.1f | %.0f%% | %.0f%% | %.0f%% | %.0f%% | %.0f%%／%.0f%% |' % (
            name, x['open_warn'], x['open_floor'], x['warn'], x['sick_pd'], x['act'], x['minutes'], x['notif'], x['cq'], x['hi'], x['mid'], x['lo'], x['ratio'], x['rhi'], x['rlo']))
    return '\n'.join(L)

def stage_fmt(sm_by_profile):
    L = ['| 玩家類型 | 芽崽（設計 24h） | 跳跳期（3 日） | 守夜者（7 日） | 靜光（4 日） | 合計（設計 ≈14 日） |', '|---|---|---|---|---|---|']
    for name, x in sm_by_profile.items():
        s = x['stage']
        L.append('| %s | %.1f 日 | %.1f 日 | %.1f 日 | %.1f 日 | %.1f 日 |' % (name, s['chick'], s['teen'], s['adult'], s['elder'], x['total']))
    return '\n'.join(L)

def variant(**kw):
    import copy
    P = copy.deepcopy(D)
    for k, v in kw.items():
        if isinstance(v, dict): P[k].update(v)
        else: P[k] = v
    return P

DEC15 = dict(hunger=5.0, mood=3.4, clean=2.6, energy=4.3)
VARIANTS = {
    '現況（設計 v1；便便睡眠中暫停＝遊測假設）': (D, ASSUME),
    'L 字面解讀：便便睡眠中照計（每 3h +1）': (D, dict(ASSUME, poop_asleep='full')),
    'V1 離線成長 50%→100%': (variant(off_growth=1.0), ASSUME),
    'V2 衰減 −15%（飽腹 5／心情 3.4／清潔 2.6／精力 4.3）': (variant(decay=DEC15), ASSUME),
    'V3 離線累積嘅便便唔觸發生病（sick_poops=4，即只計在線便便）': (variant(sick_poops=4), ASSUME),
    'V4＝V1＋V2＋V3（建議組合；保底維持 20）': (variant(off_growth=1.0, decay=DEC15, sick_poops=4), ASSUME),
    'V6＝V4＋飽腹再放緩 6→4／h（針對輕度玩家）': (variant(off_growth=1.0, decay=dict(DEC15, hunger=4.0), sick_poops=4), ASSUME),
    'V5 反例：V4＋離線保底 20→30（警告／通知失效）': (variant(off_growth=1.0, decay=DEC15, sick_poops=4, off_floor=30.0), ASSUME),
    'CQ 初值假設=0（現況數值）': (D, dict(ASSUME, cq0=0)),
    'CQ 初值假設=30（現況數值）': (D, dict(ASSUME, cq0=30)),
    'CQ 初值假設=70（現況數值）': (D, dict(ASSUME, cq0=70)),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', type=int, default=300)
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'decay_results.md'))
    a = ap.parse_args()
    md = ['# 微光小圃 衰減／CQ 模擬原始結果（由 decay_weiguang.py 生成）', '', '每個玩家類型 %d 次隨機（session 時間 ±30 分鐘、錯過機率、生病擲骰）。' % a.runs, '',
          '## 1. 靜態：需求由滿到警告／不適／空', '', static_table(), '', '## 2. 每日理論損耗', '', daily_need(), '']
    for vn, (P, A) in VARIANTS.items():
        md += ['## 3. 模擬：' + vn, '']
        sm = {name: summarize(run_profile(name, prof, a.runs, P, A, seed=11), P) for name, prof in PROFILES.items()}
        md += [fmt(sm), '', stage_fmt(sm), '']
    out = '\n'.join(md)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf8').write(out + '\n')
    print(out)

if __name__ == '__main__':
    main()
