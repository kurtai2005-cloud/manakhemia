#!/usr/bin/env python3
"""單檔 build：python3 tools/build-single.py → dist/glimmer-live-s1.html
   inline 所有 src/*.js；art/**（png/json）＋audio/**（ogg）base64 內嵌；
   前置 shim 攔截 fetch()／Image.src 相對路徑 → 內嵌資產（雙擊 file:// 即開，手機可用）。唔改 src。
   V3.1：art/v3/**.png → 無損 webp（exact，像素一樣；快取 /workspace/hdbuild/webp3 或 $GLIMMER_WEBP_CACHE）＋同內容去重；
   6d QA P1：**預設外置**（＝--ext <輸出 html 所在資料夾>）：art/v3（＋6c／6d）圖唔內嵌，寫去 DIR/art/v3/_x/<sha1>.webp，shim 將原路徑改指嗰個相對 URL
   （APK：Capacitor 由 assets/public 供檔；網頁：同 html 放埋一齊用 http 開）。--ext DIR 指定第二個資料夾。
   --inline：舊式全內嵌單檔（file:// 雙擊即開；檔大好多）。
   6c：art/breakthrough/6c/**.png 同 art/v3 一樣處理（webp／去重／--ext 外置）。6d：art/breakthrough/6d/**.png 一樣。#89：art/garden3d/**.png 一樣（3D 花園 H1）。
   預設半透明圖照用 PNG（瀏覽器解碼逐 bit 一樣）；--webp-all 全轉 webp（細啲但半透明差 ≤3/255）。"""
import base64, hashlib, json, os, re, sys
from multiprocessing import Pool
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARGS = sys.argv[1:]; EXT = None
EXACT_ALPHA = '--webp-all' not in ARGS   # V3.1 預設：半透明（0<α<255）圖保留 PNG（Chrome webp 預乘取整同 PNG 會差 1–3/255）；--webp-all＝全部 webp（細 ~5.6MB，但唔係逐 bit 一樣）
ARGS = [a for a in ARGS if a != '--webp-all']
INLINE = '--inline' in ARGS; ARGS = [a for a in ARGS if a != '--inline']
if '--ext' in ARGS: j = ARGS.index('--ext'); EXT = ARGS[j + 1]; del ARGS[j:j + 2]
if INLINE and EXT: sys.exit('--inline 同 --ext 唔可以一齊用')
OUT = ARGS[0] if ARGS else os.path.join(ROOT, 'dist', 'glimmer-live-s1.html')   # 合併版：python3 tools/build-single.py dist/glimmer-combo.html
if not INLINE and not EXT: EXT = os.path.dirname(os.path.abspath(OUT))   # 6d QA P1：預設外置（同 html 同一個資料夾）；全內嵌要明講 --inline
MIME = {'.webp': 'image/webp', '.png': 'image/png', '.json': 'application/json', '.ogg': 'audio/ogg', '.ttf': 'font/ttf', '.otf': 'font/otf'}   # V3.1b：V3 字 subset otf（6c：GenWanMin2 TC，OFL）
# 5a.2：唔打包運行時冇用嘅資產（檔仍然留喺 repo 畀測試）：成個 reskin_4b/（src 冇路徑）、FP8／FP10（v2 只用 FP12）
SKIP_DIRS = ('reskin_4b',); SKIP_FILES = ('fp8-subset.ttf', 'fp10-subset.ttf')
# 5b.1：遊美 5b 示意圖／排版稿（runtime 冇載入；檔留喺 repo 畀 long5b.test 對數）
_B5 = 'art/series2_long/5b/ui/'
SKIP_REL = set([_B5 + n + '@3x.png' for n in ('diary_page_example', 'job_card_example', 'job_card_capped', 'toast_return', 'icon_job_lv')]
               + [_B5 + 'seg_%s_%s@3x.png' % (a, b) for a in ('expedition', 'job', 'rest') for b in ('on', 'off', 'locked')] + [_B5 + 'layout.json'])
