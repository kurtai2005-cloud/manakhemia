#!/usr/bin/env python3
"""pet_behavior_sim.py — 《微光小圃》加深方案 模組 1「寵物動態」行為頻率模擬（遊測）
驗證：待機／走動／玩耍／環境互動／睡覺 比例，「太吵」「太靜」指標；按性格（活潑／文靜／貪吃）、需求狀態、時段分組。
模型（全部參數＝提案，見 PARAMS）：
  - 待機動畫（眨眼／搖擺／呵欠）每 6–15 秒隨機一次（plan 原文）。
  - 自主行動：每次回到靜止後等 U(wait) 秒，再按性格加權抽一個行動（走動／跳／玩耍／環境互動／原地發呆），並有「懶惰機率」。
  - 環境互動 4 款共用冷卻；需求 <30 → 行動意欲下降、表情改為對應不適；睡眠狀態只做 Zzz。
用法：python3 pet_behavior_sim.py [--runs 300] [--session 180] [--md out/behavior_results.md]
"""
import argparse, random, statistics as st, collections, os

ORIG_PARAMS = dict(
    idle_anim_gap=(6, 15), idle_anim_dur={'blink': 0.6, 'sway': 2.0, 'yawn': 2.5}, idle_anim_w={'blink': 5, 'sway': 3, 'yawn': 1},
    wait=(6, 16),                      # 兩次自主行動之間最短靜止（秒）
    dur={'walk': (2.0, 5.0), 'jump': (0.8, 1.2), 'play': (4, 8), 'env': (4, 8), 'stare': (2, 4)},
    env_cd=45,                         # 環境互動冷卻（秒）
    # 性格權重：walk, jump, play, env, stare；lazy＝跳過本次行動機率
    personality={'活潑': dict(w=dict(walk=45, jump=20, play=20, env=12, stare=3), lazy=0.15),
                 '文靜': dict(w=dict(walk=25, jump=4, play=10, env=25, stare=36), lazy=0.40),
                 '貪吃': dict(w=dict(walk=30, jump=6, play=14, env=15, stare=35), lazy=0.30)},
    low_need_lazy_add=0.25,            # 任何需求 <30：更懶
    tired_lazy_add=0.35,               # 精力 <30：更懶，且 walk 變慢（用時 ×1.6）
)
# ── 遊策定案版（2026-10-26）：env_cd 260 s、wait 5–10 s、性格權重按遊測建議；常駐呼吸／微動畫另計 ──
import copy
PARAMS = copy.deepcopy(ORIG_PARAMS)
PARAMS['env_cd'] = 260
PARAMS['wait'] = (5, 10)
PARAMS['personality'] = {'活潑': dict(w=dict(walk=45, jump=20, play=20, env=12, stare=3), lazy=0.15),
                         '文靜': dict(w=dict(walk=35, jump=4, play=10, env=25, stare=20), lazy=0.30),
                         '貪吃': dict(w=dict(walk=40, jump=6, play=14, env=15, stare=25), lazy=0.25)}
VISIBLE_LOCO = ('walk', 'jump', 'play', 'env')

