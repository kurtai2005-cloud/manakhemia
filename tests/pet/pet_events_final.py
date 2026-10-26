#!/usr/bin/env python3
"""pet_events_final.py — 《微光小圃》方案 A 模組 2「日常事件」最終定案參數（v5.1）模擬＋規則參考實作（遊測）
v5.1 定案（遊策 2026-10-26；延續 v5）：總事件驗收 ≤2.95（p_hit 維持 0.34，保底 0.25–0.28 接受）；防改時鐘回撥容差 120 秒（≤120 唔判，>120 判篡改）；
  lastSaveTime 若 > now+24h＝無效→重設為 now、該次唔派獎；前撥／單改時區＝已知風險（M1 唔處理）。
v5 定案：
  彩虹權重 4；命中率 p_hit＝0.34（2–4 h 抽取一次）；保底＝「當日首次開 app 如未有事件即觸發」＋原保底（16:00 後或第 2 次開 app 仍冇事件）；
  池抽取事件 2.2–2.4／日；總事件（抽取＋鬧脾氣＋保底）驗收 ≤2.95；彩虹目標 11–15 日；輕度玩家活躍日零事件 ≤3%（≥3 次/日 ≤1%）；
  日記入面螢火散步一律 +3 光粒、冇心情獎勵（心情 +10 只喺彈窗領取）；
  P2 防作弊：存檔記 lastSaveTime（UTC epoch），系統時間早於它（超出容差）＝視為改時鐘，當日唔抽閃光日同事件（唔更新 lastSaveTime）。
延續 v4：池 7 個池抽取事件（禮物、蝴蝶、流星夜、彩虹、夢話、尋寶、螢火散步 17–23 權重 20＋光粒 5／心情 10）＋鬧脾氣＋閃光日＝9；閃光日按日期存「已領」；
  鬧脾氣＝需求 <30 持續 ≥2 h 或 10 秒連點 5 下、冷卻 48 h、睡眠中連點＝輕喚醒；離線最多彈 2（稀有優先）；日記 14 日、第 12 日起提示、+3 光粒／條、單次 60 上限、×N 合併；
  防重複 ×0.25；全域間隔 ≥20 分鐘；冷卻 24 h（稀有 72 h）；時段 早07–11／午11–17／晚17–23／夜23–07。
仍屬遊測 [假設]：其餘池權重沿用提案；睡眠＝23–07；離線需求衰減＝設計 v1；玩家 85% 照顧需求、2% 連點、70% 領日記。
用法：python3 pet_events_final.py [--days 3000] [--seed 7] [--multi 8] [--md out/events_results.md]（退出碼 1＝有 FAIL）
"""
import argparse, random, math, statistics as st, collections, os, sys, hashlib

# ── 定案參數 ─────────────────────────────────────────────
P_HIT = 0.34
INTERVAL = (2.0, 4.0)            # 小時
GLOBAL_GAP_H = 20 / 60           # ≥20 分鐘
CD_H = {'normal': 24.0, 'rare': 72.0, 'tantrum': 48.0}
P_SHINY_DAY = 0.03
RAINBOW_WIN = (17, 23)
RAINBOW_W = 4                    # 遊策定案
TANTRUM_NEED_H = 2.0
SLEEP_WIN = (23, 7)
DIARY_TIP_DAY = 12
LIGHT_PER = 3
CLAIM_CAP = 60
TARGET_POOL = (2.2, 2.4); TARGET_TOTAL = 2.95; TOTAL_REPORT = 2.95; CLOCK_TOL_S = 120.0; CLOCK_FUTURE_H = 24.0   # 回撥容差 120 秒；lastSaveTime > now+24h＝無效
FIREFLY = dict(w=20, win=(17, 23), lights=5, mood=10)
POPUP_MAX = 2
DIARY_DAYS = 14
ANTI = 0.25
BANDS = {'早': (7, 11), '午': (11, 17), '晚': (17, 23), '夜': (23, 7)}
# id, 權重, 稀有?, 可觸發時段(時)；rainbow／tantrum 為獨立觸發，不入權重池
POOL = [('gift', 22, False, (7, 23)), ('butterfly', 20, False, (7, 17)), ('meteor', 10, True, (19, 5)),
        ('sleeptalk', 11, False, (23, 7)), ('treasure', 18, False, (8, 22)), ('rainbow', RAINBOW_W, True, RAINBOW_WIN),
        ('firefly', FIREFLY['w'], False, FIREFLY['win'])]
RARE = {'meteor', 'rainbow'}
ALL_IDS = [e[0] for e in POOL] + ['tantrum']
DECAY = dict(food=6.0, mood=4.0, clean=3.0, energy=5.0)
NEED_FLOOR = 20.0

def in_win(h, w):
    a, b = w
    return (a <= h < b) if a < b else (h >= a or h < b)

def band_of(h):
    for k, w in BANDS.items():
        if in_win(h, w): return k

def cd_of(eid):
    if eid == 'tantrum': return CD_H['tantrum']
    return CD_H['rare'] if eid in RARE else CD_H['normal']

def shiny_of(save_seed, day):
    """閃光日＝hash(saveSeed, 本機日期)；3%；同 seed 同日永遠同結果"""
    h = hashlib.sha256(f'{save_seed}:{day}'.encode()).digest()
    return int.from_bytes(h[:8], 'big') / 2**64 < P_SHINY_DAY

def firefly_reward(mood):
    """螢火散步彈窗領取：光粒 +5、心情 +10（上限 100）"""
    return FIREFLY['lights'], min(100, mood + FIREFLY['mood'])

def diary_claim(entries, mood):
    """日記領取（v5）：每條 +3 光粒（唔分事件種類，螢火散步亦然），冇心情獎勵；回傳（光粒, 心情, 剩餘條數）"""
    k, lights, rest = claim_calc(len(entries)); return lights, mood, rest

def guarantee_due(seen_today, hour, opens_before, mode='v5'):
    """保底判定（只計「今日未見過事件」嘅情況）：v5＝當日首次開 app 即保底＋原規則（16:00 後或第 2 次開）；eve2＝只有原規則"""
    if seen_today > 0: return False
    orig = hour >= 16 or opens_before >= 1
    return True if mode in ('first', 'v5') else (orig if mode == 'eve2' else False)

def sanitize_last_save(v):
    """lastSaveTime 損毀值（NaN／負／非數字）→ None（當冇記錄，唔崩）"""
    try: x = float(v)
    except Exception: return None
    return x if (x == x and x >= 0 and x != float('inf')) else None

def is_sleeping(hour): return in_win(hour % 24, SLEEP_WIN)

def tap_response(hour, taps, needs):
    """連點寵物回應：睡眠中＝輕喚醒（睏睏表情，唔鬧脾氣，唔扣需求）；清醒＝按 5 下／10 s 判鬧脾氣"""
    if is_sleeping(hour): return dict(result='wake_light', face='睏睏', tantrum=False, needs=dict(needs))
    t = tantrum_by_taps(taps); return dict(result='tantrum' if t else 'pet', face='鬧脾氣' if t else '開心', tantrum=t, needs=dict(needs))

def diary_tip(age_days):
    """第 12 日起提示「N 日後作廢」；N＝14−floor(age)"""
    if age_days < DIARY_TIP_DAY or age_days >= 14: return None
    return f'{14 - int(age_days)} 日後作廢'

def diary_groups(entries):
    c = collections.Counter(e['id'] for e in entries); return sorted(c.items(), key=lambda x: -x[1])