# 5c.1：遊美 5c 示意圖／未用 UI（~268KB；runtime 只用 chip_trick_*／icon_fast／icon_inherit／swatch_*；檔留喺 repo 畀 long5c.test 對數）
_C5 = 'art/series2_long/5c/ui/'
SKIP_REL |= set([_C5 + n + '@3x.png' for n in ('parent_card_A3', 'parent_card_evo_still_moon', 'inherit_preview_bar', 'icon_trick', 'icon_pattern', 'pill_fast_on', 'pill_fast_tr', 'pill_fast_locked')] + [_C5 + 'layout.json'])
# 6a.1：遊美 6a 表情 runtime 只用 1x（per_pet／faces6a.json）；@3x 同預設 face_*（只啱 evo_still_radiant）唔入單檔
_F6 = 'art/breakthrough/6a/'
SKIP_REL |= set([_F6 + n for n in ('face_smug.png', 'face_pout.png', 'face_smug@3x.png', 'face_pout@3x.png')])
# 6b.1：遊美散步美術 runtime 用 1x（walk_bg、per_pet walk、deco）＋ rail ic_walk@3x；其餘 @3x／預覽唔入單檔
_W6 = 'art/breakthrough/6b/'
SKIP_REL |= set([_W6 + n for n in ('walk_bg@3x.png', 'ic_walk@1x.png', 'preview_6b_3x.png')])
SKIP_RX = re.compile(r'^art/breakthrough/6a/per_pet/[^/]+/face_(smug|pout)@3x\.png$|^art/breakthrough/6b/(per_pet/[^/]+/walk|deco/deco_[a-z0-9_]+)@3x\.png$')
assets = {}; skipped = [0, 0]; v3png = []; extfont = []; extlic = []
for d in ('art', 'audio'):
    for dp, dns, fs in os.walk(os.path.join(ROOT, d)):
        for s in [x for x in dns if x in SKIP_DIRS]:
            for sp, _, sf in os.walk(os.path.join(dp, s)):
                for f in sf:
                    if os.path.splitext(f)[1] in MIME: skipped[0] += 1; skipped[1] += os.path.getsize(os.path.join(sp, f))
        dns[:] = sorted(x for x in dns if x not in SKIP_DIRS)
        for f in sorted(fs):
            ext = os.path.splitext(f)[1]
            if f.startswith('OFL') and ext == '.txt':   # 6c：字型授權（OFL 1.1）一定跟埋：--ext 抄去原路徑；單檔版內嵌做 text/plain 資產
                p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
                if EXT: import shutil; fp = os.path.join(EXT, rel); os.makedirs(os.path.dirname(fp), exist_ok=True); shutil.copyfile(p, fp); extlic.append(rel)
                else: assets[rel] = ['text/plain', base64.b64encode(open(p, 'rb').read()).decode()]
                continue
            if ext not in MIME: continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
            if f in SKIP_FILES or rel in SKIP_REL or SKIP_RX.match(rel): skipped[0] += 1; skipped[1] += os.path.getsize(p); continue
            if (rel.startswith('art/v3/') or rel.startswith('art/breakthrough/6c/') or rel.startswith('art/breakthrough/6d/') or rel.startswith('art/garden3d/')) and ext == '.png': v3png.append((rel, p)); continue
            if EXT and ext == '.otf':   # V3.1b：APK 外置字體（原路徑；shim 唔攔 → Capacitor 供檔）＋ OFL 授權檔
                import shutil; fp = os.path.join(EXT, rel); os.makedirs(os.path.dirname(fp), exist_ok=True); shutil.copyfile(p, fp); extfont.append(rel)
                continue
            assets[rel] = [MIME[ext], base64.b64encode(open(p, 'rb').read()).decode()]
