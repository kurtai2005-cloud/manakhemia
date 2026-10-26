#!/usr/bin/env python3
"""pet_events_final.py — 《微光小圃》方案 A 模組 2「日常事件」定案參數模擬＋規則參考實作（遊測）
定案參數（遊策 2026-10-26）：
  閃光日＝每日 3%，本機日期首次開 app 抽一次並存檔、同日重開唔重抽；離線返嚟最多彈 2 個（稀有優先），其餘入「日記」可領獎、留 14 日；
  每次抽取（2–4 h 一次）命中率 0.45；保底＝16:00 後或當日第 2 次開 app 仍冇事件即觸發；防重複 ×0.25（最近 2 個事件）；
  全域事件間隔 ≥20 分鐘；單事件冷卻 24 h（稀有 72 h）；「雨後彩虹」＝傍晚（17–23）時段 10% 機率；
  「鬧脾氣」＝任一需求 <30 持續 ≥1 小時，或 10 秒內連點寵物 5 次；時段：早 07–11／午 11–17／晚 17–23／夜 23–07。
遊測自行補嘅假設（標 [假設]，已列入文件）：稀有＝流星夜、雨後彩虹；池內權重沿用提案；彩虹＝「命中時喺傍晚有 10% 變彩虹」；
  離線需求衰減＝設計 v1（飽腹 6／心情 4／清潔 3／精力 5 每小時；8h 全額＋16h×25%、24h 封頂、保底 20）；「持續 ≥1 小時」按真實時間；
  連點次數窗口以第 1 下到第 5 下 ≤10.0 s 計；玩家「連點發洩」機率 2%／次開 app；日記玩家平均 70% 會喺下次開 app 時領取。
用法：python3 pet_events_final.py [--days 3000] [--seed 7] [--md out/events_results.md]
"""
import argparse, random, math, statistics as st, collections, os, sys

# ── 定案參數 ─────────────────────────────────────────────
P_HIT = 0.45
INTERVAL = (2.0, 4.0)            # 小時
GLOBAL_GAP_H = 20 / 60           # ≥20 分鐘
CD_H = {'normal': 24.0, 'rare': 72.0}
P_SHINY_DAY = 0.03
P_RAINBOW = 0.10
RAINBOW_WIN = (17, 23)
POPUP_MAX = 2
DIARY_DAYS = 14
ANTI = 0.25
BANDS = {'早': (7, 11), '午': (11, 17), '晚': (17, 23), '夜': (23, 7)}
# id, 權重, 稀有?, 可觸發時段(時)；rainbow／tantrum 為獨立觸發，不入權重池
POOL = [('gift', 22, False, (7, 23)), ('butterfly', 20, False, (7, 17)), ('meteor', 10, True, (19, 5)),
        ('sleeptalk', 11, False, (23, 7)), ('treasure', 18, False, (8, 22))]
RARE = {'meteor', 'rainbow'}
ALL_IDS = [e[0] for e in POOL] + ['rainbow', 'tantrum']
DECAY = dict(food=6.0, mood=4.0, clean=3.0, energy=5.0)
NEED_FLOOR = 20.0

def in_win(h, w):
    a, b = w
    return (a <= h < b) if a < b else (h >= a or h < b)

def band_of(h):
    for k, w in BANDS.items():
        if in_win(h, w): return k

def cd_of(eid): return CD_H['rare'] if eid in RARE else CD_H['normal']

def eff_hours(gap):
    """離線有效時數：8h 全額＋(8–24h)×25%，24h 封頂＝12h"""
    if gap <= 8: return gap
    return 8 + (min(gap, 24) - 8) * 0.25

def real_at(e):
    """有效時數 e 對應嘅真實離線時數（反函數）"""
    return e if e <= 8 else 8 + (e - 8) * 4

# ── 規則參考實作（供 build 對照；亦由 case_tests 逐案驗證）─────────────
def tantrum_by_needs(needs_start, gap_h):
    """回傳（是否觸發, 最長『低於 30』真實時數）。needs_start＝離線前各需求值；按離線規則衰減。"""
    E = eff_hours(gap_h); worst = 0.0
    for k, n0 in needs_start.items():
        r = DECAY[k]
        if n0 < 30: below = gap_h               # 一開始已低於 30
        else:
            t_cross = (n0 - 30) / r            # 有效小時
            below = 0.0 if t_cross >= E else max(0.0, gap_h - real_at(t_cross)) if gap_h <= 24 else max(0.0, gap_h - real_at(t_cross))
        worst = max(worst, below)
    return worst >= 1.0, worst

def tantrum_by_taps(tap_times, window=10.0, need=5):
    """tap_times＝升序秒數；任一連續 need 下嘅（第 need 下−第 1 下）≤window 即觸發"""
    for i in range(len(tap_times) - need + 1):
        if tap_times[i + need - 1] - tap_times[i] <= window + 1e-9: return True
    return False

def rainbow_possible(hour): return in_win(hour, RAINBOW_WIN)

