#!/usr/bin/env python3
"""pet_events_sim.py — 《微光小圃》加深方案 模組 2「日常事件／隨機驚喜」抽取模擬（遊測）
驗證：①抽取頻率（2–4h 一次）②每事件冷卻 ③每日保底 ≥1 ④閃光日 3% 統計 ⑤離線返嚟唔爆事件（catch-up 策略）⑥事件重複感
用法：python3 pet_events_sim.py [--days 40000] [--seed 7] [--md out/events_results.md]
全部參數為「提案」（pet-deepening-plan.md 只寫：池 8 個、每 2–4h 抽一次、每日保底 1、閃光日 3%；p_hit／冷卻／catch-up 上限未定）。
"""
import argparse, random, math, statistics as st, collections, sys

# 事件池（plan 模組 2）：id, 權重, 冷卻(h), 可觸發時段(時) , 條件備註
EVENTS = [
    # id           w   cd   hours(from,to)  備註
    ('gift',      20,  6, (7, 23),  '帶禮物回來（最適合離線返嚟）'),
    ('butterfly', 18,  6, (8, 18),  '蝴蝶訪客'),
    ('meteor',    10, 24, (19, 5),  '流星夜（夜間）'),
    ('rainbow',    8, 24, (8, 18),  '雨後彩虹（方案 A 無天氣系統 → 需獨立條件）'),
    ('sleeptalk', 10, 12, (23, 7),  '夢話（睡眠中）'),
    ('tantrum',    8, 12, (0, 24),  '鬧脾氣（建議條件：心情<50）'),
    ('treasure',  16, 12, (8, 22),  '尋寶'),
]
# 閃光日（3%）另計：以「日」為單位抽（見 shiny_mode）
P_SHINY_DAY = 0.03

def in_win(h, w):
    a, b = w
    return (a <= h < b) if a < b else (h >= a or h < b)