# V3.1：V3 png → 無損 webp（exact＝透明位 RGB 都保留）；按 PNG sha1 快取
CACHE = os.environ.get('GLIMMER_WEBP_CACHE', '/workspace/hdbuild/webp3')
def to_webp(p):
    raw = open(p, 'rb').read(); h = hashlib.sha1(raw).hexdigest(); c = os.path.join(CACHE, h + '.webp')
    if not os.path.exists(c):
        from PIL import Image; import io
        im = Image.open(io.BytesIO(raw)); im.load(); b = io.BytesIO(); im.save(b, 'WEBP', lossless=True, quality=100, method=6, exact=True)
        chk = Image.open(io.BytesIO(b.getvalue())).convert(im.mode)
        assert chk.size == im.size and chk.tobytes() == im.tobytes(), 'webp not exact: ' + p
        out = b.getvalue() if len(b.getvalue()) < len(raw) else None
        open(c + '.tmp', 'wb').write(out if out else b'PNG'); os.replace(c + '.tmp', c)
    w = open(c, 'rb').read()
    if EXACT_ALPHA and w != b'PNG':
        from PIL import Image; import io
        im = Image.open(io.BytesIO(raw))
        if im.mode in ('RGBA', 'LA', 'P') and sum(im.convert('RGBA').getchannel('A').histogram()[1:255]): w = b'PNG'
    return h, (w, 'image/webp') if w != b'PNG' else (raw, 'image/png')
os.makedirs(CACHE, exist_ok=True)
with Pool(max(1, (os.cpu_count() or 2) - 2)) as pool: conv = pool.map(to_webp, [p for _, p in v3png])
EXTMAP = {}; canon = {}; v3st = [0, 0, 0]   # 原 png bytes、輸出 bytes、去重數
for (rel, p), (h, (data, mime)) in zip(v3png, conv):
    v3st[0] += os.path.getsize(p)
    if EXT:
        name = 'art/v3/_x/' + h + ('.webp' if mime == 'image/webp' else '.png'); EXTMAP[rel] = name; fp = os.path.join(EXT, name)
        if os.path.exists(fp): v3st[2] += 1; continue
        os.makedirs(os.path.dirname(fp), exist_ok=True); open(fp, 'wb').write(data); v3st[1] += len(data)
    else:
        if h in canon: assets[rel] = canon[h]; v3st[2] += 1; continue   # 去重：JSON 存別名字串
        canon[h] = rel; assets[rel] = [mime, base64.b64encode(data).decode()]; v3st[1] += len(data)