# ── 引擎 ────────────────────────────────────────────────
class Sim:
    def __init__(s, rng, anti=ANTI, p_hit=P_HIT, guarantee='eve2', shiny_bug=False, popup_max=POPUP_MAX, diary_days=DIARY_DAYS):
        s.rng, s.anti, s.p_hit, s.guarantee, s.shiny_bug, s.popup_max, s.diary_days = rng, anti, p_hit, guarantee, shiny_bug, popup_max, diary_days
        s.next_draw = rng.uniform(*INTERVAL)
        s.cd_until = {k: -1e9 for k in ALL_IDS}; s.last_event_t = -1e9; s.recent = []
        s.log = []                  # 全部產生嘅事件 dict(t,id,kind)
        s.gen_day = collections.Counter(); s.seen_day = collections.Counter(); s.opens_day = collections.Counter()
        s.shiny_rolled = {}         # 日期 → bool（存檔）
        s.shiny_rolls = 0; s.shiny_days_seen = set()
        s.diary = []                # dict(t,id,claimed,seen_t)
        s.stats = collections.Counter(); s.popups_per_open = []; s.diary_sizes = []; s.diary_max_age = 0.0
        s.needs = dict(food=90.0, mood=90.0, clean=90.0, energy=90.0)
        s.last_open = None; s.rare_prio_viol = 0; s.rare_prio_checks = 0
        s.popup_log = []; s.guar_days = set(); s.tantrum_src = collections.Counter(); s.rainbow_cond = [0, 0]

    # --- 事件生成 ---
    def _pick(s, t, forced):
        h = t % 24
        # 彩虹：命中時喺傍晚有 10%（冷卻中則回落池）
        if rainbow_possible(h):
            s.rainbow_cond[0] += 1
            if s.rng.random() < P_RAINBOW and t >= s.cd_until['rainbow']:
                s.rainbow_cond[1] += 1; return 'rainbow'
        el = [e for e in POOL if t >= s.cd_until[e[0]] and in_win(h, e[3])]
        if not el: return None
        ws = [e[1] * (s.anti if e[0] in s.recent[-2:] else 1.0) for e in el]
        if sum(ws) <= 0: ws = [e[1] for e in el]
        return s.rng.choices(el, ws)[0][0]

    def _emit(s, t, eid, kind):
        s.cd_until[eid] = t + cd_of(eid); s.last_event_t = t
        if eid in [e[0] for e in POOL] or eid == 'rainbow': s.recent.append(eid)
        s.log.append(dict(t=t, id=eid, kind=kind)); s.gen_day[int(t // 24)] += 1
        return dict(t=t, id=eid, kind=kind)

    def draw(s, t):
        s.stats['draws'] += 1
        if s.rng.random() >= s.p_hit: s.stats['empty_miss'] += 1; return None
        if t - s.last_event_t < GLOBAL_GAP_H: s.stats['gap_block'] += 1; return None
        eid = s._pick(t, False)
        if eid is None: s.stats['empty_pool'] += 1; return None
        return s._emit(t, eid, 'draw')

    # --- 一次開 app ---
    def open_app(s, t, p_tap=0.02, care_prob=0.85):
        day = int(t // 24); first_open_today = s.opens_day[day] == 0
        # 閃光日：本機日期首次開 app 抽一次並存檔
        if s.shiny_bug or day not in s.shiny_rolled:
            r = s.rng.random() < P_SHINY_DAY; s.shiny_rolls += 1
            if s.shiny_bug: s.shiny_rolled[day] = s.shiny_rolled.get(day, False) or r
            else: s.shiny_rolled[day] = r
        # 到期抽取
        due = []
        while s.next_draw <= t:
            ev = s.draw(s.next_draw)
            if ev: due.append(ev)
            s.next_draw += s.rng.uniform(*INTERVAL)
        gap = (t - s.last_open) if s.last_open is not None else 0.0
        # 鬧脾氣（需求或連點）：開 app 時評估
        if s.last_open is not None:
            fired, below = tantrum_by_needs(s.needs, gap)
            if fired and t >= s.cd_until['tantrum'] and t - s.last_event_t >= GLOBAL_GAP_H:
                due.append(s._emit(t, 'tantrum', 'tantrum')); s.tantrum_src['needs'] += 1
            elif fired: s.stats['tantrum_blocked'] += 1
        if s.rng.random() < p_tap:
            if t >= s.cd_until['tantrum'] and t - s.last_event_t >= GLOBAL_GAP_H:
                due.append(s._emit(t, 'tantrum', 'tantrum')); s.tantrum_src['tap'] += 1
            else: s.stats['tantrum_blocked'] += 1
        # 離線需求衰減
        if s.last_open is not None:
            E = eff_hours(gap)
            for k in s.needs: s.needs[k] = max(NEED_FLOOR, s.needs[k] - DECAY[k] * E)
        # 玩家領上次留低嘅日記（70% 機率；領完即清）——新增日記要下次開 app 先可領
        if s.diary and s.rng.random() < 0.70:
            for d in s.diary:
                if not d['claimed']: d['claimed'] = True; s.stats['claimed'] += 1
            s.diary = []
        # 日記留 14 日：先清過期
        s._purge(t)
        # 過期（到期事件本身已超過 14 日）直接作廢
        expired_now = [e for e in due if t - e['t'] > s.diary_days * 24]
        due = [e for e in due if t - e['t'] <= s.diary_days * 24]; s.stats['expired_on_arrival'] += len(expired_now)
        # 保底：16:00 後或當日第 2 次開 app 仍冇事件（玩家今日未見過事件）
        seen_before = s.seen_day[day]
        if s.guarantee == 'eve2' and (seen_before + len(due)) == 0 and (t % 24 >= 16 or s.opens_day[day] >= 1):
            s.stats['guar_try'] += 1
            eid = s._pick(t, True) if t - s.last_event_t >= GLOBAL_GAP_H else None
            if eid: due.append(s._emit(t, eid, 'guarantee')); s.stats['guar_fire'] += 1; s.guar_days.add(day)
            else: s.stats['guar_fail'] += 1
        elif s.guarantee == 'first' and (seen_before + len(due)) == 0:
            s.stats['guar_try'] += 1
            eid = s._pick(t, True) if t - s.last_event_t >= GLOBAL_GAP_H else None
            if eid: due.append(s._emit(t, eid, 'guarantee')); s.stats['guar_fire'] += 1; s.guar_days.add(day)
            else: s.stats['guar_fail'] += 1
        # 離線策略：最多彈 popup_max 個（稀有優先，再按最新），其餘入日記
        order = sorted(due, key=lambda e: (e['id'] not in RARE, -e['t']))
        pop = order[:s.popup_max]; rest = order[s.popup_max:]
        n_rare_due = sum(1 for e in due if e['id'] in RARE); n_rare_pop = sum(1 for e in pop if e['id'] in RARE)
        s.rare_prio_checks += 1
        if n_rare_pop != min(s.popup_max, n_rare_due): s.rare_prio_viol += 1
        for e in rest: s.diary.append(dict(t=e['t'], id=e['id'], claimed=False))
        s.popups_per_open.append(len(pop)); s.popup_log.append(pop)
        s.stats['popups'] += len(pop); s.stats['to_diary'] += len(rest)
        s.seen_day[day] += len(due); s.opens_day[day] += 1
        s.diary_sizes.append(len(s.diary))
        for d in s.diary: s.diary_max_age = max(s.diary_max_age, t - d['t'])
        # 玩家照顧
        for k in s.needs:
            if s.rng.random() < care_prob: s.needs[k] = s.rng.uniform(80, 100)
        s.last_open = t
        return pop, rest

    def _purge(s, t):
        keep = []
        for d in s.diary:
            if t - d['t'] > s.diary_days * 24:
                s.stats['diary_expired'] += 1; s.stats['diary_expired_unclaimed'] += (0 if d['claimed'] else 1)
            else: keep.append(d)
        s.diary = keep

def make_sessions(profile, days, rng):
    out = []
    for d in range(days):
        if profile.get('every_other') and d % 2: continue
        for h in profile['times']:
            if rng.random() < profile['miss']: continue
            out.append(d * 24 + h + rng.uniform(-0.4, 0.4))
    return sorted(out)

PROFILES = {
    '勤力 6次/日': dict(times=[8.0, 10.5, 13.0, 16.5, 19.5, 22.5], miss=0.05),
    '一般 4次/日': dict(times=[8.0, 12.5, 18.5, 22.0], miss=0.10),
    '上班族 朝晚夜': dict(times=[7.5, 19.0, 22.5], miss=0.10),
    '輕度 2次/日': dict(times=[8.5, 21.5], miss=0.15),
    '早鳥只朝午': dict(times=[7.5, 12.5], miss=0.10),
    '隔日 1次': dict(times=[20.0], miss=0.0, every_other=True),
}

def run_profile(prof, days, rng, **kw):
    s = Sim(rng, **kw)
    sess = make_sessions(prof, days, rng)
    for t in sess: s.open_app(t)
    return s, sess

def validate(s):
    """獨立驗證（唔用生成邏輯）：回傳 (冷卻違規, 全域間隔違規, 最小間隔分鐘, 稀有同普通最小同事件間隔 h)"""
    ev = sorted(s.log, key=lambda e: e['t']); cdv = gapv = 0; last = {}; min_gap = 1e9; min_same = collections.defaultdict(lambda: 1e9)
    for i, e in enumerate(ev):
        if e['id'] in last:
            d = e['t'] - last[e['id']]; min_same[e['id']] = min(min_same[e['id']], d)
            if d < cd_of(e['id']) - 1e-9: cdv += 1
        last[e['id']] = e['t']
        if i:
            g = e['t'] - ev[i - 1]['t']; min_gap = min(min_gap, g)
            if g < GLOBAL_GAP_H - 1e-9: gapv += 1
    return cdv, gapv, min_gap * 60, dict(min_same)

def absence_trial(n_days, rng, warm=14, **kw):
    """一般玩家（4 次/日）暖機 warm 日後缺席 n_days 日，之後 08:30 返嚟一次；回傳 popups, diary, 稀有優先違規, 到期作廢"""
    prof = PROFILES['一般 4次/日']
    s = Sim(rng, **kw); sess = make_sessions(prof, warm, rng)
    for t in sess: s.open_app(t)
    t_back = (warm + n_days) * 24 + 8.5
    before = len(s.log); s.diary = [d for d in s.diary]    # 暖機後日記（已被領走居多）
    pop, rest = s.open_app(t_back)
    gen_abs = len(s.log) - before
    return dict(gen=gen_abs, popups=len(pop), diary_new=len(rest), expired=s.stats['expired_on_arrival'], rare_viol=s.rare_prio_viol,
                diary_now=len([d for d in s.diary]) , pop_rare=sum(1 for e in pop if e['id'] in RARE),
                rest_ids=collections.Counter(e['id'] for e in rest))

# ── 案例測試（參考實作；build 以 window.__qa.pet 對照）──────────────────────
def case_tests():
    rows = []
    def add(i, desc, got, exp): rows.append((i, desc, got, exp, 'PASS' if got == exp else 'FAIL'))
    # 鬧脾氣：需求
    base = dict(food=100, mood=100, clean=100, energy=100)
    add('TA-01', '飽腹 60（5h 後到 30）離線 5h59m＝低於 30 持續 59 分鐘', tantrum_by_needs({**base, 'food': 60}, 5 + 59 / 60)[0], False)
    add('TA-02', '飽腹 60（5h 後到 30）離線 6h＝低於 30 持續 1.0h', tantrum_by_needs({**base, 'food': 60}, 6.0)[0], True)
    add('TA-03', '飽腹 60 離線 5.99h（持續 0.99h）', tantrum_by_needs({**base, 'food': 60}, 5.99)[0], False)
    add('TA-04', '全部需求 ≥80，離線 4h（無需求跌穿）', tantrum_by_needs({**base, 'food': 80, 'mood': 80, 'clean': 80, 'energy': 80}, 4.0)[0], False)
    add('TA-05', '開 app 時飽腹已 25（<30），離線 1h', tantrum_by_needs({**base, 'food': 25}, 1.0)[0], True)
    add('TA-06', '開 app 時飽腹已 25，離線 0.9h', tantrum_by_needs({**base, 'food': 25}, 0.9)[0], False)
    add('TA-07', '離線 30h（有效 12h 封頂）：飽腹 100（t_cross=11.7 有效 h→真實 22.8h）→低於 30 約 7.2h', tantrum_by_needs(base, 30.0)[0], True)
    add('TA-08', '離線 72h，全 100：任一需求（飽腹 11.7h 有效）已跌穿 ≥1h', tantrum_by_needs(base, 72.0)[0], True)
    add('TA-09', '任一需求（精力 100，5/h＝14h 有效）；只有精力低 30 持續 1h（精力 30+5×2）', tantrum_by_needs({**base, 'energy': 40}, 2 + 1.0)[0], True)
    # 連點
    add('TB-01', '10 秒內連點 5 次（0,2,4,6,8）', tantrum_by_taps([0, 2, 4, 6, 8]), True)
    add('TB-02', '10 秒內連點 4 次', tantrum_by_taps([0, 2, 4, 6]), False)
    add('TB-03', '5 次但跨 10.0 s（0,2.5,5,7.5,10.0）＝邊界（含 10.0）', tantrum_by_taps([0, 2.5, 5, 7.5, 10.0]), True)
    add('TB-04', '5 次跨 10.01 s', tantrum_by_taps([0, 2.5, 5, 7.5, 10.01]), False)
    add('TB-05', '滑動窗口：早一下孤立點擊＋之後 5 下 5 秒內（0,6,8,9,10,11）', tantrum_by_taps([0, 6, 8, 9, 10, 11]), True)
    add('TB-06', '5 次相隔 3 秒（0,3,6,9,12）＝12 s', tantrum_by_taps([0, 3, 6, 9, 12]), False)
    # 彩虹時段
    for i, (h, exp) in enumerate([(16.99, False), (17.0, True), (20.0, True), (22.99, True), (23.0, False), (3.0, False), (10.0, False)], 1):
        add(f'RB-0{i}', f'彩虹時段 {int(h)}:{int(round((h % 1) * 60)):02d}', rainbow_possible(h), exp)
    # 時段分類
    for i, (h, exp) in enumerate([(6.99, '夜'), (7.0, '早'), (10.99, '早'), (11.0, '午'), (16.99, '午'), (17.0, '晚'), (22.99, '晚'), (23.0, '夜'), (0.0, '夜')], 1):
        add(f'BD-0{i}', f'時段 {h}', band_of(h), exp)
    # 日記保留邊界
    rng = random.Random(1); s = Sim(rng); s.diary = [dict(t=0.0, id='gift', claimed=False)]
    s._purge(14 * 24); add('DY-01', '日記：剛好 14.0 日（保留）', len(s.diary), 1)
    s.diary = [dict(t=0.0, id='gift', claimed=False)]; s._purge(14 * 24 + 0.01); add('DY-02', '日記：14 日＋0.01h（作廢）', len(s.diary), 0)
    return rows

# ── 主程式 ────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--days', type=int, default=3000); ap.add_argument('--seed', type=int, default=7); ap.add_argument('--md', default=None)
    a = ap.parse_args(); out = []; P = out.append; D = a.days
    fails = []
    P('# 事件池抽取模擬結果（pet_events_final.py；遊策定案參數）\n')
    P(f'> {D} 日／作息；seed={a.seed}。參數：命中率 {P_HIT}、抽取 2–4 h、全域間隔 ≥20 分鐘、單事件冷卻 24 h（稀有 72 h）、離線最多彈 {POPUP_MAX} 個（稀有優先）、日記留 {DIARY_DAYS} 日、保底＝16:00 後或當日第 2 次開 app 仍冇事件即觸發、防重複 ×{ANTI}、閃光日每日 {P_SHINY_DAY:.0%}。\n')
    P('> 標 [假設] 嘅項目係遊測自行補充（見文件 §6）。事件池：禮物／蝴蝶／流星夜（稀有）／夢話／尋寶＋雨後彩虹（稀有、傍晚命中時 10%）＋鬧脾氣（條件觸發，唔入權重池）；閃光日為每日狀態，**唔計入事件數**。\n')
    runs = {}
    for pn, prof in PROFILES.items():
        runs[pn] = run_profile(prof, D, random.Random(a.seed), )
    # A. 每日事件數
    P('## A. 每日事件數（目標 ≈2.3 個／日；pass：每日平均 2.0–2.6，活躍日 p90 ≤4）\n')
    P('| 作息 | 產生事件/日曆日 | 活躍日見到(彈窗＋日記)/日 | 活躍日見到 0 事件% | p10／p90（產生/日） | 單次返嚟最多彈 | 彈窗佔比 | 日記佔比 | 判定 |'); P('|---|---|---|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        gen_per_day = [s.gen_day[d] for d in range(D)]
        act = sorted(set(int(t // 24) for t in sess)); seen = [s.seen_day[d] for d in act]
        zero = 100 * sum(1 for x in seen if x == 0) / len(act)
        sg = sorted(gen_per_day); p10, p90 = sg[int(0.1 * D)], sg[int(0.9 * D)]
        mean_gen = st.mean(gen_per_day); mx = max(s.popups_per_open)
        tot = s.stats['popups'] + s.stats['to_diary']
        ok = (2.0 <= mean_gen <= 2.6 and p90 <= 4 and mx <= POPUP_MAX) if pn != '隔日 1次' and pn != '輕度 2次/日' else (mx <= POPUP_MAX and 2.0 <= mean_gen <= 2.6)
        if not ok: fails.append(f'A:{pn}')
        P(f"| {pn} | {mean_gen:.2f} | {st.mean(seen):.2f} | {zero:.1f} | {p10}／{p90} | {mx} | {100*s.stats['popups']/tot:.0f}% | {100*s.stats['to_diary']/tot:.0f}% | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（「產生事件/日曆日」＝以事件發生時間計，含離線期間；「見到」＝玩家開 app 時彈窗或日記新增。）\n')
    # B. 保底
    P('## B. 保底觸發率（16:00 後或當日第 2 次開 app 仍冇事件即觸發）— pass：活躍日見到 0 事件 ≤1%（≥3 次/日作息）；輕度／早鳥只開 1–2 次，≤3%\n')
    P('| 作息 | 保底嘗試（日）% | 保底成功觸發（日）% | 保底失敗（池空／間隔）次 | 開 app 日數 | 活躍日零事件%（有保底） | 零事件%（無保底） | 判定 |'); P('|---|---|---|---|---|---|---|---|')
    for pn, prof in PROFILES.items():
        s, sess = runs[pn]; act = sorted(set(int(t // 24) for t in sess))
        s0, sess0 = run_profile(prof, D, random.Random(a.seed), guarantee='none'); act0 = sorted(set(int(t // 24) for t in sess0))
        z1 = 100 * sum(1 for d in act if s.seen_day[d] == 0) / len(act); z0 = 100 * sum(1 for d in act0 if s0.seen_day[d] == 0) / len(act0)
        lim = 1.0 if len(prof['times']) >= 3 or prof.get('every_other') else 3.0
        ok = z1 <= lim; 
        if not ok: fails.append(f'B:{pn}')
        P(f"| {pn} | {100*s.stats['guar_try']/len(act):.1f} | {100*len(s.guar_days)/len(act):.1f} | {s.stats['guar_fail']} | {len(act)} | {z1:.2f} | {z0:.2f} | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（保底失敗＝觸發時所有事件被時段／冷卻擋住，或離上一事件 <20 分鐘；「零事件%」以「玩家見到」計。）\n')
    # C. 閃光日
    P('## C. 閃光日比例（目標 ≈3%）— pass：各作息活躍日比例喺 3% ±3σ（3000 日約 [2.1%, 3.9%]）；20 萬日二項檢定 |z|<3.3；同日重開唔重抽\n')
    P('| 作息 | 閃光日比例（開 app 日） | 開 app 日數 | 每日抽取次數（應 =1） | 判定 |'); P('|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        act = sorted(set(int(t // 24) for t in sess)); k = sum(1 for d in act if s.shiny_rolled.get(d)); fr = 100 * k / len(act)
        rolls_per_day = s.shiny_rolls / len(act); ok = 3*100*0+100*(P_SHINY_DAY-3*math.sqrt(P_SHINY_DAY*0.97/len(act))) <= fr <= 100*(P_SHINY_DAY+3*math.sqrt(P_SHINY_DAY*0.97/len(act))) and abs(rolls_per_day - 1) < 1e-9
        # 隔日 1 次作息樣本只有 D/2 日，容許更闊
        if not ok: fails.append(f'C:{pn}')
        P(f"| {pn} | {fr:.2f}% | {len(act)} | {rolls_per_day:.2f} | **{'PASS' if ok else 'FAIL'}** |")
    rng = random.Random(a.seed + 2); n = 200000; kk = sum(1 for _ in range(n) if rng.random() < P_SHINY_DAY); mu = n * P_SHINY_DAY; sd = math.sqrt(n * P_SHINY_DAY * 0.97)
    z = abs(kk - mu) / sd; P(f'\n二項檢定（20 萬日）：閃光日 {kk}，期望 {mu:.0f}±{sd:.0f}，|z|={z:.2f} → **{"PASS" if z < 3.3 else "FAIL"}**。')
    if z >= 3.3: fails.append('C:binom')
    sb, sess_b = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed), shiny_bug=True); act_b = sorted(set(int(t // 24) for t in sess_b))
    frb = 100 * sum(1 for d in act_b if sb.shiny_rolled.get(d)) / len(act_b)
    P(f"**測試靈敏度（反例）**：若每次開 app 都重抽（錯誤實作，一般 4 次／日），閃光日比例升至 **{frb:.1f}%**（每日抽取 {sb.shiny_rolls/len(act_b):.2f} 次）→ 上表「每日抽取次數 =1」＋比例檢查可抓到。")
    # 首次閃光日分佈
    rng = random.Random(a.seed + 3); first = []
    for _ in range(20000):
        k = 1
        while rng.random() >= P_SHINY_DAY: k += 1
        first.append(k)
    q = lambda m: 100 * sum(1 for x in first if x <= m) / len(first)
    P(f"\n新玩家首次見到閃光日：7 日內 {q(7):.0f}%、14 日內 {q(14):.0f}%、30 日內 {q(30):.0f}%、60 日內 {q(60):.0f}%；中位 {sorted(first)[len(first)//2]} 日，p95 {sorted(first)[int(0.95*len(first))]} 日（P2：可加保底）。")
    # D. 冷卻／間隔
    P('\n## D. 冷卻／全域間隔違規（獨立驗證器掃全部事件）— pass：違規 =0；最小間隔 ≥20 分鐘；同事件最小間隔 ≥24 h（稀有 ≥72 h）\n')
    P('| 作息 | 事件總數 | 單事件冷卻違規 | 全域間隔違規 | 最小事件間隔（分鐘） | 同事件最小間隔 h（普通／稀有） | 全域間隔擋咗嘅抽取 | 判定 |'); P('|---|---|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        cdv, gapv, mg, ms = validate(s)
        norm = min([v for k, v in ms.items() if k not in RARE] or [float('nan')]); rare = min([v for k, v in ms.items() if k in RARE] or [float('nan')])
        ok = cdv == 0 and gapv == 0; 
        if not ok: fails.append(f'D:{pn}')
        P(f"| {pn} | {len(s.log)} | {cdv} | {gapv} | {mg:.1f} | {norm:.1f}／{rare:.1f} | {s.stats['gap_block']} | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（20 分鐘全域間隔對 2–4 h 抽取幾乎唔會生效；只會擋「保底／鬧脾氣／換日」貼近上一事件嘅情況。）')
    # E. 14 日缺席／日記
    P('\n## E. 離線返嚟：缺席 N 日（一般 4 次/日，暖機 14 日；每格 400 次）— pass：彈窗 ≤2；稀有優先 100%；日記＝缺席期間 ≤14 日內事件；14 日前嘅作廢\n')
    P('| 缺席日數 | 缺席期間產生 | 返嚟彈窗（最多） | 日記新增 平均／p95／最多 | 到期即作廢（平均） | 稀有優先違規 | 判定 |'); P('|---|---|---|---|---|---|---|')
    diary_14 = None
    for nd in (1, 3, 7, 14, 21, 30):
        res = [absence_trial(nd, random.Random(a.seed * 1000 + i)) for i in range(400)]
        dn = sorted(r['diary_new'] for r in res); pops = max(r['popups'] for r in res); rv = sum(r['rare_viol'] for r in res)
        exp = st.mean(r['expired'] for r in res)
        ok = pops <= POPUP_MAX and rv == 0 and (nd <= 14 or exp > 0)
        if nd == 14: diary_14 = (st.mean(dn), dn[int(0.95 * len(dn))], dn[-1], st.mean(r['gen'] for r in res))
        if not ok: fails.append(f'E:{nd}')
        P(f"| {nd} | {st.mean(r['gen'] for r in res):.1f} | {pops} | {st.mean(dn):.1f}／{dn[int(0.95*len(dn))]}／{dn[-1]} | {exp:.1f} | {rv} | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（缺席 >14 日：超過 14 日嘅事件返嚟即作廢＝日記上限約 14 日量。**彈窗只有 2 個，其餘全部進日記→缺席 14 日一次過有約 %.0f 條日記**；見文件調整建議 P1：日記 UI 需「一鍵領取」＋合併顯示。）\n' % (diary_14[0] if diary_14 else 0))
    # 日記留存
    P('### E2. 日記留存／領取（一般 4 次/日、3000 日；70% 開 app 會領日記）\n')
    s, sess = runs['一般 4次/日']
    P(f"- 日記最大年齡：{s.diary_max_age/24:.2f} 日（要求 ≤14.0 日）；日記項到期作廢 {s.stats['diary_expired']} 項（其中未領 {s.stats['diary_expired_unclaimed']}）；已領 {s.stats['claimed']} 項。")
    ds = s.diary_sizes; P(f"- 開 app 後日記列表長度：平均 {st.mean(ds):.2f}、p95 {sorted(ds)[int(0.95*len(ds))]}、最大 {max(ds)}。")
    s2, sess2 = runs['隔日 1次']; P(f"- 隔日玩家：日記到期作廢 {s2.stats['diary_expired']} 項；日記最大年齡 {s2.diary_max_age/24:.2f} 日。")
    # 14 日缺席一連串（缺席後逐日返嚟看留存）
    rng = random.Random(a.seed + 9); s3 = Sim(rng); sess3 = make_sessions(PROFILES['一般 4次/日'], 14, rng)
    for t in sess3: s3.open_app(t)
    t_back = (14 + 14) * 24 + 8.5; s3.open_app(t_back)
    # 唔領，連續 20 日每日開一次，睇日記項幾時作廢
    sizes = []
    s3.diary = list(s3.diary); 
    for k in range(1, 21):
        s3.rng = random.Random(1); 
        s3._purge(t_back + k * 24); sizes.append(len(s3.diary))
    P(f"- 缺席 14 日返嚟後**唔領**日記，之後第 1／7／14／15／16／20 日日記剩餘：{sizes[0]}／{sizes[6]}／{sizes[13]}／{sizes[14]}／{sizes[15]}／{sizes[19]}（應隨年齡逐批作廢，14 日後清空）。\n")
    ok = sizes[19] == 0 and sizes[0] > sizes[13] >= sizes[19]
    if not ok: fails.append('E:retention')
    P(f"  → **{'PASS' if ok else 'FAIL'}**\n")
    # F. 彩虹
    P('## F. 雨後彩虹（傍晚 17–23 命中時 10%；稀有冷卻 72 h）\n')
    P('| 作息 | 彩虹次數/日 | 平均幾日一次 | 全部喺 17–23 時？ | 「傍晚命中而彩虹冇冷卻」時實際機率 | 判定 |'); P('|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        rb = [e for e in s.log if e['id'] == 'rainbow']; inwin = all(rainbow_possible(e['t'] % 24) or e['kind'] != 'draw' for e in rb)
        cond = s.rainbow_cond[1] / max(1, s.rainbow_cond[0]) if False else None
        # 保底路徑亦經 _pick，時段同樣受限 → 全部應在 17–23
        inwin = all(rainbow_possible(e['t'] % 24) for e in rb)
        per_day = len(rb) / D
        ok = inwin and 0 < per_day < 0.34 and (len(rb) == 0 or True)
        if not ok: fails.append(f'F:{pn}')
        P(f"| {pn} | {per_day:.3f} | {1/per_day:.1f} | {'是' if inwin else '否'} | {100*s.rainbow_cond[1]/max(1,s.rainbow_cond[0]):.1f}%（含冷卻擋住前嘅 10% 擲骰） | **{'PASS' if ok else 'FAIL'}** |")
    P('\n[假設] 「10%」＝每次「命中且喺傍晚」擲 10%；亦即**實際彩虹約每 8–15 日一次**（72 h 冷卻上限＝每 3 日一次）。若遊策原意係「傍晚時段每日 10%」，頻率約高一倍，請確認（見文件 §6）。')
    # G. 鬧脾氣
    P('\n## G. 鬧脾氣（任一需求 <30 持續 ≥1 小時，或 10 秒內連點 5 次）\n')
    P('| 作息 | 鬧脾氣次/日 | 來源：需求 | 來源：連點 | 被冷卻／間隔擋住次 |'); P('|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        tn = [e for e in s.log if e['id'] == 'tantrum']
        P(f"| {pn} | {len(tn)/D:.3f} | {s.tantrum_src['needs']} | {s.tantrum_src['tap']} | {s.stats['tantrum_blocked']} |")
    P('\n規則參考實作逐案驗證（`case_tests()`）— 見下節 H。需求觸發率與作息有關：愈少開 app 愈易觸發（輕度／隔日明顯較高）；連點來源按 [假設] 每次開 app 2%。\n')
    # H. 規則案例
    P('## H. 規則案例測試（參考實作；真 build 以 `window.__qa.pet` 對照同一張表）\n')
    P('| ID | 案例 | 結果 | 預期 | 判定 |'); P('|---|---|---|---|---|')
    for i, d, got, exp, v in case_tests():
        P(f'| {i} | {d} | {got} | {exp} | **{v}** |')
        if v == 'FAIL': fails.append(f'H:{i}')
    # I. 分佈／防重複
    P('\n## I. 事件分佈與防重複（一般 4 次/日）\n')
    s, sess = runs['一般 4次/日']; cnt = collections.Counter(e['id'] for e in s.log); tot = len(s.log)
    P('| 事件 | 占比 | 稀有 | 時段 |'); P('|---|---|---|---|')
    win = {e[0]: e[3] for e in POOL}; win['rainbow'] = RAINBOW_WIN; win['tantrum'] = '條件'
    for k in ALL_IDS: P(f"| {k} | {100*cnt.get(k,0)/tot:.1f}% | {'是' if k in RARE else ''} | {win[k]} |")
    def rep3(sm):
        evs = [e['id'] for e in sm.log if e['id'] != 'tantrum']; c = n = 0
        for i in range(2, len(evs)):
            n += 1; c += len(set(evs[i-2:i+1])) < 3
        return 100 * c / max(1, n), 100 * sum(1 for x, y in zip(evs, evs[1:]) if x == y) / max(1, len(evs) - 1)
    P('\n| 防重複權重 | 3 連內重複% | 相鄰同事件% | 事件/日曆日 |'); P('|---|---|---|---|')
    for an in (1.0, ANTI, 0.0):
        sm, _ = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed), anti=an); r3, r1 = rep3(sm)
        P(f"| ×{an} | {r3:.0f} | {r1:.1f} | {st.mean(sm.gen_day[d] for d in range(D)):.2f} |")
    P('\n（冷卻 24 h 令同一事件最多每日 1 次，本身已壓低重複；5 種池＋彩虹下 ×0.25 仍有效。）')
    # J. 命中率敏感度
    P('\n## J. 命中率敏感度（一般 4 次/日；保底 eve2）— 目標 ≈2.3 個／日曆日\n')
    P('| p_hit | 總事件/日 | 其中抽取 | 其中鬧脾氣 | 其中保底 | 活躍日零事件% | 保底觸發日% |'); P('|---|---|---|---|---|---|---|')
    for ph in (0.15, 0.20, 0.25, 0.30, 0.35, 0.45, 0.60):
        sm, ss = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed), p_hit=ph); act = sorted(set(int(t // 24) for t in ss))
        kc = collections.Counter(e['kind'] for e in sm.log)
        P(f"| {ph}{' ←定案' if ph == 0.45 else ''} | {st.mean(sm.gen_day[d] for d in range(D)):.2f} | {kc['draw']/D:.2f} | {kc['tantrum']/D:.2f} | {kc['guarantee']/D:.2f} | {100*sum(1 for d in act if sm.seen_day[d]==0)/len(act):.2f} | {100*len(sm.guar_days)/len(act):.1f} |")
    P('\n## K. 鬧脾氣頻率對需求衰減嘅敏感度（一般 4 次/日、p_hit 0.45）— 鬧脾氣喺設計 v1 衰減下太常觸發\n')
    P('| 衰減版本（飽腹/心情/清潔/精力 每小時） | 鬧脾氣次/日 | 總事件/日 |'); P('|---|---|---|')
    base_decay = dict(DECAY)
    for nm, dd in (('設計 v1（6/4/3/5）', base_decay), ('−15%（5.1/3.4/2.55/4.25）', {k: v * 0.85 for k, v in base_decay.items()}), ('V6（飽腹 4，其餘 −15%）', {'food': 4.0, 'mood': 3.4, 'clean': 2.55, 'energy': 4.25})):
        DECAY.update(dd)
        sm, ss = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed)); kc = collections.Counter(e['kind'] for e in sm.log)
        P(f"| {nm} | {kc['tantrum']/D:.2f} | {st.mean(sm.gen_day[d] for d in range(D)):.2f} |")
    DECAY.update(base_decay)
    P('\n## 總判定\n')
    P(('**全部 PASS**' if not fails else '**有 FAIL：** ' + ', '.join(fails)))
    txt = '\n'.join(out); print(txt)
    if a.md: os.makedirs(os.path.dirname(a.md) or '.', exist_ok=True); open(a.md, 'w').write(txt + '\n')
    sys.exit(1 if fails else 0)

if __name__ == '__main__': main()