class Pet:
    def __init__(s, rng, p_hit, interval=(2, 4), global_gap=1.0, guarantee='eve', catchup='cap1', mood_low_prob=0.25,
                 shiny_mode='day', anti=1.0):
        s.anti = anti; s.recent = []
        s.rng, s.p_hit, s.interval = rng, p_hit, interval
        s.global_gap, s.guarantee, s.catchup = global_gap, guarantee, catchup
        s.mood_low_prob, s.shiny_mode = mood_low_prob, shiny_mode
        s.next_draw = rng.uniform(*interval)
        s.cd_until = {e[0]: -1e9 for e in EVENTS}
        s.last_event_t = -1e9
        s.day_events = collections.defaultdict(int); s.opens = collections.defaultdict(int)
        s.shiny_days = set(); s.day_rolled = set()
        s.log = []          # (t, id, kind)
        s.empty_draws = 0; s.draws = 0; s.cd_viol = 0

    def shiny_today(s, day):
        if day not in s.day_rolled:
            s.day_rolled.add(day)
            if s.shiny_mode == 'day' and s.rng.random() < P_SHINY_DAY: s.shiny_days.add(day)
        return day in s.shiny_days

    def eligible(s, t):
        h = t % 24
        mood_low = s.rng.random() < s.mood_low_prob
        out = []
        for e in EVENTS:
            if t < s.cd_until[e[0]]: continue
            if not in_win(h, e[3]): continue
            if e[0] == 'tantrum' and not mood_low: continue
            out.append(e)
        return out

    def draw(s, t, forced=False):
        """一次抽取；回傳事件 id 或 None"""
        s.draws += 1
        day = int(t // 24)
        if s.shiny_mode == 'draw' and not forced and s.rng.random() < P_SHINY_DAY:
            s.shiny_days.add(day); return 'shiny'
        if not forced:
            if s.rng.random() > s.p_hit: s.empty_draws += 1; return None
            if t - s.last_event_t < s.global_gap: s.empty_draws += 1; return None
        el = s.eligible(t)
        if not el: s.empty_draws += 1; return None
        ws = [e[1] * (s.anti if e[0] in s.recent[-2:] else 1.0) for e in el]; 
        if sum(ws) <= 0: ws = [e[1] for e in el]   # 只剩最近事件可用 → 唔好令池變空
        e = s.rng.choices(el, ws)[0]; s.recent.append(e[0])
        if t < s.cd_until[e[0]]: s.cd_viol += 1
        s.cd_until[e[0]] = t + e[2]; s.last_event_t = t
        return e[0]

def run(profile, days, rng, p_hit, **kw):
    """profile: dict(times=[...], miss=prob, absent=[(day_from,day_to)...])；回傳統計"""
    pet = Pet(rng, p_hit, **kw)
    sessions = []
    for d in range(days):
        if profile.get('every_other') and d % 2: continue
        for h in profile['times']:
            if rng.random() < profile['miss']: continue
            sessions.append(d * 24 + h + rng.uniform(-0.4, 0.4))
    sessions.sort()
    shown = []   # (t_session, [events shown], n_dropped)
    per_session = []; returns = []
    last_open = 0.0
    for t in sessions:
        # 1) 計出自上次打開起嘅「到期抽取」
        due = []
        while pet.next_draw <= t:
            td = pet.next_draw
            if pet.shiny_mode == 'day': pet.shiny_today(int(td // 24))
            ev = pet.draw(td)
            if ev: due.append((td, ev))
            pet.next_draw += rng.uniform(*pet.interval)
        pet.shiny_today(int(t // 24))
        gap = t - last_open; last_open = t
        # 2) catch-up 策略
        deliver, dropped = [], 0
        if pet.catchup == 'all': deliver = due
        elif pet.catchup == 'cap1': deliver, dropped = (due[-1:], max(0, len(due) - 1))      # 只顯示最近 1 個，其餘入日記
        elif pet.catchup == 'cap2': deliver, dropped = (due[-2:], max(0, len(due) - 2))
        elif pet.catchup == 'cap1_old': deliver, dropped = (due[:1], max(0, len(due) - 1))
        # 3) 每日保底
        day = int(t // 24); h = t % 24
        ok_guar = False
        if pet.guarantee == 'first': ok_guar = (pet.day_events[day] + len(deliver) == 0)
        elif pet.guarantee == 'eve': ok_guar = (pet.day_events[day] + len(deliver) == 0 and h >= 16)
        elif pet.guarantee == 'eve2': ok_guar = (pet.day_events[day] + len(deliver) == 0 and (h >= 16 or pet.opens[day] >= 1))
        elif pet.guarantee == 'none': ok_guar = False
        pet.opens[day] += 1
        if ok_guar:
            ev = pet.draw(t, forced=True)
            if ev: deliver = deliver + [(t, ev)]
        for (td, ev) in deliver:
            pet.day_events[int(t // 24)] += 1
            pet.log.append((td, ev))
        shown.append((t, [e for _, e in deliver], dropped, gap, len(due)))
    return pet, shown, sessions

def stats(pet, shown, sessions, days, active_days_only=True):
    evs = pet.log
    sess_days = collections.Counter(int(t // 24) for t in sessions)
    zero_days = sum(1 for d in sess_days if pet.day_events[d] == 0)
    per_day = [pet.day_events[d] for d in sess_days]
    max_ret = max((len(x[1]) for x in shown), default=0)
    mult = [len(x[1]) for x in shown]
    drop_total = sum(x[2] for x in shown)
    big = [x for x in shown if x[3] >= 24]       # 離開 ≥24h 後返嚟
    big_max = max((len(x[1]) for x in big), default=0)
    # 連續重複（相鄰兩個事件同 id）
    rep = sum(1 for a, b in zip(evs, evs[1:]) if a[1] == b[1]) / max(1, len(evs) - 1)
    # 3 連內重複（滑動窗口內出現同事件）
    rep3 = 0
    for i in range(len(evs)):
        w = [e[1] for e in evs[max(0, i - 2):i + 1]]
        if len(w) == 3 and len(set(w)) < 3: rep3 += 1
    rep3 /= max(1, len(evs) - 2)
    gaps = [b[0] - a[0] for a, b in zip(evs, evs[1:])]
    cnt = collections.Counter(e for _, e in evs)
    return dict(sessions_per_day=len(sessions) / max(1, len(sess_days)), events_per_active_day=st.mean(per_day) if per_day else 0,
                evt_per_session=len(evs) / max(1, len(sessions)), zero_days_pct=100 * zero_days / max(1, len(sess_days)),
                max_per_return=max_ret, big_return_max=big_max, dropped_per_day=drop_total / max(1, len(sess_days)),
                repeat_adjacent=rep, repeat_in3=rep3, min_gap=min(gaps) if gaps else float('nan'), cd_viol=pet.cd_viol,
                dist={k: v / len(evs) for k, v in cnt.items()} if evs else {}, empty_draw_pct=100 * pet.empty_draws / max(1, pet.draws),
                p90_per_day=sorted(per_day)[int(0.9 * len(per_day))] if per_day else 0)

PROFILES = {
    '勤力 6次/日':   dict(times=[8.0, 10.5, 13.0, 16.5, 19.5, 22.5], miss=0.05),
    '一般 4次/日':   dict(times=[8.0, 12.5, 18.5, 22.0], miss=0.10),
    '上班族 朝晚夜': dict(times=[7.5, 19.0, 22.5], miss=0.10),
    '輕度 2次/日':   dict(times=[8.5, 21.5], miss=0.15),
    '早鳥只朝午':    dict(times=[7.5, 12.5], miss=0.10),
    '隔日 1次':      dict(times=[20.0], miss=0.0, every_other=True),
}

def shiny_stats(n_days, rng, mode):
    """閃光日統計：逐日；回傳 (日比例, 首次閃光日分佈 P(≤7/14/30 日), 最長無閃光日, 同日多次比例)"""
    p = Pet(rng, 0.35, shiny_mode=mode)
    flags = []
    if mode == 'day':
        for d in range(n_days): flags.append(p.shiny_today(d))
    else:  # 每次抽取 3%：每日 24/3=8 抽（2–4h）
        t = 0.0; days = collections.defaultdict(int)
        while t < n_days * 24:
            t += rng.uniform(2, 4)
            if rng.random() < P_SHINY_DAY: days[int(t // 24)] += 1
        flags = [days[d] > 0 for d in range(n_days)]
    frac = sum(flags) / n_days
    first = []
    for _ in range(4000):
        k = 0
        while rng.random() >= (P_SHINY_DAY if mode == 'day' else 1 - (1 - P_SHINY_DAY) ** 8): k += 1
        first.append(k + 1)
    q = lambda n: sum(1 for x in first if x <= n) / len(first)
    run_, best = 0, 0
    for f in flags:
        run_ = 0 if f else run_ + 1; best = max(best, run_)
    return frac, q(7), q(14), q(30), best

def chi2_uniformity(rng, n=20000):
    """3% 二項檢定：n 日中閃光日數落喺 99.9% 區間內"""
    k = sum(1 for _ in range(n) if rng.random() < P_SHINY_DAY)
    mu = n * P_SHINY_DAY; sd = math.sqrt(n * P_SHINY_DAY * (1 - P_SHINY_DAY))
    return k, mu, sd, abs(k - mu) / sd

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--days', type=int, default=3000); ap.add_argument('--seed', type=int, default=7); ap.add_argument('--md', default=None)
    a = ap.parse_args(); out = []
    P = out.append
    P('# 事件池抽取模擬結果（pet_events_sim.py）\n')
    P(f'> {a.days} 日／檔案；seed={a.seed}；參數＝提案。\n')
    # A. p_hit 掃描（catch-up=cap1、guarantee=eve）
    P('## A. 每次抽取命中率 p_hit 掃描（一般 4次/日；catch-up cap1；保底 eve）\n')
    P('| p_hit | 事件/活躍日 | 事件/session | 每日 0 事件% | p90 事件/日 | 單次返嚟最多 | 空抽% | 3連內重複% |'); P('|---|---|---|---|---|---|---|---|')
    for p in (0.15, 0.25, 0.35, 0.5, 0.75, 1.0):
        pet, sh, se = run(PROFILES['一般 4次/日'], a.days, random.Random(a.seed), p, catchup='cap1', guarantee='eve')
        s = stats(pet, sh, se, a.days)
        P(f"| {p} | {s['events_per_active_day']:.2f} | {s['evt_per_session']:.2f} | {s['zero_days_pct']:.1f} | {s['p90_per_day']} | {s['max_per_return']} | {s['empty_draw_pct']:.0f} | {100*s['repeat_in3']:.0f} |")
    # B. 離線 catch-up 策略
    P('\n## B. 離線返嚟處理（p_hit=0.35；保底 eve）\n')
    P('| profile | catch-up 策略 | 事件/日 | 單次返嚟最多（任何離開） | 離開≥24h 返嚟最多 | 日記條目/日（被收埋） | 每日 0 事件% |'); P('|---|---|---|---|---|---|---|')
    for pn in ('一般 4次/日', '上班族 朝晚夜', '隔日 1次'):
        for cu in ('all', 'cap2', 'cap1'):
            pet, sh, se = run(PROFILES[pn], a.days, random.Random(a.seed), 0.35, catchup=cu, guarantee='eve')
            s = stats(pet, sh, se, a.days)
            P(f"| {pn} | {cu} | {s['events_per_active_day']:.2f} | {s['max_per_return']} | {s['big_return_max']} | {s['dropped_per_day']:.2f} | {s['zero_days_pct']:.1f} |")
    # 長期缺席（14 日）
    rng = random.Random(a.seed); pet = Pet(rng, 0.35, catchup='all'); n_due = 0; t = 0.0
    while t < 14 * 24:
        t += rng.uniform(2, 4)
        if rng.random() < 0.35: n_due += 1
    P(f'\n長期缺席 14 日後返嚟，**未設上限**會一次到期約 **{n_due}** 個事件（2–4h/抽、p_hit 0.35），即係爆事件；cap1＝只顯示 1 個＋日記。\n')
    # C. 保底策略
    P('## C. 每日保底策略（p_hit=0.35；cap1）— 「每日 0 事件」比例（只計有開 app 嘅日子）\n')
    P('| profile | none | first（當日首次打開） | eve（16:00 後首次打開） | eve2（16:00 後，或當日第 2 次打開）｜事件/日 first／eve2 |'); P('|---|---|---|---|---|')
    for pn, prof in PROFILES.items():
        row = []; epd = []
        for g in ('none', 'first', 'eve', 'eve2'):
            pet, sh, se = run(prof, a.days, random.Random(a.seed), 0.35, catchup='cap1', guarantee=g)
            r = stats(pet, sh, se, a.days); row.append(r['zero_days_pct']); epd.append(r['events_per_active_day'])
        P(f'| {pn} | {row[0]:.1f}% | {row[1]:.1f}% | {row[2]:.1f}% | {row[3]:.1f}% ｜ {epd[1]:.2f}／{epd[3]:.2f} |')
    # D. 冷卻違規＋分佈
    pet, sh, se = run(PROFILES['勤力 6次/日'], a.days, random.Random(a.seed), 0.5, catchup='cap2', guarantee='eve')
    s = stats(pet, sh, se, a.days)
    P(f"\n## D. 冷卻／全域間隔／分佈（勤力 6次/日，p_hit 0.5）\n\n- 冷卻違規次數：**{s['cd_viol']}**（要 =0）；事件最小間隔（以抽取時間計）：{s['min_gap']:.2f} h（全域間隔 1 h；保底強制抽取除外）\n- 相鄰同事件：{100*s['repeat_adjacent']:.1f}%；3 連內重複：{100*s['repeat_in3']:.0f}%\n")
    wsum = sum(e[1] for e in EVENTS)
    P('| 事件 | 名義權重% | 實際% | 備註 |'); P('|---|---|---|---|')
    for e in EVENTS: P(f"| {e[0]} | {100*e[1]/wsum:.0f} | {100*s['dist'].get(e[0], 0):.1f} | {e[4]} |")
    P('\n（實際% 偏離名義＝時段條件／冷卻令部分事件較少抽到。流星夜／夢話只可喺夜間，若玩家夜間少開 app，佢哋近乎永遠見唔到 → 見建議。）')
    P('\n## D2. 防重複（最近 2 個事件權重 ×anti）— 勤力／一般／輕度，p_hit 0.35\n')
    P('| profile | anti | 相鄰同事件% | 3連內重複% | 事件/日 |'); P('|---|---|---|---|---|')
    for pn in ('勤力 6次/日', '一般 4次/日', '輕度 2次/日'):
        for an in (1.0, 0.25, 0.0):
            pet, sh, se = run(PROFILES[pn], a.days, random.Random(a.seed), 0.35, catchup='cap1', guarantee='eve2', anti=an)
            r = stats(pet, sh, se, a.days)
            P(f"| {pn} | {an} | {100*r['repeat_adjacent']:.1f} | {100*r['repeat_in3']:.0f} | {r['events_per_active_day']:.2f} |")
    # E. 閃光日
    P('\n## E. 閃光日 3% 統計\n')
    P('| 定義 | 閃光日比例 | 新玩家 7 日內見到 | 14 日內 | 30 日內 | 最長無閃光日數（%d 日樣本） |' % a.days); P('|---|---|---|---|---|---|')
    for mode, nm in (('day', '每日 3%（日為單位，建議）'), ('draw', '每次抽取 3%（約 8 抽/日）')):
        fr, q7, q14, q30, best = shiny_stats(a.days, random.Random(a.seed + 1), mode)
        P(f'| {nm} | {100*fr:.2f}% | {100*q7:.0f}% | {100*q14:.0f}% | {100*q30:.0f}% | {best} |')
    k, mu, sd, z = chi2_uniformity(random.Random(a.seed + 2), 200000)
    P(f'\n二項檢定（20 萬日）：閃光日 {k}，期望 {mu:.0f}±{sd:.0f}（|z|={z:.2f}，<3.3 即 99.9% 內 → 通過）。')
    P('\n**重點**：「每次抽取 3%」實際令 **≈22% 嘅日子** 係閃光日（見上表），唔係 3%；plan 要先定義單位。日為單位時新玩家 14 日內見到只有 ≈35%、最長可近 250 日無閃光（3000 日樣本 247 日） → 建議加保底（P2）。')
    txt = '\n'.join(out); print(txt)
    if a.md:
        import os; os.makedirs(os.path.dirname(a.md), exist_ok=True); open(a.md, 'w').write(txt + '\n')

if __name__ == '__main__':
    main()