def simulate(pers, secs, rng, P=PARAMS, low_need=False, tired=False, asleep=False, tap_every=None):
    """回傳 dict：每種狀態佔時、自主行動數、無明顯變化最長間隔、無位移最長間隔"""
    t = 0.0; acc = collections.Counter(); acts = collections.Counter()
    if asleep:
        return dict(frac={'sleep': 1.0}, acts=acts, per_min=0.0, max_gap_any=0.0, max_gap_loco=secs, loco_time=0.0, tap=0)
    pp = P['personality'][pers]; lazy = pp['lazy'] + (P['low_need_lazy_add'] if low_need else 0) + (P['tired_lazy_add'] if tired else 0)
    lazy = min(0.9, lazy)
    next_idle = rng.uniform(*P['idle_anim_gap']); next_act = rng.uniform(*P['wait']); env_ready = 0.0
    events = []   # (start, end, kind)
    cur_end = 0.0
    while t < secs:
        # 找下一個事件
        if t >= cur_end:
            if t >= next_act:
                if rng.random() < lazy:
                    next_act = t + rng.uniform(*P['wait'])
                else:
                    w = dict(pp['w'])
                    if t < env_ready: w['env'] = 0
                    k = rng.choices(list(w), list(w.values()))[0]
                    d = rng.uniform(*P['dur'][k]) * (1.6 if (tired and k == 'walk') else 1.0)
                    if k == 'env': env_ready = t + d + P['env_cd']
                    events.append((t, min(secs, t + d), k)); acc[k] += min(d, secs - t); acts[k] += 1
                    cur_end = t + d; next_act = cur_end + rng.uniform(*P['wait'])
                    next_idle = max(next_idle, cur_end + 1.0)
                    t = cur_end; continue
            if t >= next_idle:
                k = rng.choices(list(P['idle_anim_w']), list(P['idle_anim_w'].values()))[0]
                d = P['idle_anim_dur'][k]; events.append((t, min(secs, t + d), 'idle_' + k)); acc['idle_anim'] += min(d, secs - t)
                cur_end = t + d; next_idle = cur_end + rng.uniform(*P['idle_anim_gap']); t = cur_end; continue
        t = min(cur_end if cur_end > t else 1e9, next_act if next_act > t else 1e9, next_idle if next_idle > t else 1e9, secs)
    # 指標：事件間隔（任何可見動畫 vs 位移類）
    def max_gap(kinds):
        ts = [(a, b) for a, b, k in events if kinds(k)]
        g = 0.0; prev = 0.0
        for a, b in ts: g = max(g, a - prev); prev = b
        return max(g, secs - prev)
    gaps_any = max_gap(lambda k: True); gaps_loco = max_gap(lambda k: k in VISIBLE_LOCO)
    total_act = sum(acts.values()); loco_time = sum(acc[k] for k in VISIBLE_LOCO)
    frac = {k: acc[k] / secs for k in acc}; frac['still'] = max(0.0, 1 - sum(acc.values()) / secs)
    return dict(frac=frac, acts=acts, per_min=total_act / (secs / 60), max_gap_any=gaps_any, max_gap_loco=gaps_loco, loco_time=loco_time / secs, tap=0)

def agg(pers, secs, runs, seed, **kw):
    rng = random.Random(seed); rs = [simulate(pers, secs, rng, **kw) for _ in range(runs)]
    def m(f): return st.mean(f(r) for r in rs)
    def p95(f): v = sorted(f(r) for r in rs); return v[int(0.95 * len(v)) - 1]
    return dict(per_min=m(lambda r: r['per_min']), loco=m(lambda r: r['loco_time']), still=m(lambda r: r['frac'].get('still', 0)),
                idle=m(lambda r: r['frac'].get('idle_anim', 0)), gap_any_p95=p95(lambda r: r['max_gap_any']), gap_loco_p95=p95(lambda r: r['max_gap_loco']),
                zero_act_pct=100 * sum(1 for r in rs if sum(r['acts'].values()) == 0) / runs,
                env_per_h=m(lambda r: r['acts'].get('env', 0)) * 3600 / secs, jump_per_min=m(lambda r: r['acts'].get('jump', 0)) * 60 / secs,
                mix={k: m(lambda r, k=k: r['acts'].get(k, 0)) for k in ('walk', 'jump', 'play', 'env', 'stare')})

# 通過準則（提案）
CRIT = dict(per_min=(1.5, 5.0), loco=(0.17, 0.28), gap_any_p95=(None, 20.0), gap_loco_p95_3min=(None, 100.0), zero_act_3min_pct=(None, 5.0), jump_per_min=(None, 2.5))