shim = r"""<script>/* 單檔 build：內嵌資產解析器（fetch／Image） */
(function () {
  var A = window.__GLIMMER_ASSETS = %s; window.__GLIMMER_SINGLE = true;
  var X = window.__GLIMMER_EXT = %s;   /* V3.1：APK 外置檔（原路徑 → 相對 URL） */
  for (var a in A) if (typeof A[a] === 'string') A[a] = A[A[a]];   /* V3.1：去重別名 */
  var keys = Object.keys(A).concat(Object.keys(X));
  function hit(u) { if (u == null) return null; u = String(u); if (/^(data|blob):/.test(u)) return null;
    try { u = decodeURIComponent(new URL(u, location.href).pathname); } catch (e) { }
    u = u.replace(/[?#].*$/, ''); for (var i = 0; i < keys.length; i++) { var k = keys[i]; if (u === k || u.slice(-k.length - 1) === '/' + k) return k; } return null; }
  function dataOf(k) { return X[k] || ('data:' + A[k][0] + ';base64,' + A[k][1]); }
  function bytes(k) { var s = atob(A[k][1]), n = s.length, b = new Uint8Array(n); for (var i = 0; i < n; i++) b[i] = s.charCodeAt(i); return b; }
  var of = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function (u, o) { var k = hit(typeof u === 'string' ? u : (u && u.url)); if (k && X[k]) return of(X[k], o); if (k) return Promise.resolve(new Response(new Blob([bytes(k)], { type: A[k][0] }), { status: 200, headers: { 'Content-Type': A[k][0] } })); return of ? of(u, o) : Promise.reject(new Error('no fetch')); };
  var d = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
  Object.defineProperty(HTMLImageElement.prototype, 'src', { configurable: true, enumerable: d.enumerable, get: function () { return d.get.call(this); },
    set: function (v) { var k = hit(v); d.set.call(this, k ? dataOf(k) : v); } });
  /* innerHTML 嘅 <img src>／inline style url(...) 唔經 setter → MutationObserver 補換（4a 細佬卡／托盤／rail icon） */
  function fix(el) { if (!el || el.nodeType !== 1) return;
    if (el.tagName === 'IMG') { var v = el.getAttribute('src'), k = hit(v); if (k) d.set.call(el, dataOf(k)); }
    var st = el.getAttribute('style'); if (st && st.indexOf('url(') >= 0) { var ch = false, ns = st.replace(/url\((['"]?)([^)'"]+)\1\)/g, function (m, q, u) { var k = hit(u); if (!k) return m; ch = true; return 'url("' + dataOf(k) + '")'; }); if (ch) el.setAttribute('style', ns); } }
  function scan(n) { if (!n || n.nodeType !== 1) return; fix(n); if (n.querySelectorAll) { var l = n.querySelectorAll('img,[style*="url("]'); for (var i = 0; i < l.length; i++) fix(l[i]); } }
  /* V3.1b：innerHTML／insertAdjacentHTML 嘅 <img src>／url() 喺解析前改寫（MutationObserver 太遲：瀏覽器已發出請求 → http／APK 會出 404 log） */
  function rw(h) { if (typeof h !== 'string' || (h.indexOf('src=') < 0 && h.indexOf('url(') < 0)) return h;
    return h.replace(/(\bsrc=)(["'])([^"']+)\2/g, function (m, a, q, u) { var k = hit(u); return k ? a + q + dataOf(k) + q : m; })
            .replace(/url\((&quot;|['"]?)([^)'"&]+)\1\)/g, function (m, q, u) { var k = hit(u); return k ? 'url(' + q + dataOf(k) + q + ')' : m; }); }
  var ih = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
  Object.defineProperty(Element.prototype, 'innerHTML', { configurable: true, enumerable: ih.enumerable, get: function () { return ih.get.call(this); }, set: function (v) { ih.set.call(this, rw(v)); } });
  var iah = Element.prototype.insertAdjacentHTML; Element.prototype.insertAdjacentHTML = function (pos, h) { return iah.call(this, pos, rw(h)); };
  new MutationObserver(function (ms) { for (var i = 0; i < ms.length; i++) { var m = ms[i]; if (m.type === 'attributes') fix(m.target); else for (var j = 0; j < m.addedNodes.length; j++) scan(m.addedNodes[j]); } })
    .observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['src', 'style'] });
})();
</script>""" % (json.dumps(assets, separators=(',', ':')), json.dumps(EXTMAP, separators=(',', ':')))
html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
def inline(m):
    js = open(os.path.join(ROOT, m.group(1)), encoding='utf-8').read().replace('</script', '<\\/script')
    return '<script>/* ' + m.group(1) + ' */\n' + js + '\n</script>'
first = html.index('<script src=')
html = html[:first] + shim + '\n' + html[first:]
html = re.sub(r'<script src="([^"]+\.js)"></script>', inline, html)
assert '<script src=' not in html
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(html)
print('wrote', OUT, os.path.getsize(OUT), 'bytes,', len(assets), 'assets', '| skipped', skipped[0], 'files', skipped[1], 'raw bytes', '| v3 png', len(v3png), v3st[0], '→', v3st[1], 'bytes, dedup', v3st[2], ('| ext ' + EXT + ' ' + str(len(EXTMAP)) + ' img + ' + str(len(extfont)) + ' font + ' + str(len(extlic)) + ' OFL') if EXT else '| inline')