def claim_calc(n_entries):
    """一次領取：每條 +3 光粒，上限 60（＝20 條，最舊先領）；回傳（領咗幾條, 光粒, 剩餘條數）"""
    k = min(n_entries, CLAIM_CAP // LIGHT_PER); return k, k * LIGHT_PER, n_entries - k

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
    return worst >= TANTRUM_NEED_H - 1e-9, worst

def tantrum_by_taps(tap_times, window=10.0, need=5):
    """tap_times＝升序秒數；任一連續 need 下嘅（第 need 下−第 1 下）≤window 即觸發"""
    for i in range(len(tap_times) - need + 1):
        if tap_times[i + need - 1] - tap_times[i] <= window + 1e-9: return True
    return False

def rainbow_possible(hour): return in_win(hour, RAINBOW_WIN)

# ── 引擎 ────────────────────────────────────────────────
class Sim:
    def __init__(s, rng, anti=ANTI, p_hit=P_HIT, guarantee='v5', shiny_bug=False, popup_max=POPUP_MAX, diary_days=DIARY_DAYS, save_seed=20261026):
        s.rng, s.anti, s.p_hit, s.guarantee, s.shiny_bug, s.popup_max, s.diary_days, s.save_seed = rng, anti, p_hit, guarantee, shiny_bug, popup_max, diary_days, save_seed
        s.next_draw = rng.uniform(*INTERVAL)
        s.cd_until = {k: -1e9 for k in ALL_IDS}; s.last_event_t = -1e9; s.recent = []
        s.log = []                  # 全部產生嘅事件 dict(t,id,kind)
        s.gen_day = collections.Counter(); s.seen_day = collections.Counter(); s.opens_day = collections.Counter()
        s.shiny_rolled = {}         # 日期 → bool（存檔）
        s.shiny_rolls = 0; s.shiny_days_seen = set(); s.shiny_claimed = set(); s.shiny_reward_claims = 0
        s.diary = []                # dict(t,id,claimed,seen_t)
        s.stats = collections.Counter(); s.popups_per_open = []; s.diary_sizes = []; s.diary_max_age = 0.0
        s.needs = dict(food=90.0, mood=90.0, clean=90.0, energy=90.0)
        s.last_open = None; s.rare_prio_viol = 0; s.rare_prio_checks = 0
        s.last_save = None; s.clock_status = 'ok'; s.tamper_days = set(); s.popup_log = []; s.guar_days = set(); s.tantrum_src = collections.Counter(); s.claim_log = []

    # --- 事件生成 ---
    def _pick(s, t, forced):
        h = t % 24
        el = [e for e in POOL if t >= s.cd_until[e[0]] and in_win(h, e[3])]
        if not el: return None
        ws = [e[1] * (s.anti if e[0] in s.recent[-2:] else 1.0) for e in el]
        if sum(ws) <= 0: ws = [e[1] for e in el]
        return s.rng.choices(el, ws)[0][0]

    def _emit(s, t, eid, kind):
        s.cd_until[eid] = t + cd_of(eid); s.last_event_t = t
        if eid != 'tantrum': s.recent.append(eid)
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
    def clock_check(s, utc, tol_s=CLOCK_TOL_S):
        """防改時鐘（v5.1）：utc＝UTC epoch 小時（唔受時區／DST 影響）。
        · lastSaveTime 比 now 遲 >24h＝無效（視為損毀／離譜）→ 重設為 now，該次唔派獎（status='reset'）
        · 否則 now 比 lastSaveTime 早 >tol_s 秒（預設 120；≤120 唔判）＝改時鐘（status='tamper'），唔更新 lastSaveTime
        · 其餘＝正常（status='ok'）：lastSaveTime＝max(舊值, now)"""
        if s.last_save is not None:
            back_s = round((s.last_save - utc) * 3600.0, 6)
            if back_s > CLOCK_FUTURE_H * 3600.0:
                s.last_save = utc; s.clock_status = 'reset'; s.stats['clock_reset'] += 1; return False
            if back_s > tol_s:
                s.clock_status = 'tamper'; s.stats['tamper_block'] += 1; return False
        s.last_save = utc if s.last_save is None else max(s.last_save, utc); s.clock_status = 'ok'; return True

    def open_app(s, t, p_tap=0.02, care_prob=0.85, utc=None, tol_s=CLOCK_TOL_S):
        day = int(t // 24)
        if not s.clock_check(t if utc is None else utc, tol_s):      # 改時鐘／lastSaveTime 無效：該次唔抽閃光日、唔派獎／唔產生事件（亦唔補領／唔入日記）
            s.tamper_days.add(day); s.popups_per_open.append(0); return [], []
        first_open_today = s.opens_day[day] == 0
        # 閃光日：本機日期首次開 app 抽一次並存檔
        if s.shiny_bug:                    # 反例：每次開 app 重抽
            r = s.rng.random() < P_SHINY_DAY; s.shiny_rolls += 1; s.shiny_rolled[day] = s.shiny_rolled.get(day, False) or r
        elif day not in s.shiny_rolled:    # 定案：hash(saveSeed, date)，首次開 app 評估並存檔
            s.shiny_rolls += 1; s.shiny_rolled[day] = shiny_of(s.save_seed, day)
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
            if is_sleeping(t % 24): s.stats['tap_sleep_wake'] += 1     # 睡眠中連點＝輕喚醒（睏睏），唔鬧脾氣、唔扣需求
            elif t >= s.cd_until['tantrum'] and t - s.last_event_t >= GLOBAL_GAP_H:
                due.append(s._emit(t, 'tantrum', 'tantrum')); s.tantrum_src['tap'] += 1
            else: s.stats['tantrum_blocked'] += 1
        # 離線需求衰減
        if s.last_open is not None:
            E = eff_hours(gap)
            for k in s.needs: s.needs[k] = max(NEED_FLOOR, s.needs[k] - DECAY[k] * E)
        # 玩家領上次留低嘅日記（70% 機率；領完即清）——新增日記要下次開 app 先可領
        if s.diary and s.rng.random() < 0.70: s._claim(t)
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
            if eid: due.append(s._emit(t, eid, 'guarantee')); s.stats['guar_fire'] += 1; s.guar_days.add(day); s.stats['guar_orig'] += 1
            else: s.stats['guar_fail'] += 1
        elif s.guarantee in ('first', 'v5') and (seen_before + len(due)) == 0:
            s.stats['guar_try'] += 1
            eid = s._pick(t, True) if t - s.last_event_t >= GLOBAL_GAP_H else None
            if eid: due.append(s._emit(t, eid, 'guarantee')); s.stats['guar_fire'] += 1; s.guar_days.add(day); s.stats['guar_first' if (s.opens_day[day] == 0 and t % 24 < 16) else 'guar_orig'] += 1
            else: s.stats['guar_fail'] += 1
        # 離線策略：最多彈 popup_max 個（稀有優先，再按最新），其餘入日記
        order = sorted(due, key=lambda e: (e['id'] not in RARE, -e['t']))
        pop = order[:s.popup_max]; rest = order[s.popup_max:]
        n_rare_due = sum(1 for e in due if e['id'] in RARE); n_rare_pop = sum(1 for e in pop if e['id'] in RARE)
        s.rare_prio_checks += 1
        if n_rare_pop != min(s.popup_max, n_rare_due): s.rare_prio_viol += 1
        for e in rest: s.diary.append(dict(t=e['t'], id=e['id'], claimed=False, warned=False))
        s.popups_per_open.append(len(pop)); s.popup_log.append(pop)
        s.stats['popups'] += len(pop); s.stats['to_diary'] += len(rest)
        s.seen_day[day] += len(due); s.opens_day[day] += 1
        s.diary_sizes.append(len(s.diary))
        for d in s.diary:
            if t - d['t'] >= DIARY_TIP_DAY * 24: d['warned'] = True      # 開 app 時日記頁面顯示「N 日後作廢」
        for d in s.diary: s.diary_max_age = max(s.diary_max_age, t - d['t'])
        for e in pop:
            if e['id'] == 'firefly':
                s.stats['firefly_pop'] += 1; s.stats['firefly_lights'] += FIREFLY['lights']; s.needs['mood'] = min(100, s.needs['mood'] + FIREFLY['mood'])
        s.stats['firefly_diary'] += sum(1 for e in rest if e['id'] == 'firefly')
        # 玩家照顧
        for k in s.needs:
            if s.rng.random() < care_prob: s.needs[k] = s.rng.uniform(80, 100)
        s.last_open = t
        return pop, rest

    def claim_shiny(s, day):
        """閃光日獎勵：該日期係閃光日且未領過先俾；已領日期存檔（撥日期去已領閃光日唔可重領）"""
        if day in s.tamper_days or not shiny_of(s.save_seed, day) or day in s.shiny_claimed: return False
        s.shiny_claimed.add(day); s.shiny_reward_claims += 1; return True

    def _claim(s, t):
        """一次領取：最舊先領，每條 +3 光粒，單次上限 60 光粒（＝20 條）"""
        s.diary.sort(key=lambda d: d['t']); k, lights, rest = claim_calc(len(s.diary))
        for d in s.diary[:k]: d['claimed'] = True
        s.diary = s.diary[k:]; s.stats['claimed'] += k; s.stats['claims'] += 1; s.stats['lights'] += lights
        s.claim_log.append((k, lights, rest))
        if rest: s.stats['claims_capped'] += 1

    def _purge(s, t):
        keep = []
        for d in s.diary:
            if t - d['t'] > s.diary_days * 24:
                s.stats['diary_expired'] += 1; s.stats['diary_expired_unclaimed'] += 1
                s.stats['expired_warned' if d.get('warned') else 'expired_unwarned'] += 1
            else:
                if t - d['t'] >= DIARY_TIP_DAY * 24: d['warned'] = True
                keep.append(d)
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
                diary_now=len([d for d in s.diary]), tip=sum(1 for d in s.diary if t_back - d['t'] >= DIARY_TIP_DAY * 24), claims_needed=math.ceil(len(rest) / (CLAIM_CAP // LIGHT_PER)), pop_rare=sum(1 for e in pop if e['id'] in RARE),
                rest_ids=collections.Counter(e['id'] for e in rest))

# ── 案例測試（參考實作；build 以 window.__qa.pet 對照）──────────────────────
def case_tests():
    rows = []
    def add(i, desc, got, exp): rows.append((i, desc, got, exp, 'PASS' if got == exp else 'FAIL'))
    base = dict(food=100, mood=100, clean=100, energy=100)
    # 鬧脾氣：需求 <30 持續 ≥2 小時
    add('TA-01', '飽腹 60（5h 後到 30）離線 6h59m＝低於 30 持續 1h59m', tantrum_by_needs({**base, 'food': 60}, 6 + 59 / 60)[0], False)
    add('TA-02', '飽腹 60（5h 後到 30）離線 7h＝低於 30 持續 2.0h', tantrum_by_needs({**base, 'food': 60}, 7.0)[0], True)
    add('TA-03', '飽腹 60 離線 6h（持續 1h；舊規則 ≥1h 會觸發，新規則唔會）', tantrum_by_needs({**base, 'food': 60}, 6.0)[0], False)
    add('TA-04', '全部需求 ≥80，離線 4h（無需求跌穿）', tantrum_by_needs({**base, 'food': 80, 'mood': 80, 'clean': 80, 'energy': 80}, 4.0)[0], False)
    add('TA-05', '開 app 時飽腹已 25（<30），離線 2h', tantrum_by_needs({**base, 'food': 25}, 2.0)[0], True)
    add('TA-06', '開 app 時飽腹已 25，離線 1.9h', tantrum_by_needs({**base, 'food': 25}, 1.9)[0], False)
    add('TA-07', '離線 30h（有效 12h 封頂）：飽腹 100 跌穿 30 約 7.3h（真實）', tantrum_by_needs(base, 30.0)[0], True)
    add('TA-08', '離線 72h，全 100：任一需求已跌穿 ≥2h', tantrum_by_needs(base, 72.0)[0], True)
    add('TA-09', '精力 40（2h 後到 30，5/h）離線 4h＝低於 30 持續 2h', tantrum_by_needs({**base, 'energy': 40}, 4.0)[0], True)
    add('TA-10', '精力 40 離線 3.99h＝持續 1h59m', tantrum_by_needs({**base, 'energy': 40}, 3.99)[0], False)
    # 鬧脾氣：連點
    add('TB-01', '10 秒內連點 5 次（0,2,4,6,8）', tantrum_by_taps([0, 2, 4, 6, 8]), True)
    add('TB-02', '10 秒內連點 4 次', tantrum_by_taps([0, 2, 4, 6]), False)
    add('TB-03', '5 次但跨 10.0 s（0,2.5,5,7.5,10.0）＝邊界（含 10.0）', tantrum_by_taps([0, 2.5, 5, 7.5, 10.0]), True)
    add('TB-04', '5 次跨 10.01 s', tantrum_by_taps([0, 2.5, 5, 7.5, 10.01]), False)
    add('TB-05', '滑動窗口：早一下孤立點擊＋之後 5 下 5 秒內（0,6,8,9,10,11）', tantrum_by_taps([0, 6, 8, 9, 10, 11]), True)
    add('TB-06', '5 次相隔 3 秒（0,3,6,9,12）＝12 s', tantrum_by_taps([0, 3, 6, 9, 12]), False)
    # 睡眠中連點＝輕喚醒
    nd = dict(food=70, mood=60, clean=80, energy=50)
    r = tap_response(2.0, [0, 2, 4, 6, 8], nd)
    add('SL-01', '睡眠中（02:00）10 秒內連點 5 次→輕喚醒（睏睏），唔鬧脾氣', (r['result'], r['face'], r['tantrum']), ('wake_light', '睏睏', False))
    add('SL-02', '睡眠中連點 5 次→需求完全唔變（唔扣）', r['needs'], nd)
    r2 = tap_response(12.0, [0, 2, 4, 6, 8], nd)
    add('SL-03', '清醒（12:00）同一連點→鬧脾氣', (r2['result'], r2['tantrum']), ('tantrum', True))
    add('SL-04', '睡眠邊界：22:59 清醒／23:00 睡／06:59 睡／07:00 清醒', tuple(is_sleeping(h) for h in (22.99, 23.0, 6.99, 7.0)), (False, True, True, False))
    # 冷卻／間隔（Sim 內 cd_until＝實作對照）
    sm = Sim(random.Random(1)); sm._emit(0.0, 'tantrum', 'x'); sm._emit(1.0, 'gift', 'x'); sm._emit(2.0, 'meteor', 'x')
    ok = lambda eid, t: t >= sm.cd_until[eid]
    add('TC-01', '鬧脾氣冷卻 48h：47.9h 後再觸發', ok('tantrum', 47.9), False)
    add('TC-02', '鬧脾氣冷卻 48h：48.0h 後再觸發', ok('tantrum', 48.0), True)
    add('TC-03', '普通事件冷卻 24h：1.0+23.9h／24.0h', (ok('gift', 24.9), ok('gift', 25.0)), (False, True))
    add('TC-04', '稀有事件冷卻 72h：2.0+71.9h／72.0h', (ok('meteor', 73.9), ok('meteor', 74.0)), (False, True))
    add('TC-05', '全域間隔 ≥20 分鐘：19.9／20.0 分鐘', tuple((t - 5.0) >= GLOBAL_GAP_H - 1e-9 for t in (5.0 + 19.9 / 60, 5.0 + 20.0 / 60)), (False, True))
    # 彩虹（入池：只喺 17–23；冷卻 72h）
    for i, (h, exp) in enumerate([(16.99, False), (17.0, True), (20.0, True), (22.99, True), (23.0, False), (3.0, False), (10.0, False)], 1):
        el = [e[0] for e in POOL if in_win(h, e[3])]
        add(f'RB-0{i}', f'彩虹入池時段 {int(h)}:{int(round((h % 1) * 60)):02d}', 'rainbow' in el, exp)
    add('RB-08', '彩虹唔另擲 10%%：池內權重＝%d，其餘 17–23 池事件權重和 %d' % (RAINBOW_W, sum(e[1] for e in POOL if e[0] != 'rainbow' and in_win(20.0, e[3]))), [e[0] for e in POOL if e[0] == 'rainbow'], ['rainbow'])
    add('RB-09', '稀有集合＝流星夜＋雨後彩虹', sorted(RARE), ['meteor', 'rainbow'])
    # 時段分類
    for i, (h, exp) in enumerate([(6.99, '夜'), (7.0, '早'), (10.99, '早'), (11.0, '午'), (16.99, '午'), (17.0, '晚'), (22.99, '晚'), (23.0, '夜'), (0.0, '夜')], 1):
        add(f'BD-0{i}', f'時段 {h}', band_of(h), exp)
    # 閃光日 hash(saveSeed, date)
    seedA, seedB = 20261026, 777
    d0 = next(d for d in range(1000) if shiny_of(seedA, d))        # 一個閃光日（令比較有意義）
    sa = Sim(random.Random(1), save_seed=seedA); vals = []
    for k in range(5): sa.open_app(d0 * 24 + 8 + k * 0.5); vals.append(sa.shiny_rolled[d0])
    add('SH-01', f'閃光日（第 {d0} 日）同日重開 app 5 次：結果恆為閃光、只評估 1 次', (vals, sa.shiny_rolls), ([True] * 5, 1))
    sb = Sim(random.Random(99), save_seed=seedA); sb.open_app(d0 * 24 + 9)
    add('SH-02', '同 seed、另一個實例／另一個 RNG 狀態、同日→結果一致（閃光）', sb.shiny_rolled[d0], True)
    seq = [shiny_of(seedA, d) for d in range(3650)]           # 逐日前撥 10 年
    order = list(range(3650)); random.Random(3).shuffle(order); rnd = {d: shiny_of(seedA, d) for d in order}
    add('SH-03', '逐日前撥系統日期 3650 日 vs 亂序查詢：每日結果完全一致', all(seq[d] == rnd[d] for d in range(3650)), True)
    add('SH-04', '前撥→後退→再前撥同一日期（20 次）：結果不變', len({shiny_of(seedA, 500) for _ in range(20)}) == 1, True)
    k = sum(seq); add('SH-05', f'前撥 3650 日閃光日比例 3% ±3σ（實測 {100*k/3650:.2f}%）', abs(k / 3650 - 0.03) < 3 * math.sqrt(0.03 * 0.97 / 3650), True)
    ov = sum(1 for d in range(20000) if shiny_of(seedA, d) and shiny_of(seedB, d)); ex = 20000 * 0.03 * 0.03
    add('SH-06', f'不同 seed 閃光日集合唔同（重疊 {ov} 日，期望 {ex:.0f}）', abs(ov - ex) < 4 * math.sqrt(ex), True)
    s_am = Sim(random.Random(5), save_seed=seedA); s_am.open_app(d0 * 24 + 0.02); s_pm = Sim(random.Random(6), save_seed=seedA); s_pm.open_app(d0 * 24 + 23.98)
    add('SH-07', '同一本機日期內 00:01／23:59 首次開 app→同結果（閃光日）', (s_am.shiny_rolled[d0], s_pm.shiny_rolled[d0]), (True, True))
    # 日記：14 日、第 12 日提示、+3 光粒、上限 60、×N 合併
    rng = random.Random(1); s0 = Sim(rng); s0.diary = [dict(t=0.0, id='gift', claimed=False)]
    s0._purge(14 * 24); add('DY-01', '日記：剛好 14.0 日（保留）', len(s0.diary), 1)
    s0.diary = [dict(t=0.0, id='gift', claimed=False)]; s0._purge(14 * 24 + 0.01); add('DY-02', '日記：14 日＋0.01h（作廢）', len(s0.diary), 0)
    add('DT-01', '提示：11.99 日→冇提示', diary_tip(11.99), None)
    add('DT-02', '提示：12.0 日→「2 日後作廢」', diary_tip(12.0), '2 日後作廢')
    add('DT-03', '提示：12.99 日→「2 日後作廢」', diary_tip(12.99), '2 日後作廢')
    add('DT-04', '提示：13.0／13.99 日→「1 日後作廢」[假設：第 13 日起改 1 日]', (diary_tip(13.0), diary_tip(13.99)), ('1 日後作廢', '1 日後作廢'))
    add('DK-01', '領取：1 條＝+3 光粒', claim_calc(1), (1, 3, 0))
    add('DK-02', '領取：20 條＝60 光粒（剛好上限）', claim_calc(20), (20, 60, 0))
    add('DK-03', '領取：21 條＝領 20 條 60 光粒，剩 1 條', claim_calc(21), (20, 60, 1))
    add('DK-04', '領取：14 日缺席約 32 條＝第 1 次 60（剩 12）、第 2 次 36（剩 0）', (claim_calc(32), claim_calc(12)), ((20, 60, 12), (12, 36, 0)))
    g = diary_groups([dict(id='gift')] * 5 + [dict(id='butterfly')] * 3)
    add('DK-05', '×N 合併顯示：禮物×5、蝴蝶×3；總獎勵＝8×3＝24 光粒（唔 cap）', (g, claim_calc(8)[1]), ([('gift', 5), ('butterfly', 3)], 24))
    g = diary_groups([dict(id='gift')] * 25)
    add('DK-06', '×N 合併後獎勵：禮物×25＝領 20 條＝60 光粒（上限），剩禮物×5', (g, claim_calc(25)), ([('gift', 25)], (20, 60, 5)))
    add('DK-07', '×N 合併後獎勵＝N×3（唔係每組 3）：×7＝21 光粒', claim_calc(7)[1], 21)
    s1 = Sim(random.Random(2)); s1.diary = [dict(t=float(i), id='gift', claimed=False, warned=False) for i in range(30)]; s1._claim(100.0)
    add('DK-08', '領取最舊先領＋冪等（同一條唔重複領）', (s1.stats['lights'], len(s1.diary), min(d['t'] for d in s1.diary)), (60, 10, 20.0))
    # 螢火散步（傍晚 17–23 普通事件；+5 光粒、心情 +10）
    for i, (h, exp) in enumerate([(16.99, False), (17.0, True), (20.0, True), (22.99, True), (23.0, False), (3.0, False), (10.0, False)], 1):
        add(f'FF-0{i}', f'螢火散步入池時段 {int(h)}:{int(round((h % 1) * 60)):02d}', 'firefly' in [e[0] for e in POOL if in_win(h, e[3])], exp)
    add('FF-08', '螢火散步獎勵：光粒 +5、心情 50→60', firefly_reward(50), (5, 60))
    add('FF-09', '螢火散步心情 95→100（上限 100）', firefly_reward(95)[1], 100)
    add('FF-10', '螢火散步屬普通事件（非稀有）、冷卻 24 h、權重 20', ('firefly' in RARE, cd_of('firefly'), [e[1] for e in POOL if e[0] == 'firefly'][0]), (False, 24.0, 20))
    add('FF-11', '日記×N 合併：螢火×6＋禮物×3 → 螢火散步×6、禮物×3；光粒＝9 條×3＝27（定案：日記一律 +3／條）', (diary_groups([dict(id='firefly')] * 6 + [dict(id='gift')] * 3), claim_calc(9)[1]), ([('firefly', 6), ('gift', 3)], 27))
    add('FF-12', '日記×N 觸頂：螢火×25 → 領 20 條＝60 光粒，剩螢火×5', (diary_groups([dict(id='firefly')] * 25), claim_calc(25)), ([('firefly', 25)], (20, 60, 5)))
    add('FF-13', '日記螢火散步領取：螢火×13＋禮物×2＝15 條×3＝45 光粒（唔係螢火 +5）、心情唔變（50→50）、未觸頂', diary_claim([1] * 15, 50), (45, 50, 0))
    add('FF-14', '日記螢火散步×21（最舊先）→ 領 20 條＝60 光粒（唔係 +5×20＝100）、心情唔變、剩 ×1', diary_claim([1] * 21, 70), (60, 70, 1))
    add('FF-15', '彈窗 vs 日記：同一螢火散步事件，彈窗領＝+5 光粒＋心情 +10；入日記領＝+3 光粒、心情 +0', (firefly_reward(50), diary_claim([1], 50)[:2]), ((5, 60), (3, 50)))
    # 保底：首次開 app 即保底＋原規則
    for i, (lab, args, exp) in enumerate([
            ('首次開 app 08:00、當日未見事件 → 保底（v5）', (0, 8.0, 0, 'v5'), True), ('首次開 app 15:59、未見事件 → 保底（v5；舊規則 eve2 唔會）', (0, 15.99, 0, 'v5'), True),
            ('首次開 app 08:00、舊規則 eve2 → 唔保底（對照）', (0, 8.0, 0, 'eve2'), False), ('首次開 app 但離線已有到期事件（seen+due>0）→ 唔保底', (1, 8.0, 0, 'v5'), False),
            ('第 2 次開 app（任何時間）、當日仍未見事件 → 保底', (0, 10.0, 1, 'v5'), True), ('16:00 後首次開 → 保底', (0, 16.0, 0, 'v5'), True),
            ('當日已見事件（彈窗過）再開 → 唔保底', (2, 20.0, 3, 'v5'), False)], 1):
        add(f'GU-0{i}', lab, guarantee_due(*args), exp)
    g1 = Sim(random.Random(3)); g1.next_draw = 1e9; r1, _ = g1.open_app(8.0); n1 = len(g1.log); g1.open_app(9.0); n2 = len(g1.log)
    add('GU-08', 'Sim：首次開 app 保底恰觸發 1 個（kind=guarantee），同日再開（已見事件）唔再觸發', (n1, n2, g1.log[0]['kind']), (1, 1, 'guarantee'))
    g2 = Sim(random.Random(4)); g2.next_draw = 1e9; g2.last_event_t = 7.9; g2.open_app(8.0)
    add('GU-09', 'Sim：保底亦受全域間隔 ≥20 分鐘限制（上一事件 6 分鐘前→放棄，唔違規）', (len(g2.log), g2.stats['guar_fail']), (0, 1))
    g3 = Sim(random.Random(5)); g3.next_draw = 1e9; g3.cd_until = {k: 1e9 for k in ALL_IDS}; g3.open_app(8.0)
    add('GU-10', 'Sim：所有事件冷卻中／時段擋住→保底失敗唔崩、唔違規', (len(g3.log), g3.stats['guar_fail']), (0, 1))
    # 閃光日「已領」按日期存檔
    seedA = 20261026; sd_days = [d for d in range(2000) if shiny_of(seedA, d)]; nd_day = next(d for d in range(2000) if not shiny_of(seedA, d))
    sc = Sim(random.Random(1), save_seed=seedA)
    add('SC-01', f'閃光日（第 {sd_days[0]} 日）首次領獎', sc.claim_shiny(sd_days[0]), True)
    add('SC-02', '同日期再領（重開 app／殺 app 後）→ 唔可重領', sc.claim_shiny(sd_days[0]), False)
    for d in range(sd_days[0], sd_days[0] + 5): sc.opens_day[d] = 1          # 日期前撥 5 日
    add('SC-03', f'前撥幾日後撥返去已領閃光日（第 {sd_days[0]} 日）→ 唔可重領', sc.claim_shiny(sd_days[0]), False)
    import json as _j; saved = _j.dumps(sorted(sc.shiny_claimed)); sc2 = Sim(random.Random(7), save_seed=seedA); sc2.shiny_claimed = set(_j.loads(saved))
    add('SC-04', '存檔→重載後（已領集合序列化）同日期仍唔可重領', sc2.claim_shiny(sd_days[0]), False)
    add('SC-05', f'撥去未領嘅另一個閃光日（第 {sd_days[1]} 日）→ 可領一次（唔同日期）', (sc.claim_shiny(sd_days[1]), sc.claim_shiny(sd_days[1])), (True, False))
    add('SC-06', f'撥去非閃光日（第 {nd_day} 日）→ 冇獎', sc.claim_shiny(nd_day), False)
    sc3 = Sim(random.Random(8), save_seed=seedA); got = sum(1 for d in range(365) if sc3.claim_shiny(d)); exp = sum(1 for d in range(365) if shiny_of(seedA, d))
    add('SC-07', f'[已知限制，資訊] 逐日前撥 365 日可領 {got} 次＝該段所有閃光日各 1 次（≈3%；單調時鐘／前撥上限仍屬 P2）', got, exp)
    # 防改時鐘（lastSaveTime；UTC epoch）
    T0 = 24 * 400 + 10.0; sd0 = [d for d in range(2000) if shiny_of(20261026, d)]
    c = Sim(random.Random(11)); res = [c.open_app(T0 + h)[0] is not None and c.stats['tamper_block'] for h in (0, 2, 26)]
    add('CG-01', '正常遞增開 app（+0／+2／+26 h）→ 唔誤判（tamper_block=0）', c.stats['tamper_block'], 0)
    c = Sim(random.Random(12)); c.open_app(T0); c.open_app(T0 + 1.0); n_before = len(c.log); c.open_app(T0 + 0.5)
    add('CG-02', '撥早 30 分鐘（早於 lastSaveTime）→ 當次判改時鐘：冇新事件、不更新 lastSaveTime', (c.stats['tamper_block'], len(c.log) == n_before, c.last_save), (1, True, T0 + 1.0))
    d0 = sd0[0]; c = Sim(random.Random(13)); c.open_app((d0 + 1) * 24 + 5); ok1 = c.open_app(d0 * 24 + 12) == ([], [])
    add('CG-03', f'撥早 1 日去閃光日（第 {d0} 日，未開過）→ 判改時鐘：該日唔抽閃光日（shiny_rolled 冇記錄）、唔可領閃光獎勵', (ok1, d0 in c.shiny_rolled, c.claim_shiny(d0)), (True, False, False))
    c = Sim(random.Random(14)); c.open_app(d0 * 24 + 9); got = c.claim_shiny(d0); c.open_app((d0 + 3) * 24 + 9); c.open_app(d0 * 24 + 20); again = c.claim_shiny(d0)
    add('CG-04', '已領閃光日：前撥 3 日再撥返去該日重領 → 唔可重領（已領存檔＋判改時鐘雙重）', (got, again, c.shiny_reward_claims), (True, False, 1))
    c = Sim(random.Random(15)); c.open_app(T0); c.open_app(T0 + 72); b = []
    for h in (5, 30, 71.9, 72.05):
        st0 = dict(c.stats); r_ = c.open_app(T0 + h); b.append(c.clock_status)
    add('CG-05', '撥前 3 日（>24h）再撥返：撥返當次因 lastSaveTime 比 now 遲 >24h＝無效→重設、該次唔派獎；之後正常（唔鎖住）', (b, c.stats['clock_reset'], c.stats['tamper_block']), (['reset', 'ok', 'ok', 'ok'], 1, 0))
    c = Sim(random.Random(25)); c.open_app(T0); c.open_app(T0 + 20); b = []
    for h in (1, 19.9, 20.0, 20.01): c.open_app(T0 + h); b.append(c.clock_status)
    add('CG-20', '撥前 20 h（≤24h）再撥返：撥返期間判改時鐘（鎖住）直至 lastSaveTime 追上（+20.0 h 等於 lastSaveTime 唔判，但 ≤120 秒內）', (b, c.stats['tamper_block']), (['tamper', 'tamper', 'ok', 'ok'], 2))
    c = Sim(random.Random(16)); c.open_app(T0 + 50); saved = repr(c.last_save); c2 = Sim(random.Random(17)); c2.last_save = sanitize_last_save(float(eval(saved))); r = c2.open_app(T0 + 40)
    add('CG-06', '存檔→重載後（lastSaveTime 序列化）撥早仍判改時鐘', (r, c2.stats['tamper_block']), (([], []), 1))
    add('CG-07', 'lastSaveTime 損毀（NaN／負數／字串／null）→ 當冇記錄、唔崩', [sanitize_last_save(v) for v in (float('nan'), -5, 'abc', None)], [None, None, None, None])
    def ls_case(off_h):
        q = Sim(random.Random(18)); q.last_save = T0 + off_h; q.open_app(T0); st = q.clock_status; ls1 = q.last_save; q.open_app(T0 + 1.0); return st, ls1 == T0, q.clock_status
    add('CG-08', 'lastSaveTime＝now+25h（>24h）→ 無效：重設為 now、該次唔派獎；下次開 app 正常', ls_case(25.0), ('reset', True, 'ok'))
    add('CG-15', 'lastSaveTime＝now+23h59m（≤24h，邊界）→ 仍有效＝判改時鐘（鎖住，唔重設）；下次（+1h）仍鎖', ls_case(23 + 59 / 60), ('tamper', False, 'tamper'))
    add('CG-16', 'lastSaveTime＝now+24h00m00s（剛好 24h，唔大於）→ 仍有效＝判改時鐘', ls_case(24.0)[0], 'tamper')
    add('CG-17', 'lastSaveTime＝now+24h00m10s（>24h）→ 無效、重設', ls_case(24.0 + 10 / 3600)[0], 'reset')
    def back_case(sec):
        q = Sim(random.Random(26)); q.clock_check(1000.0); ok = q.clock_check(1000.0 - sec / 3600.0); return ok, q.clock_status, q.last_save == 1000.0
    add('CG-18', '回撥 119 秒（≤120）→ 唔判篡改', back_case(119)[:2], (True, 'ok'))
    add('CG-19', '回撥 120 秒（剛好容差，≤120）→ 唔判篡改；lastSaveTime 唔倒退', (back_case(120)[:2], back_case(120)[2]), ((True, 'ok'), True))
    add('CG-21', '回撥 121 秒（>120）→ 判篡改；lastSaveTime 唔變', (back_case(121)[:2], back_case(121)[2]), ((False, 'tamper'), True))
    # 時區／DST（以 UTC epoch 比較；本機牆鐘比較＝錯誤實作對照）
    hk_local = 20.0; la_local_after = hk_local + 1.0 - 16.0     # HKT(UTC+8)→PST(UTC−8)：牆鐘跳後 16 h，UTC 前進 1 h
    c = Sim(random.Random(19)); c.clock_check(100.0); ok_tz = c.clock_check(101.0)
    add('CG-09', '時區 HKT→UTC−8（牆鐘後退 16 h、UTC 前進 1 h）→ 唔誤判；對照：牆鐘比較（錯誤實作）會誤判', (ok_tz, la_local_after < hk_local), (True, True))
    c = Sim(random.Random(20)); c.clock_check(5.5); ok_dst = c.clock_check(6.17)      # 美東 11/01 UTC 05:30＝01:30 EDT；06:10＝01:10 EST（牆鐘 01:30→01:10）
    add('CG-10', 'DST 秋季回撥（美東 01:30 EDT→01:10 EST；UTC 05:30→06:10）→ 唔誤判；對照：牆鐘 1.50→1.17 比較會誤判', (ok_dst, 1.0 + 10 / 60 < 1.5), (True, True))
    c = Sim(random.Random(21)); c.clock_check(7.0); ok_sp = c.clock_check(7.5)           # 春季前撥（02:00 跳 03:00）：UTC 照樣前進
    add('CG-11', 'DST 春季前撥（當日 23 h）→ 唔誤判；閃光日按本機日期仍每日 1 次', (ok_sp, shiny_of(20261026, 70) == shiny_of(20261026, 70)), (True, True))
    c = Sim(random.Random(22)); c.clock_check(1000.0); r_ntp = c.clock_check(1000.0 - 30 / 3600)
    add('CG-12', 'NTP 自動校時回撥 30 秒 → 唔誤判（容差 2 分鐘）', r_ntp, True)
    c = Sim(random.Random(23)); c.open_app(T0); c.open_app(T0 + 720)
    for k in range(1, 130): c.open_app(T0 + 6 * k)
    add('CG-13', '[已知風險，M1 唔處理] 前撥 30 日（>24h）後撥返：撥返當次唔派獎＋重設，之後即正常（唔鎖住）→ 前撥可重複掃閃光日／事件，代價＝每次撥返損失 1 次開 app', (c.stats['clock_reset'], c.stats['tamper_block']), (1, 0))
    add('CG-14', '[已知風險，M1 唔處理] 只改時區（UTC 不變、本機日期 +1）去攞下一日閃光日：lastSaveTime(UTC) 唔變→唔判改時鐘（前撥作弊仍可行，但每日期只領一次；見 SC-07）', (lambda q: (q.clock_check(500.0), q.clock_check(500.0)))(Sim(random.Random(24))), (True, True))
    return rows

# ── 主程式 ────────────────────────────────────────────────
class patched:
    """暫時改池／冷卻參數（敏感度分析用）"""
    def __init__(s, pool=None, rare_cd=None, decay=None): s.pool, s.rare_cd, s.decay = pool, rare_cd, decay
    def __enter__(s):
        s.o = (list(POOL), list(ALL_IDS), CD_H['rare'], dict(DECAY))
        if s.pool is not None: POOL[:] = s.pool; ALL_IDS[:] = [e[0] for e in s.pool] + ['tantrum']
        if s.rare_cd is not None: CD_H['rare'] = s.rare_cd
        if s.decay is not None: DECAY.update(s.decay)
    def __exit__(s, *a):
        POOL[:] = s.o[0]; ALL_IDS[:] = s.o[1]; CD_H['rare'] = s.o[2]; DECAY.update(s.o[3])

def kinds(sm): return collections.Counter(e['kind'] for e in sm.log)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--days', type=int, default=3000); ap.add_argument('--seed', type=int, default=7); ap.add_argument('--md', default=None); ap.add_argument('--multi', type=int, default=8)
    a = ap.parse_args(); out = []; P = out.append; D = a.days
    fails = []; warns = []
    P('# 事件池抽取模擬結果（pet_events_final.py；遊策最終定案 v5.1）\n')
    P(f'> {D} 日／作息；seed={a.seed}。參數：命中率 {P_HIT}、抽取 2–4 h、全域間隔 ≥20 分鐘、單事件冷卻 24 h（稀有 72 h，鬧脾氣 48 h）、彩虹權重 {RAINBOW_W}、螢火散步權重 {FIREFLY['w']}、離線最多彈 {POPUP_MAX} 個（稀有優先）、日記留 {DIARY_DAYS} 日（第 {DIARY_TIP_DAY} 日起提示；每條 +{LIGHT_PER} 光粒；單次上限 {CLAIM_CAP}）、保底＝16:00 後或當日第 2 次開 app 仍冇事件即觸發、防重複 ×{ANTI}、閃光日 hash(saveSeed,date) {P_SHINY_DAY:.0%}。\n')
    P('> 事件池（9）＝7 個池抽取事件：禮物／蝴蝶／流星夜（稀有）／夢話／尋寶／雨後彩虹（稀有，17–23，權重 %s）／螢火散步（17–23，權重 %s，+5 光粒＋心情 +10）＋鬧脾氣（條件觸發）＋閃光日（每日狀態，**唔計入事件數**）。\n' % (RAINBOW_W, FIREFLY['w']))
    runs = {pn: run_profile(prof, D, random.Random(a.seed)) for pn, prof in PROFILES.items()}
    # A
    P(f'## A. 每日事件數 — pass：池抽取事件 {TARGET_POOL[0]}–{TARGET_POOL[1]} 個／日；總事件（抽取＋鬧脾氣＋保底）≤{TARGET_TOTAL}；單次返嚟彈窗 ≤{POPUP_MAX}\n')
    P('| 作息 | 池抽取事件/日 | 鬧脾氣/日 | 保底/日 | **總事件/日** | 鬧脾氣佔總% | 活躍日見到 0 事件% | p10／p90（總） | 單次最多彈 | 彈窗佔比 | 日記佔比 | 判定 |'); P('|---|---|---|---|---|---|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        k = kinds(s); pool_d = k['draw'] / D; tan_d = k['tantrum'] / D; gu_d = k['guarantee'] / D; tot_d = len(s.log) / D
        gen = sorted(s.gen_day[d] for d in range(D)); act = sorted(set(int(t // 24) for t in sess)); seen = [s.seen_day[d] for d in act]
        zero = 100 * sum(1 for x in seen if x == 0) / len(act); mx = max(s.popups_per_open); tot = s.stats['popups'] + s.stats['to_diary']
        ok = TARGET_POOL[0] <= pool_d <= TARGET_POOL[1] and tot_d <= TARGET_TOTAL and mx <= POPUP_MAX
        if not ok: fails.append(f'A:{pn}')
        if tot_d > TOTAL_REPORT: warns.append(f'A:{pn} 總事件 {tot_d:.2f} >{TOTAL_REPORT}（超過 ≤{TARGET_TOTAL} 上限）')
        P(f"| {pn} | {pool_d:.2f} | {tan_d:.2f} | {gu_d:.2f} | **{tot_d:.2f}** | {100*tan_d/tot_d:.0f}% | {zero:.1f} | {gen[int(0.1*D)]}／{gen[int(0.9*D)]} | {mx} | {100*s.stats['popups']/tot:.0f}% | {100*s.stats['to_diary']/tot:.0f}% | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（「池抽取事件」＝定時抽取命中；總事件含鬧脾氣同保底；以事件發生時間計、含離線期間。）\n')
    # B
    P('## B. 保底觸發率（v5＝當日首次開 app 未有事件即觸發＋原規則 16:00 後／第 2 次開）— pass：活躍日見到 0 事件 ≤1%（≥3 次/日作息）；輕度／早鳥只開 1–2 次，≤3%\n')
    P('| 作息 | 保底嘗試（日）% | 保底成功觸發（日）% | 保底失敗（池空／間隔）次 | 開 app 日數 | 活躍日零事件%（有保底） | 零事件%（無保底） | 判定 |'); P('|---|---|---|---|---|---|---|---|')
    for pn, prof in PROFILES.items():
        s, sess = runs[pn]; act = sorted(set(int(t // 24) for t in sess))
        s0, sess0 = run_profile(prof, D, random.Random(a.seed), guarantee='none'); act0 = sorted(set(int(t // 24) for t in sess0))
        z1 = 100 * sum(1 for d in act if s.seen_day[d] == 0) / len(act); z0 = 100 * sum(1 for d in act0 if s0.seen_day[d] == 0) / len(act0)
        lim = 1.0 if len(prof['times']) >= 3 or prof.get('every_other') else 3.0; ok = z1 <= lim
        if not ok: fails.append(f'B:{pn}')
        P(f"| {pn} | {100*s.stats['guar_try']/len(act):.1f} | {100*len(s.guar_days)/len(act):.1f} | {s.stats['guar_fail']} | {len(act)} | {z1:.2f} | {z0:.2f} | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（保底失敗＝觸發時所有事件被時段／冷卻擋住，或離上一事件 <20 分鐘；「零事件%」以「玩家見到」計。）\n')
    # C
    lo = lambda n: 100 * (P_SHINY_DAY - 3 * math.sqrt(P_SHINY_DAY * 0.97 / n)); hi = lambda n: 100 * (P_SHINY_DAY + 3 * math.sqrt(P_SHINY_DAY * 0.97 / n))
    P('## C. 閃光日（hash(saveSeed, date)）— pass：各作息比例 3% ±3σ；20 萬日二項 |z|<3.3；每日評估恰 1 次；逐日前撥／重開／同 seed 同日結果一致（案例 SH-01…07，見 H）\n')
    P('| 作息 | 閃光日比例（開 app 日） | 開 app 日數 | 3σ 範圍 | 每日評估次數（應 =1） | 判定 |'); P('|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        act = sorted(set(int(t // 24) for t in sess)); k = sum(1 for d in act if s.shiny_rolled.get(d)); fr = 100 * k / len(act); rpd = s.shiny_rolls / len(act)
        ok = lo(len(act)) <= fr <= hi(len(act)) and abs(rpd - 1) < 1e-9
        if not ok: fails.append(f'C:{pn}')
        P(f"| {pn} | {fr:.2f}% | {len(act)} | {lo(len(act)):.1f}–{hi(len(act)):.1f}% | {rpd:.2f} | **{'PASS' if ok else 'FAIL'}** |")
    n = 200000; kk = sum(1 for d in range(n) if shiny_of(20261026, d)); mu = n * P_SHINY_DAY; sd = math.sqrt(n * P_SHINY_DAY * 0.97); z = abs(kk - mu) / sd
    P(f'\nhash 二項檢定（20 萬個日期）：閃光日 {kk}，期望 {mu:.0f}±{sd:.0f}，|z|={z:.2f} → **{"PASS" if z < 3.3 else "FAIL"}**。')
    if z >= 3.3: fails.append('C:binom')
    sb, sess_b = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed), shiny_bug=True); act_b = sorted(set(int(t // 24) for t in sess_b))
    frb = 100 * sum(1 for d in act_b if sb.shiny_rolled.get(d)) / len(act_b)
    P(f"**測試靈敏度（反例）**：若每次開 app 都用隨機重抽（錯誤實作，一般 4 次／日），閃光日比例升至 **{frb:.1f}%**（每日評估 {sb.shiny_rolls/len(act_b):.2f} 次）→ 比例檢查＋「每日評估 =1」可抓到。")
    rng = random.Random(a.seed + 3); first = []
    for _ in range(20000):
        kq = 1
        while rng.random() >= P_SHINY_DAY: kq += 1
        first.append(kq)
    q = lambda m: 100 * sum(1 for x in first if x <= m) / len(first)
    P(f"\n新玩家首次見到閃光日：7 日內 {q(7):.0f}%、14 日內 {q(14):.0f}%、30 日內 {q(30):.0f}%、60 日內 {q(60):.0f}%；中位 {sorted(first)[len(first)//2]} 日，p95 {sorted(first)[int(0.95*len(first))]} 日。")
    P('\n**閃光日已領存檔（v4 採納 P2）**：獎勵按日期存「已領」，撥日期去已領閃光日唔可重領（SC-01…06）；hash 令「重開 app／逐日前撥」唔增加抽中機會（SH-03／04）。**v5.1 lastSaveTime 防改時鐘（CG-01…21）**：系統時間比 lastSaveTime（UTC epoch）早 >120 秒＝當日唔抽閃光日同事件；lastSaveTime 比 now 遲 >24h＝無效、重設、該次唔派獎。**已知風險（M1 唔處理）**：前撥 >24h 再撥返只損失 1 次開 app（CG-13），前撥 365 日仍可領約 3% 嘅閃光日（SC-07）；只改時區唔會被偵測（CG-14）。')
    # D
    P('\n## D. 冷卻／全域間隔違規（獨立驗證器掃全部事件）— pass：違規 =0；最小間隔 ≥20 分鐘；同事件最小間隔 ≥24 h（稀有 ≥72 h）；鬧脾氣 ≥48 h\n')
    P('| 作息 | 事件總數 | 單事件冷卻違規 | 全域間隔違規 | 最小事件間隔（分鐘） | 同事件最小間隔 h（普通／稀有） | 鬧脾氣最小間隔 h | 全域間隔擋咗嘅抽取 | 判定 |'); P('|---|---|---|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        cdv, gapv, mg, ms = validate(s)
        norm = min([v for k, v in ms.items() if k not in RARE and k != 'tantrum'] or [float('nan')]); rare = min([v for k, v in ms.items() if k in RARE] or [float('nan')]); tn = ms.get('tantrum', float('nan'))
        ok = cdv == 0 and gapv == 0
        if not ok: fails.append(f'D:{pn}')
        P(f"| {pn} | {len(s.log)} | {cdv} | {gapv} | {mg:.1f} | {norm:.1f}／{rare:.1f} | {tn:.1f} | {s.stats['gap_block']} | **{'PASS' if ok else 'FAIL'}** |")
    tb = sum(sm.stats['tamper_block'] for sm, _ in runs.values())
    if tb: fails.append('D:正常作息被誤判改時鐘')
    tb += sum(sm.stats['clock_reset'] for sm, _ in runs.values())
    P(f'\n正常作息（遞增時間）被誤判改時鐘／重設次數：**{tb}**（要求 0）→ **{"PASS" if tb == 0 else "FAIL"}**；`lastSaveTime` 防改時鐘案例 CG-01…21 見 §H。')
    P('\n（20 分鐘全域間隔對 2–4 h 抽取幾乎唔會生效；只會擋「保底／鬧脾氣／換日」貼近上一事件嘅情況。）')
    # E
    P('\n## E. 離線返嚟：缺席 N 日（一般 4 次/日，暖機 14 日；每格 400 次）— pass：彈窗 ≤2；稀有優先違規 0；日記＝缺席期間 ≤14 日內事件；超過 14 日嘅作廢\n')
    P('| 缺席日數 | 缺席期間產生 | 返嚟彈窗（最多） | 日記新增 平均／p95／最多 | 返嚟時帶「2 日後作廢」提示條數（平均） | 領完要幾次（上限 60） | 到期即作廢（平均） | 稀有優先違規 | 判定 |'); P('|---|---|---|---|---|---|---|---|---|')
    diary_14 = None
    for nd in (1, 3, 7, 14, 21, 30):
        res = [absence_trial(nd, random.Random(a.seed * 1000 + i)) for i in range(400)]
        dn = sorted(r['diary_new'] for r in res); pops = max(r['popups'] for r in res); rv = sum(r['rare_viol'] for r in res); exp = st.mean(r['expired'] for r in res)
        ok = pops <= POPUP_MAX and rv == 0 and (nd <= 14 or exp > 0)
        if nd == 14: diary_14 = (st.mean(dn), dn[int(0.95 * len(dn))], dn[-1], st.mean(r['gen'] for r in res), st.mean(r['tip'] for r in res), st.mean(r['claims_needed'] for r in res))
        if not ok: fails.append(f'E:{nd}')
        P(f"| {nd} | {st.mean(r['gen'] for r in res):.1f} | {pops} | {st.mean(dn):.1f}／{dn[int(0.95*len(dn))]}／{dn[-1]} | {st.mean(r['tip'] for r in res):.1f} | {st.mean(r['claims_needed'] for r in res):.1f} | {exp:.1f} | {rv} | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（缺席 >14 日：超過 14 日嘅事件返嚟即作廢＝日記上限約 14 日量。**彈窗只有 2 個，其餘進日記→缺席 14 日一次過有約 %.0f 條日記＝%.0f 光粒，要領 %.1f 次（每次最多 60 光粒＝20 條）**；一鍵領取要支援「續領」。）\n' % (diary_14[0], diary_14[0] * LIGHT_PER, diary_14[5]))
    P('### E2. 日記留存／領取／提示（一般 4 次/日、3000 日；70% 開 app 會領日記；一鍵領取每次最多 60 光粒）\n')
    s, sess = runs['一般 4次/日']
    P(f"- 日記最大年齡：{s.diary_max_age/24:.2f} 日（要求 ≤14.0 日）；已領 {s.stats['claimed']} 項／{s.stats['claims']} 次領取，共 {s.stats['lights']} 光粒；單次最多 {max(c[1] for c in s.claim_log)} 光粒（≤{CLAIM_CAP}）；因上限而留低 {s.stats['claims_capped']} 次。")
    P(f"- 日記到期作廢 {s.stats['diary_expired']} 項（有提示 {s.stats['expired_warned']}／冇提示 {s.stats['expired_unwarned']}）；開 app 後日記列表長度：平均 {st.mean(s.diary_sizes):.2f}、p95 {sorted(s.diary_sizes)[int(0.95*len(s.diary_sizes))]}、最大 {max(s.diary_sizes)}。")
    s2, sess2 = runs['隔日 1次']; P(f"- 隔日玩家：領取 {s2.stats['claims']} 次、共 {s2.stats['lights']} 光粒、單次最多 {max(c[1] for c in s2.claim_log)}；日記到期作廢 {s2.stats['diary_expired']} 項（有提示 {s2.stats['expired_warned']}／冇提示 {s2.stats['expired_unwarned']}）；日記最大年齡 {s2.diary_max_age/24:.2f} 日。")
    rng = random.Random(a.seed + 9); s3 = Sim(rng); sess3 = make_sessions(PROFILES['一般 4次/日'], 14, rng)
    for t in sess3: s3.open_app(t)
    t_back = (14 + 14) * 24 + 8.5; s3.open_app(t_back); sizes = []
    for k in range(1, 21): s3._purge(t_back + k * 24); sizes.append(len(s3.diary))
    P(f"- 缺席 14 日返嚟後**唔領**日記，之後第 1／7／14／15／16／20 日日記剩餘：{sizes[0]}／{sizes[6]}／{sizes[13]}／{sizes[14]}／{sizes[15]}／{sizes[19]}（應隨年齡逐批作廢，14 日後清空）。")
    ok = sizes[19] == 0 and sizes[0] > sizes[13] >= sizes[19]
    if not ok: fails.append('E:retention')
    ok2 = s.stats['expired_unwarned'] == 0 and s2.stats['expired_unwarned'] == 0
    # 提示有效：一般玩家無作廢；隔日有開 app→有提示。若有「作廢但冇提示」要報
    if s.stats['diary_expired'] + s2.stats['diary_expired'] and not ok2: warns.append('E:有日記未經提示即作廢（玩家 12–14 日內冇開 app）')
    ok3 = max(c[1] for c in s.claim_log + s2.claim_log) <= CLAIM_CAP
    if not ok3: fails.append('E:cap')
    P(f"  → 留存 **{'PASS' if ok else 'FAIL'}**；單次領取 ≤{CLAIM_CAP} 光粒 **{'PASS' if ok3 else 'FAIL'}**\n")
    # F
    P('## F. 雨後彩虹（17–23 入池抽取，唔另擲 10%；稀有冷卻 72 h）— pass：只喺 17:00–22:59 出現；頻率約每 13 日一次（可接受 11–15 日）\n')
    P('| 作息 | 彩虹次數/日 | 平均幾日一次 | 全部喺 17–23 時？ | 判定 |'); P('|---|---|---|---|---|')
    f_days = []
    for pn, (s, sess) in runs.items():
        rb = [e for e in s.log if e['id'] == 'rainbow']; inwin = all(rainbow_possible(e['t'] % 24) for e in rb); per_day = len(rb) / D; days = 1 / per_day; f_days.append(days)
        ok_win = inwin; ok_f = 11 <= days <= 15
        if not ok_win: fails.append(f'F:時段:{pn}')
        if not ok_f: fails.append(f'F:頻率:{pn}')
        P(f"| {pn} | {per_day:.3f} | {days:.1f} | {'是' if inwin else '否'} | 時段 **{'PASS' if ok_win else 'FAIL'}**／頻率 **{'PASS' if ok_f else 'FAIL'}** |")
    P('\n### F2. 彩虹頻率敏感度（一般 4 次/日）— 頻率取決於「傍晚可用事件嘅數量」，而唔係彩虹權重\n')
    P('彩虹頻率主要取決於傍晚（17–23）可入池嘅普通事件數量（24 h 冷卻令佢哋傍晚多數已冷卻，彩虹變成「剩低嘅唯一選擇」）。v3＝禮物、尋寶；v4 加螢火散步。\n')
    P('| 池設定 | 彩虹權重 | 彩虹幾日一次（6 作息範圍） | 池抽取/日 | 總事件/日 |'); P('|---|---|---|---|---|')
    mk = lambda w, extra=(): [e if e[0] != 'rainbow' else ('rainbow', w, True, RAINBOW_WIN) for e in POOL] + list(extra)
    base_pool = list(POOL)
    ff = ('firefly', 20, False, (17, 23)); ln = ('lantern', 15, False, (17, 23))
    def sweep(label, pool, w, rare_cd=None):
        with patched(pool=pool, rare_cd=rare_cd):
            r = []
            for pn, prof in PROFILES.items():
                sm, _ = run_profile(prof, D, random.Random(a.seed)); k = kinds(sm); n_r = sum(1 for e in sm.log if e['id'] == 'rainbow'); r.append((D / max(n_r, 1), k['draw'] / D, len(sm.log) / D))
        P(f"| {label} | {w} | {min(x[0] for x in r):.1f}–{max(x[0] for x in r):.1f} | {min(x[1] for x in r):.2f}–{max(x[1] for x in r):.2f} | {min(x[2] for x in r):.2f}–{max(x[2] for x in r):.2f} |")
    nofire = [e for e in POOL if e[0] != 'firefly']
    mk0 = lambda w: [e if e[0] != 'rainbow' else ('rainbow', w, True, RAINBOW_WIN) for e in nofire]
    sweep('v3（無螢火散步）', mk0(1), 1)
    for w in (1, 2, 3, 4, 8): sweep('v4（含螢火散步）' + (' ←定案' if w == RAINBOW_W else ''), mk(w), w)
    sweep('v4＋稀有冷卻 120 h', mk(RAINBOW_W), RAINBOW_W, rare_cd=120)
    P(f'\n→ 彩虹約 13 日一次要靠「傍晚普通事件夠多」；定案（螢火散步＋彩虹權重 {RAINBOW_W}）見上表 ←定案 行。')
    # G
    P('\n## G. 鬧脾氣（任一需求 <30 持續 ≥2 小時，或 10 秒內連點 5 次；冷卻 48 h）— pass：頻率同佔比報告；佔總事件 ≤15%、≤0.40 次/日（建議值）\n')
    P('| 作息 | 鬧脾氣次/日 | 佔總事件% | 來源：需求 | 來源：連點 | 睡眠中連點→輕喚醒（次） | 被冷卻／間隔擋住次 | 判定 |'); P('|---|---|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        tn = [e for e in s.log if e['id'] == 'tantrum']; tr = len(tn) / D; sh = 100 * tr / (len(s.log) / D); ok = tr <= 0.40 and sh <= 15
        if not ok: warns.append(f'G:{pn}（鬧脾氣 {tr:.2f}/日、佔 {sh:.0f}%）')
        P(f"| {pn} | {tr:.3f} | {sh:.1f}% | {s.tantrum_src['needs']} | {s.tantrum_src['tap']} | {s.stats['tap_sleep_wake']} | {s.stats['tantrum_blocked']} | **{'PASS' if ok else '偏高'}** |")
    P('\n需求觸發率與作息有關：愈少開 app 愈易觸發（輕度／早鳥／隔日較高）；連點來源按 [假設] 每次開 app 2%，睡眠中（23–07）連點只輕喚醒、唔鬧脾氣。\n')
    # H
    P('## H. 規則案例測試（參考實作；真 build 以 `window.__qa.pet` 對照同一張表）\n')
    P('| ID | 案例 | 結果 | 預期 | 判定 |'); P('|---|---|---|---|---|')
    for i, d, got, exp, v in case_tests():
        P(f'| {i} | {d} | {got} | {exp} | **{v}** |')
        if v == 'FAIL': fails.append(f'H:{i}')
    # I
    P('\n## I. 事件分佈與防重複（一般 4 次/日）\n')
    s, sess = runs['一般 4次/日']; cnt = collections.Counter(e['id'] for e in s.log); tot = len(s.log)
    P('| 事件 | 占比 | 稀有 | 時段 |'); P('|---|---|---|---|')
    win = {e[0]: e[3] for e in POOL}; win['tantrum'] = '條件'
    for k in ALL_IDS: P(f"| {k} | {100*cnt.get(k,0)/tot:.1f}% | {'是' if k in RARE else ''} | {win[k]} |")
    def rep3(sm):
        evs = [e['id'] for e in sm.log if e['id'] != 'tantrum']; c = n = 0
        for i in range(2, len(evs)): n += 1; c += len(set(evs[i-2:i+1])) < 3
        return 100 * c / max(1, n), 100 * sum(1 for x, y in zip(evs, evs[1:]) if x == y) / max(1, len(evs) - 1)
    P('\n| 防重複權重 | 3 連內重複% | 相鄰同事件% | 事件/日曆日 |'); P('|---|---|---|---|')
    for an in (1.0, ANTI, 0.0):
        sm, _ = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed), anti=an); r3, r1 = rep3(sm)
        P(f"| ×{an} | {r3:.0f} | {r1:.1f} | {st.mean(sm.gen_day[d] for d in range(D)):.2f} |")
    P('\n（冷卻 24 h 令同一事件最多每日 1 次，本身已壓低重複。）')
    # J
    P('\n## J. 命中率敏感度（一般 4 次/日；保底 v5）— 池抽取目標 2.2–2.4、總 ≤2.95\n')
    P('| p_hit | 池抽取/日 | 鬧脾氣/日 | 保底/日 | 總事件/日 | 活躍日零事件% | 保底觸發日% |'); P('|---|---|---|---|---|---|---|')
    for ph in (0.30, 0.32, 0.33, 0.34, 0.35, 0.36, 0.38):
        sm, ss = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed), p_hit=ph); act = sorted(set(int(t // 24) for t in ss)); kc = kinds(sm)
        P(f"| {ph}{' ←定案' if ph == P_HIT else ''} | {kc['draw']/D:.2f} | {kc['tantrum']/D:.2f} | {kc['guarantee']/D:.2f} | {len(sm.log)/D:.2f} | {100*sum(1 for d in act if sm.seen_day[d]==0)/len(act):.2f} | {100*len(sm.guar_days)/len(act):.1f} |")
    P(f'\n## K. 鬧脾氣對需求衰減／冷卻嘅敏感度（一般 4 次/日、p_hit {P_HIT}）\n')
    P('| 衰減版本（飽腹/心情/清潔/精力 每小時） | 鬧脾氣次/日 | 總事件/日 |'); P('|---|---|---|')
    for nm, dd in (('設計 v1（6/4/3/5）', dict(DECAY)), ('−15%（5.1/3.4/2.55/4.25）', {k: v * 0.85 for k, v in DECAY.items()}), ('V6（飽腹 4，其餘 −15%）', {'food': 4.0, 'mood': 3.4, 'clean': 2.55, 'energy': 4.25})):
        with patched(decay=dd):
            sm, ss = run_profile(PROFILES['一般 4次/日'], D, random.Random(a.seed)); kc = kinds(sm)
            P(f"| {nm} | {kc['tantrum']/D:.2f} | {len(sm.log)/D:.2f} |")
    P('\n## L. 螢火散步統計（一般 4 次/日及全部作息）— pass：全部喺 17:00–22:59；占比／日；光粒收入計入\n')
    P('| 作息 | 螢火散步/日 | 占池抽取% | 全部喺 17–23？ | 彈窗領取次 | 日記條目 | 光粒收入/日（彈窗 +5） | 判定 |'); P('|---|---|---|---|---|---|---|---|')
    for pn, (s, sess) in runs.items():
        ff_ev = [e for e in s.log if e['id'] == 'firefly']; inw = all(in_win(e['t'] % 24, FIREFLY['win']) for e in ff_ev); k = kinds(s)
        ok = inw and len(ff_ev) > 0
        if not ok: fails.append(f'L:{pn}')
        P(f"| {pn} | {len(ff_ev)/D:.3f} | {100*len(ff_ev)/max(1,k['draw']+k['guarantee']):.1f}% | {'是' if inw else '否'} | {s.stats['firefly_pop']} | {s.stats['firefly_diary']} | {s.stats['firefly_lights']/D:.2f} | **{'PASS' if ok else 'FAIL'}** |")
    P('\n（彈窗 +5 光粒、心情 +10 已計入模擬；日記條目（v5 定案）一律 +3 光粒、冇心情獎勵（FF-11…15）。）')
    # M. 多 seed 一致性
    seeds = [7, 3, 5, 11, 13, 17, 19, 23][:a.multi]
    P(f'\n## M. 多 seed 一致性（{len(seeds)} 個 seed × 6 作息 × {D} 日；各項取 seed 間 min–max，並列通過 seed 數）\n')
    P('| 指標 | 要求 | 範圍（6 作息 × 各 seed） | 通過 seed 數 |'); P('|---|---|---|---|')
    agg = collections.defaultdict(list); passes = collections.defaultdict(int)
    for sd in seeds:
        chk = collections.defaultdict(lambda: True)
        for pn, prof in PROFILES.items():
            sm, ss = run_profile(prof, D, random.Random(sd)); k = kinds(sm); act = sorted(set(int(t // 24) for t in ss))
            pool_d = k['draw'] / D; tot_d = len(sm.log) / D; tan_d = k['tantrum'] / D; zero = 100 * sum(1 for d in act if sm.seen_day[d] == 0) / len(act)
            rb = sum(1 for e in sm.log if e['id'] == 'rainbow'); rbd = D / max(rb, 1); cdv, gapv, mg, ms = validate(sm)
            sh = 100 * sum(1 for d in act if sm.shiny_rolled.get(d)) / len(act)
            for key, val, ok in (('池抽取事件/日', pool_d, TARGET_POOL[0] <= pool_d <= TARGET_POOL[1]), ('總事件/日', tot_d, tot_d <= TARGET_TOTAL), ('其中 >2.95 嘅作息數', float(tot_d > TARGET_TOTAL), True),
                                 ('鬧脾氣/日', tan_d, tan_d <= 0.40), ('彩虹幾日一次', rbd, 11 <= rbd <= 15), ('活躍日零事件%', zero, zero <= (3.0 if len(prof['times']) < 3 and not prof.get('every_other') else 1.0)),
                                 ('冷卻＋間隔違規', float(cdv + gapv), cdv + gapv == 0), ('閃光日比例%', sh, lo(len(act)) <= sh <= hi(len(act))), ('彈窗最多', float(max(sm.popups_per_open)), max(sm.popups_per_open) <= POPUP_MAX)):
                agg[key].append(val); chk[key] = chk[key] and ok
        for key in chk: passes[key] += chk[key]
    req = {'池抽取事件/日': '2.2–2.4', '總事件/日': '≤2.95', '其中 >2.95 嘅作息數': '資訊', '鬧脾氣/日': '≤0.40（建議）', '彩虹幾日一次': '11–15', '活躍日零事件%': '≤1%（≥3 次/日）／≤3%（輕度、早鳥）', '冷卻＋間隔違規': '0', '閃光日比例%': '3% ±3σ', '彈窗最多': '≤2'}
    for key in req:
        v = agg[key]; P(f"| {key} | {req[key]} | {min(v):.2f}–{max(v):.2f} | {passes[key]}/{len(seeds)} |")
        if key != '其中 >2.95 嘅作息數' and passes[key] < len(seeds): fails.append(f'M:{key}（{passes[key]}/{len(seeds)}）')
    # N. 方案對比（定案偏差時嘅建議）
    P(f'\n## N. 敏感度對比（{len(seeds[:4])} 個 seed × 6 作息；範圍＝min–max）— v5.1 定案 vs 鄰近檔位\n')
    P('| 方案 | 池抽取/日（2.2–2.4） | 總事件/日（≤2.95） | 彩虹幾日一次（11–15） | 輕度零事件%（≤3） | 早鳥零事件%（≤3） | 保底/日（最大） |'); P('|---|---|---|---|---|---|---|')
    def variant(label, w=RAINBOW_W, ph=P_HIT, g='v5'):
        pool = [e if e[0] != 'rainbow' else ('rainbow', w, True, RAINBOW_WIN) for e in POOL]; R = []
        for sd in seeds[:4]:
            for pn, prof in PROFILES.items():
                with patched(pool=pool):
                    sm, ss = run_profile(prof, D, random.Random(sd), p_hit=ph, guarantee=g)
                k = kinds(sm); act = sorted(set(int(t // 24) for t in ss)); rb = sum(1 for e in sm.log if e['id'] == 'rainbow')
                R.append((pn, k['draw'] / D, len(sm.log) / D, D / max(rb, 1), 100 * sum(1 for d in act if sm.seen_day[d] == 0) / len(act), k['guarantee'] / D))
        rg = lambda i, names=None: (lambda v: f'{min(v):.2f}–{max(v):.2f}')([r[i] for r in R if names is None or r[0] in names])
        P(f"| {label} | {rg(1)} | {rg(2)} | {rg(3)} | {rg(4, ['輕度 2次/日'])} | {rg(4, ['早鳥只朝午'])} | {max(r[5] for r in R):.2f} |")
    variant(f'**定案**：彩虹 w{RAINBOW_W}、p_hit {P_HIT}、保底 v5（首次開即保底＋原規則）')
    variant('p_hit 0.33', ph=0.33); variant('p_hit 0.35', ph=0.35); variant('彩虹 w3', w=3); variant('彩虹 w5', w=5)
    variant('（對照）保底只用原規則 eve2', g='eve2'); variant('（對照）v4：w3、p_hit 0.33、eve2', w=3, ph=0.33, g='eve2')
    P('\n## 總判定\n')
    P(('**全部 PASS**' if not fails else '**有 FAIL：** ' + ', '.join(fails)))
    if warns: P('\n**留意（非 FAIL）：** ' + '；'.join(warns))
    txt = '\n'.join(out); print(txt)
    if a.md: os.makedirs(os.path.dirname(a.md) or '.', exist_ok=True); open(a.md, 'w').write(txt + '\n')
    sys.exit(1 if fails else 0)

if __name__ == '__main__': main()
