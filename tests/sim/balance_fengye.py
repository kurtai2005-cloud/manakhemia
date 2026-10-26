#!/usr/bin/env python3
"""balance_fengye.py — 《風野競走》MVP 平衡 Monte Carlo（遊測）

做法：直接用遊程原型嘅真實 sim.js／data.js（Node）跑比賽，唔係另寫一套公式，所以結果同遊戲一致。
  python3 balance_fengye.py [--src <windrun src 目錄>] [--n 20000] [--out out/fengye_results.md]
src 搜尋次序：--src > $WINDRUN_SRC > <repo>/src > <repo>/windrun-proto/src > /workspace/windrun-proto/src
需要：Python 3.8+、Node 16+（無額外套件）。

量度：
 A) 出場勝率：隨機 3v3（雙方 AI、隨機首發、隨機賽道、同等級），野靈 X 所在隊嘅勝率（平均必為 50%）。
    健康帶（遊測假設）：45–55%；>58% 視為過強、<42% 視為過弱。
 B) 反事實：同種子禁用換人／技能，勝負改變比例（一頁設計驗收：換人／技能改變勝負 ≥30%）。
 C) 關卡：AI 代打「所有有序組合」玩家隊 vs 該關對手；報「可贏組合比例」（race 近乎確定性，故勝率≈組合比例）。
    ※玩家等級係假設值（見報告），AI 代打≠真人。
"""
import argparse, json, math, os, subprocess, sys, tempfile, statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(HERE, 'fengye_harness.js')

def find_src(cli):
    root = os.path.abspath(os.path.join(HERE, '..', '..'))
    cands = [cli, os.environ.get('WINDRUN_SRC'), os.path.join(root, 'src'),
             os.path.join(root, 'windrun-proto', 'src'), '/workspace/windrun-proto/src']
    for c in cands:
        if c and os.path.exists(os.path.join(c, 'sim.js')) and os.path.exists(os.path.join(c, 'data.js')):
            return c
    sys.exit('搵唔到 windrun src（要有 sim.js／data.js）；用 --src 指定')

SRC = None
def run(sc):
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(sc, f)
    try:
        return json.loads(subprocess.check_output(['node', HARNESS, SRC, f.name]))
    finally:
        os.unlink(f.name)

# ---------------- 建議改動（PROPOSAL）：全部係「提案值」，唔係已定案 ----------------
PROPOSAL = {
    'creatures': {
        'narrowcat':  {'base': {'speed': 71, 'stamina': 92}},          # 80/80 → 71/92
        'windweasel': {'base': {'speed': 68}},                          # 74 → 68
        'tingyu':     {'base': {'speed': 68, 'stamina': 92}, 'apt': [2, 2, 4, 3, 3]},  # 72/90、懸橋 2→3
        'namifin':    {'base': {'speed': 68}},                          # 64 → 68
        'mistfern':   {'base': {'speed': 67}},                          # 62 → 67
        'mochi':      {'base': {'speed': 71}},                          # 70 → 71
        'frostdeer':  {'apt': [3, 2, 1, 4, 3]},                         # 懸橋 2→3
    },
    'stages': {
        '1': {'oppTeam': [['namifin', 3], ['frostdeer', 3]]},
        '2': {'oppLv': 3},
        '3': {'oppTeam': [['windweasel', 7], ['frostdeer', 7], ['gravelbadger', 7]]},
    },
}
PROPOSAL_DESC = [
    '窄樑貓：基礎速度 80→71、耐力 80→92（強度由「速度怪」變成「懸橋專家」）',
    '風鼬：基礎速度 74→68', '汀羽：基礎速度 72→68、耐力 90→92、懸橋適性 2→3',
    '浪鰭：基礎速度 64→68', '霧蕨：基礎速度 62→67', '苔團：基礎速度 70→71', '霜角鹿：懸橋適性 2→3',
    '第 1 關對手：汀羽＋霧蕨 Lv3 → 浪鰭＋霜角鹿 Lv3', '第 2 關對手：全隊 Lv5 → Lv3',
    '第 3 關影子隊：風鼬／窄樑貓／霜角鹿 Lv6 → 風鼬／霜角鹿／碎石獾 Lv7（換掉窄樑貓，換人／技能腳本不變）',
]
SKILL_TWEAK = {'P': {'skill_mult': {'boost': 1.4, 'trip': 0.7}, 'skill_duration': {'boost': 6, 'trip': 6, 'shield': 6}}}

