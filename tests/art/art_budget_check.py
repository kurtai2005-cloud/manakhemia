#!/usr/bin/env python3
"""art_budget_check.py — 貼圖預算自動檢查（《微光小圃》加深方案：atlas ≤1024×1024、同時載入貼圖預算 ≤16MB）
掃描 art 目錄：讀 PNG IHDR（唔需要 Pillow）、檔案大小、解碼後 RGBA 記憶體（w*h*4，可選 mipmap ×1.33）、atlas JSON frame 越界／重疊／padding。
用法：python3 art_budget_check.py <art 目錄> [--budget-mb 16] [--max-atlas 1024] [--mode disk|gpu|both] [--pet tuanrong] [--md out/art_budget.md] [--json out/art_budget.json]
退出碼：0＝全 PASS；1＝有 FAIL（CI 可用）。
定義（提案；plan 只寫「貼圖預算 ≤16MB」未講明係磁碟抑或 GPU）：
  - 「運行時貼圖」＝ 排除 *preview* / *concept* / *contact_sheet* / *palette* / frames/ 單幀（打包後只載 atlas；可用 --include-frames 計入）／motion 原始序列 ... 以 --exclude 自訂。
  - 分 pet 計：同時只載入當前寵物（plan 風險節）→ 以 --pet 指定資料夾關鍵字，或預設以第二層資料夾名分組。
  - GPU 記憶體 ＝ Σ w×h×4（RGBA8888）；磁碟＝ PNG 檔案大小。兩者都 ≤ budget 先算 PASS。
  - 限制：非 2 次冪 atlas 在部分舊 GPU／WebGL1 會被補到 2 次冪（記憶體 ↑）→ WARN。
"""
import sys, os, struct, json, argparse, re, collections, fnmatch

def png_size(p):
    with open(p, 'rb') as f:
        h = f.read(33)
    if h[:8] != b'\x89PNG\r\n\x1a\n' or h[12:16] != b'IHDR': return None
    w, hh = struct.unpack('>II', h[16:24]); ct = h[25]
    return w, hh, ct

def npot(n): return n & (n - 1) != 0
def pot_up(n):
    p = 1
    while p < n: p <<= 1
    return p