def verdict(a, secs):
    long_ = secs >= 3600
    v = []
    lo, hi = CRIT['per_min']
    v.append('太靜' if a['per_min'] < lo else ('太吵' if a['per_min'] > hi else 'OK'))
    lo, hi = CRIT['loco']
    v.append('位移比' + ('偏低' if a['loco'] < lo else ('偏高' if a['loco'] > hi else 'OK')))
    v.append('靜止比' + ('偏高' if a['still'] > 0.60 else 'OK'))
    v.append('環境互動' + (('太密' if a['env_per_h'] > 12 else ('偏疏' if a['env_per_h'] < 10 else 'OK')) if long_ else '（短觀看不評）'))
    return ' / '.join(v)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--runs', type=int, default=300); ap.add_argument('--session', type=int, default=180); ap.add_argument('--seed', type=int, default=5); ap.add_argument('--md', default=None)
    a = ap.parse_args(); out = []; P = out.append; S = a.session
    P('# 寵物行為頻率模擬結果（pet_behavior_sim.py；遊策定案參數版）\n')
    P(f'> 每組 {a.runs} 次、每次觀看 {S} 秒（典型 session 1–3 分鐘）；環境互動頻率另以 3600 秒×40 組量度（短時間量度會被「開頭必抽」偏高，**之前以 600 秒量度得出「env_cd 360 → 10–12 次/小時」係高估，實際 360 只有 8–9 次/小時**）。\n')
    P('定案參數：env_cd **260 s**；wait **5–10 s**；活潑 walk45/jump20/play20/env12/stare3 lazy0.15；文靜 walk35/jump4/play10/env25/stare20 lazy0.30；貪吃 walk40/jump6/play14/env15/stare25 lazy0.25；待機動畫 6–15 s；另加常駐呼吸（令「幀完全冇變化」＝0）。\n')
    P('**通過準則（定案）**：位移類（走／跳／玩／環境互動）佔時 **17–28%**；環境互動 **10–12 次/小時**；自主行動 1.5–5 次/分；任何可見動畫最長間隔 p95 ≤20 s；位移最長間隔 p95 ≤100 s（3 分鐘 session）；3 分鐘零自主行動 ≤5%；跳 ≤2.5 次/分；性格有差異（活潑位移佔時 ≥ 文靜×1.25，跳次數 ≥ 文靜×3）。\n')
    P('## A. 按性格（需求正常、清醒；位移／間隔以 180 s×%d 組，環境互動以 3600 s×40 組）\n' % a.runs)
    P('| 性格 | 行動/分 | 位移佔時 | 位移最長間隔 p95 | 3 分鐘零行動% | 跳/分 | 環境互動/小時 | 完全靜止佔時（未計呼吸） | 判定 |'); P('|---|---|---|---|---|---|---|---|---|')
    res = {}
    for pers in PARAMS['personality']:
        r = agg(pers, S, a.runs, a.seed); rl = agg(pers, 3600, 40, a.seed); r['env_per_h'] = rl['env_per_h']; res[pers] = r
        ok = (0.17 <= r['loco'] <= 0.28) and (10 <= r['env_per_h'] <= 12) and r['gap_loco_p95'] <= 100 and r['zero_act_pct'] <= 5 and r['jump_per_min'] <= 2.5
        P(f"| {pers} | {r['per_min']:.1f} | {100*r['loco']:.0f}% | {r['gap_loco_p95']:.0f}s | {r['zero_act_pct']:.1f} | {r['jump_per_min']:.2f} | {r['env_per_h']:.1f} | {100*r['still']:.0f}% | **{'PASS' if ok else 'FAIL'}** {verdict(r, S)} |")
    d1 = res['活潑']['loco'] / res['文靜']['loco']; d2 = res['活潑']['jump_per_min'] / max(1e-9, res['文靜']['jump_per_min'])
    P(f"\n性格差異：活潑／文靜 位移佔時比 {d1:.2f}（要求 ≥1.25）；跳次數比 {d2:.1f}（要求 ≥3）→ **{'PASS' if d1 >= 1.25 and d2 >= 3 else 'FAIL'}**\n")
    P('## B. 按狀態（文靜／活潑）\n')
    P('| 性格 | 狀態 | 行動/分 | 位移佔時 | 位移最長間隔 p95 | 3 分鐘零行動% | 判定 |'); P('|---|---|---|---|---|---|---|')
    for pers in ('活潑', '文靜'):
        for nm, kw in (('正常', {}), ('有需求 <30', dict(low_need=True)), ('精力 <30（眼瞓）', dict(tired=True)), ('兩者皆低', dict(low_need=True, tired=True))):
            r = agg(pers, S, a.runs, a.seed, **kw)
            P(f"| {pers} | {nm} | {r['per_min']:.1f} | {100*r['loco']:.0f}% | {r['gap_loco_p95']:.0f}s | {r['zero_act_pct']:.1f} | {verdict(r, S)} |")
    P('\n（需求／精力偏低時位移比下降屬預期；準則只要求 3 分鐘零行動 ≤5%，兩者皆低可放寬至 ≤20%。）')
    P('\n## C. 觀看長度（文靜）— 長時間掛機有冇「太吵」\n')
    P('| 觀看 | 行動/分 | 位移佔時 | 環境互動/小時 | 判定 |'); P('|---|---|---|---|---|')
    for secs in (60, 180, 900, 3600):
        n = 200 if secs <= 180 else (60 if secs <= 900 else 40)
        r = agg('文靜', secs, n, a.seed)
        P(f"| {secs}s | {r['per_min']:.1f} | {100*r['loco']:.0f}% | {r['env_per_h']:.0f}{'（開頭偏高，僅供參考）' if secs < 3600 else ''} | {verdict(r, secs)} |")
    P('\n## C2. 原提案 vs 定案（env 以 3600 s 量度）\n')
    P('| 性格 | 版本 | 行動/分 | 位移佔時 | 環境互動/小時 | 位移最長間隔 p95（180 s） |'); P('|---|---|---|---|---|---|')
    for pers in ('活潑', '文靜', '貪吃'):
        for nm, pr in (('原提案', ORIG_PARAMS), ('定案', PARAMS)):
            r = agg(pers, 3600, 40, a.seed, P=pr); r3 = agg(pers, 180, a.runs, a.seed, P=pr)
            P(f"| {pers} | {nm} | {r['per_min']:.1f} | {100*r['loco']:.0f}% | {r['env_per_h']:.1f} | {r3['gap_loco_p95']:.0f}s |")
    P('\n## C3. env_cd 敏感度（3600 s×40；文靜／活潑／貪吃 環境互動次/小時）\n')
    P('| env_cd | 活潑 | 文靜 | 貪吃 |'); P('|---|---|---|---|')
    for cd in (360, 300, 260, 240):
        T = copy.deepcopy(PARAMS); T['env_cd'] = cd
        P(f"| {cd}s | " + ' | '.join(f"{agg(p, 3600, 40, a.seed, P=T)['env_per_h']:.1f}" for p in ('活潑', '文靜', '貪吃')) + ' |')
    P('\n## D. 睡眠比例（時段）\n')
    P('睡眠由狀態機外部決定（精力／23:00–07:00 就寢／玩家關燈），行為模擬只負責 Zzz。以 `decay_weiguang.py` 嘅日循環邏輯估：自動就寢建議 23–07＝8 小時；pet-one-pager 睡眠 +12/h 精力、由 20 睡到 100 約 6.7 小時 → **夜間睡眠 6.7–8 小時（28–33% 全日）；日間唔應自主入睡（除精力 <20）**。測試見 QA/pet-deepening-test-plan.md §4。')
    txt = '\n'.join(out); print(txt)
    if a.md: os.makedirs(os.path.dirname(a.md), exist_ok=True); open(a.md, 'w').write(txt + '\n')

if __name__ == '__main__': main()