def merge(a, b):
    out = json.loads(json.dumps(a))
    for k, v in b.items():
        out[k] = merge(out.get(k, {}), v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out

def ci(p, n):
    return 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / n)

def field_table(ov, n, lvs, tracks):
    rows, meta = {}, {}
    for lv in lvs:
        r = run({'exp': 'field', 'n': n, 'lv': lv, 'tracks': tracks, 'overrides': ov, 'seed': 7 + lv})
        for cid, v in r['per'].items():
            rows.setdefault(r['names'][cid], {})[lv] = (100 * v['w'] / v['n'], v['n'])
        meta[lv] = (r['avgDur'], r['sideAWin'])
    return rows, meta

def fmt_field(rows, meta, lvs):
    L = ['| 野靈 | ' + ' | '.join('Lv%d 勝率' % lv for lv in lvs) + ' | 判定 |', '|---|' + '---|' * (len(lvs) + 1)]
    for name, d in sorted(rows.items(), key=lambda kv: -S.mean(x[0] for x in kv[1].values())):
        avg = S.mean(x[0] for x in d.values())
        flag = '🔴 過強' if avg > 58 else ('🟠 偏強' if avg > 55 else ('🔴 過弱' if avg < 42 else ('🟠 偏弱' if avg < 45 else '🟢 健康')))
        L.append('| %s | ' % name + ' | '.join('%.1f%% ±%.1f' % (d[lv][0], 100 * ci(d[lv][0] / 100, d[lv][1])) for lv in lvs) + ' | %s |' % flag)
    L.append('')
    L.append('平均時長：' + '、'.join('Lv%d %.1fs' % (lv, meta[lv][0]) for lv in lvs) + '；甲方（先手位）勝率：' + '、'.join('%.1f%%' % (100 * meta[lv][1]) for lv in lvs))
    return '\n'.join(L)

def track_breakdown(ov, n, who):
    out = []
    r = run({'exp': 'field', 'n': n, 'lv': 5, 'tracks': ['main'], 'overrides': ov, 'seed': 31})  # main＝五地形各一段
    for tk, label in [('s1', '苔坡入門賽賽道'), ('s2', '灘霜盃賽道'), ('s3', '懸橋峽谷賽道'), ('main', '標準五地形賽道')]:
        rr = run({'exp': 'field', 'n': n, 'lv': 5, 'tracks': [tk], 'overrides': ov, 'seed': 41})
        out.append((label, {rr['names'][c]: 100 * rr['per'][c]['w'] / rr['per'][c]['n'] for c in who}))
    return out

def stage_rows(ov, stage, lvs, seeds=2):
    r = run({'exp': 'stage', 'stage': stage, 'lvs': lvs, 'seeds': seeds, 'overrides': ov})
    res = {}
    for lv in lvs:
        rows = r['res'][str(lv)]
        w = [x['wr'] for x in rows]
        gate = {}
        wins = [x for x in rows if x['wr'] >= .5]
        for nm in ('窄樑貓', '風鼬'):
            gate[nm] = (100 * sum(1 for x in wins if nm in x['team']) / len(wins)) if wins else 0
        res[lv] = dict(avg=100 * S.mean(w), n=len(rows), win=len(wins), gate=gate,
                       best=sorted(wins, key=lambda x: -x['margin'])[:3])
    return r['oppLv'], res