DEFAULT_EXCLUDE = ['*preview*', '*concept*', '*contact_sheet*', '*palette*', '*similarity*']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root'); ap.add_argument('--budget-mb', type=float, default=16.0); ap.add_argument('--max-atlas', type=int, default=1024)
    ap.add_argument('--mode', default='both'); ap.add_argument('--exclude', action='append', default=None); ap.add_argument('--include-frames', action='store_true')
    ap.add_argument('--mipmap', action='store_true'); ap.add_argument('--md'); ap.add_argument('--json'); ap.add_argument('--pet', default=None)
    a = ap.parse_args()
    excl = a.exclude if a.exclude is not None else DEFAULT_EXCLUDE
    files = []
    for dp, dn, fn in os.walk(a.root):
        if '/.git' in dp or '/node_modules' in dp: continue
        for f in fn:
            if f.lower().endswith('.png'): files.append(os.path.join(dp, f))
    rows = []; fails = []; warns = []
    for p in sorted(files):
        rel = os.path.relpath(p, a.root); sz = os.path.getsize(p); info = png_size(p)
        base = os.path.basename(p).lower()
        skip_reason = None
        if any(fnmatch.fnmatch(base, e.lower()) or fnmatch.fnmatch(rel.lower(), e.lower()) for e in excl): skip_reason = '非運行時（preview/concept…）'
        elif ('/frames/' in '/' + rel.replace('\\', '/') or '/motion/' in '/' + rel.replace('\\', '/')) and not a.include_frames and not re.search(r'atlas', base): skip_reason = '單幀／來源序列（打包入 atlas）'
        elif re.search(r'_sheet\.png$', base) and not a.include_frames: skip_reason = '橫排 sheet（來源／預覽；打包只載 atlas）'
        if info is None: rows.append(dict(rel=rel, bytes=sz, w=0, h=0, skip='非有效 PNG')); fails.append(f'{rel}: 非有效 PNG'); continue
        w, h, ct = info
        rows.append(dict(rel=rel, bytes=sz, w=w, h=h, gpu=w * h * 4 * (1.333 if a.mipmap else 1), skip=skip_reason, color_type=ct))
    run = [r for r in rows if not r.get('skip')]
    # 分組：第二層資料夾（art/<cat>/<name>）；用 --pet 過濾
    def group(r):
        parts = r['rel'].replace('\\', '/').split('/')
        for k in parts:
            if a.pet and a.pet in k: return a.pet
        return '/'.join(parts[:-1][:3]) or '.'
    groups = collections.defaultdict(list)
    for r in run:
        if a.pet and a.pet not in r['rel']: continue
        groups[group(r)].append(r)
    B = a.budget_mb * 1024 * 1024
    out = ['# 貼圖預算檢查結果（art_budget_check.py）\n', f'> 目錄：`{a.root}`；預算 {a.budget_mb:g} MB（模式 {a.mode}）；atlas 上限 {a.max_atlas}×{a.max_atlas}；mipmap={"on" if a.mipmap else "off"}\n']
    out.append('## 1. 尺寸檢查（運行時貼圖）\n'); out.append('| 檔案 | 尺寸 | 磁碟 | 解碼 RGBA | 判定 |'); out.append('|---|---|---|---|---|')
    for r in run:
        if a.pet and a.pet not in r['rel']: continue
        v = []
        if r['w'] > a.max_atlas or r['h'] > a.max_atlas: v.append('FAIL 超出 %d' % a.max_atlas); fails.append(f"{r['rel']}: {r['w']}×{r['h']} 超出 {a.max_atlas}×{a.max_atlas}")
        if (npot(r['w']) or npot(r['h'])) and re.search(r'atlas', r['rel']): v.append('WARN 非 2 次冪（補至 %d×%d ＝ %.1f MB）' % (pot_up(r['w']), pot_up(r['h']), pot_up(r['w']) * pot_up(r['h']) * 4 / 1048576)); warns.append(f"{r['rel']}: atlas 非 2 次冪 {r['w']}×{r['h']}")
        out.append(f"| `{r['rel']}` | {r['w']}×{r['h']} | {r['bytes']/1024:.1f} KB | {r['gpu']/1048576:.2f} MB | {' '.join(v) or 'PASS'} |")
    out.append('\n## 2. 每組（寵物）運行時貼圖總量\n'); out.append('| 組 | 張數 | 磁碟 | GPU（解碼） | 對預算 | 判定 |'); out.append('|---|---|---|---|---|---|')
    for g, rs in groups.items():
        d = sum(r['bytes'] for r in rs); gp = sum(r['gpu'] for r in rs); v = []
        if a.mode in ('disk', 'both') and d > B: v.append('FAIL 磁碟超預算'); fails.append(f'{g}: 磁碟 {d/1048576:.1f} MB > {a.budget_mb:g}')
        if a.mode in ('gpu', 'both') and gp > B: v.append('FAIL GPU 超預算'); fails.append(f'{g}: GPU {gp/1048576:.1f} MB > {a.budget_mb:g}')
        out.append(f"| {g} | {len(rs)} | {d/1048576:.2f} MB ({100*d/B:.0f}%) | {gp/1048576:.2f} MB ({100*gp/B:.0f}%) | {a.budget_mb:g} MB | {' '.join(v) or 'PASS'} |")
    # atlas JSON
    jsons = [os.path.join(dp, f) for dp, dn, fn in os.walk(a.root) for f in fn if f.endswith('.json') and 'atlas' in f.lower()]
    out.append('\n## 3. atlas JSON 檢查（frame 越界／重疊／padding）\n')
    if not jsons: out.append('（搵唔到 *atlas*.json）')
    for jp in sorted(jsons):
        rel = os.path.relpath(jp, a.root)
        try: d = json.load(open(jp))
        except Exception as e: out.append(f'- `{rel}`：JSON 無法解析 {e}'); fails.append(rel + ' JSON 損毀'); continue
        fr = d.get('frames', {}); meta = d.get('meta', {}); img = meta.get('image'); size = meta.get('size') or {}
        ip = os.path.join(os.path.dirname(jp), img) if img else jp.replace('.json', '.png')
        inf = png_size(ip) if os.path.exists(ip) else None
        W, H = (inf[0], inf[1]) if inf else (size.get('w', 0), size.get('h', 0))
        items = list(fr.items()) if isinstance(fr, dict) else [(x.get('filename'), x) for x in fr]
        oob = [n for n, f in items if f['frame']['x'] < 0 or f['frame']['y'] < 0 or f['frame']['x'] + f['frame']['w'] > W or f['frame']['y'] + f['frame']['h'] > H]
        rects = [(n, f['frame']['x'], f['frame']['y'], f['frame']['x'] + f['frame']['w'], f['frame']['y'] + f['frame']['h']) for n, f in items]
        ov = []; mingap = 1e9
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                A, Bb = rects[i], rects[j]
                if A[1] < Bb[3] and Bb[1] < A[3] and A[2] < Bb[4] and Bb[2] < A[4]: ov.append((A[0], Bb[0]))
                else:
                    dx = max(Bb[1] - A[3], A[1] - Bb[3], 0); dy = max(Bb[2] - A[4], A[2] - Bb[4], 0)
                    if dx == 0 or dy == 0: mingap = min(mingap, max(dx, dy))
        ws = {(f['frame']['w'], f['frame']['h']) for _, f in items}
        used = sum(f['frame']['w'] * f['frame']['h'] for _, f in items); fill = used / (W * H) if W * H else 0
        st = []
        if oob: st.append(f'FAIL {len(oob)} 個 frame 越界'); fails.append(f'{rel}: frame 越界 {oob[:3]}')
        if ov: st.append(f'FAIL {len(ov)} 對 frame 重疊'); fails.append(f'{rel}: frame 重疊 {ov[:2]}')
        if mingap < 2 and mingap != 1e9: st.append(f'WARN 最小間距 {mingap}px（<2px 縮放／過濾會滲色；建議 extrude 1px＋padding 2px）'); warns.append(f'{rel}: padding {mingap}px')
        if W > a.max_atlas or H > a.max_atlas: st.append(f'FAIL atlas {W}×{H} 超出 {a.max_atlas}'); fails.append(f'{rel}: atlas {W}×{H} 超出 {a.max_atlas}×{a.max_atlas}（對應 PNG）')
        out.append(f"- `{rel}` → 圖 {W}×{H}，{len(items)} frames（尺寸種類 {sorted(ws)}），填充率 {100*fill:.1f}%，最小間距 {'-' if mingap == 1e9 else mingap}px：{' ; '.join(st) or 'PASS'}")
        if fill < 0.25 and W * H > 256 * 256: out.append(f'  - 填充率 {100*fill:.0f}% 偏低：atlas 大部分係空白 → 記憶體浪費（{W*H*4/1048576:.1f} MB 只用 {used*4/1048576:.2f} MB）；建議縮細或拆分。'); warns.append(f'{rel}: 填充率 {100*fill:.0f}%')
    # 低優先：被排除嘅大檔
    big = sorted([r for r in rows if r.get('skip') and r['bytes'] > 200 * 1024], key=lambda r: -r['bytes'])[:5]
    if big: out.append('\n## 4. 被排除但偏大嘅檔案（確認唔會打包入 app）\n'); out += [f"- `{r['rel']}` {r['bytes']/1024:.0f} KB（{r['skip']}）" for r in big]
    out.append('\n## 判定\n'); out.append(('**FAIL**（%d 項）：\n' % len(fails) + '\n'.join('- ' + f for f in fails)) if fails else '**PASS**'); 
    if warns: out.append('\nWARN：\n' + '\n'.join('- ' + w for w in warns))
    txt = '\n'.join(out); print(txt)
    if a.md: os.makedirs(os.path.dirname(a.md) or '.', exist_ok=True); open(a.md, 'w').write(txt + '\n')
    if a.json: os.makedirs(os.path.dirname(a.json) or '.', exist_ok=True); json.dump(dict(fails=fails, warns=warns, rows=rows), open(a.json, 'w'), indent=1, ensure_ascii=False)
    sys.exit(1 if fails else 0)
main()