def main():
    global SRC
    ap = argparse.ArgumentParser()
    ap.add_argument('--src'); ap.add_argument('--n', type=int, default=20000)
    ap.add_argument('--out', default=os.path.join(HERE, 'out', 'fengye_results.md'))
    a = ap.parse_args(); SRC = find_src(a.src)
    n = a.n; tracks = ['main', 's1', 's2', 's3']; lvs = [3, 5, 10]
    md = ['# 風野競走 MVP 平衡模擬原始結果（由 balance_fengye.py 生成）', '', 'sim 來源：`%s`；每個等級 %d 場隨機 3v3。' % (SRC, n), '']

    md += ['## A. 現況（無改動）出場勝率', '']
    base_rows, base_meta = field_table({}, n, lvs, tracks)
    md += [fmt_field(base_rows, base_meta, lvs), '']
    md += ['### 窄樑貓／風鼬／汀羽 按賽道（Lv5）', '', '| 賽道 | 窄樑貓 | 風鼬 | 汀羽 |', '|---|---|---|---|']
    for label, d in track_breakdown({}, n // 2, ['narrowcat', 'windweasel', 'tingyu']):
        md.append('| %s | %.1f%% | %.1f%% | %.1f%% |' % (label, d['窄樑貓'], d['風鼬'], d['汀羽']))
    md.append('')

    md += ['## B. 換人／技能影響勝負（反事實，Lv6，%d 場）' % (n // 4), '']
    f0 = run({'exp': 'flip', 'n': n // 4, 'lv': 6, 'tracks': tracks})
    f1 = run({'exp': 'flip', 'n': n // 4, 'lv': 6, 'tracks': tracks, 'overrides': merge(PROPOSAL, {})})
    f2 = run({'exp': 'flip', 'n': n // 4, 'lv': 6, 'tracks': tracks, 'overrides': merge(PROPOSAL, SKILL_TWEAK)})
    md += ['| 設定 | 禁換人→勝負改變 | 禁技能→勝負改變 | 兩者皆禁 | 每場換人 | 每場技能 | 平均時長 |', '|---|---|---|---|---|---|---|']
    for nm, f in [('現況', f0), ('建議改動', f1), ('建議改動＋技能加強（疾風衝 ×1.4／絆草 ×0.7，持續 3→6 秒）', f2)]:
        md.append('| %s | %.1f%% | %.1f%% | %.1f%% | %.2f | %.2f | %.1fs |' % (nm, 100 * f['flipNoSwap'], 100 * f['flipNoSkill'], 100 * f['flipNoBoth'], f['swapsPerMatch'], f['skillsPerMatch'], f['avgDur']))
    md.append('')

    md += ['## C. 關卡難度（AI 代打全部有序組合；「可贏組合比例」）', '']
    plan = {1: [1, 3, 5], 2: [3, 5, 7], 3: [4, 5, 6, 7, 8]}
    for label, ov in [('現況', {}), ('建議改動', PROPOSAL)]:
        md += ['### ' + label, '', '| 關卡 | 對手等級 | 玩家等級（假設） | 可贏組合 | 可贏組合佔窄樑貓比例 | 佔風鼬比例 |', '|---|---|---|---|---|---|']
        for st in (1, 2, 3):
            oppLv, res = stage_rows(ov, st, plan[st])
            for lv in plan[st]:
                x = res[lv]
                md.append('| 第%d關 | Lv%d | Lv%d | %.0f%%（%d/%d） | %.0f%% | %.0f%% |' % (st, oppLv, lv, x['avg'], x['win'], x['n'], x['gate']['窄樑貓'], x['gate']['風鼬']))
        md.append('')

    md += ['## D. 建議改動後出場勝率（重新模擬）', '']
    new_rows, new_meta = field_table(PROPOSAL, n, lvs, tracks)
    md += [fmt_field(new_rows, new_meta, lvs), '', '### 建議改動清單', ''] + ['- ' + s for s in PROPOSAL_DESC] + ['']

    # 靜態指標
    md += ['## E. 靜態強度（基礎速度×K×平均適性倍率；五地形平均）', '', '| 野靈 | 基礎速度 | 耐力 | 平均 A | 理論平均 m/s | 最佳地形 m/s |', '|---|---|---|---|---|---|']
    st = run({'exp': 'static'})
    for c in st['rows']:
        md.append('| %s | %d | %d | %.2f | %.2f | %.2f |' % (c['name'], c['speed'], c['stamina'], c['meanA'], c['mean'], c['best']))
    out = '\n'.join(md)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, 'w', encoding='utf8').write(out + '\n')
    print(out)

if __name__ == '__main__':
    main()
