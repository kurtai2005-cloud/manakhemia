#!/usr/bin/env python3
"""單檔 build：python3 tools/build-single.py → dist/glimmer-live-s1.html
   inline 所有 src/*.js；art/**（png/json）＋audio/**（ogg）base64 內嵌；
   前置 shim 攔截 fetch()／Image.src 相對路徑 → 內嵌資產（雙擊 file:// 即開，手機可用）。唔改 src。"""
import base64, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dist', 'glimmer-live-s1.html')   # 合併版：python3 tools/build-single.py dist/glimmer-combo.html
MIME = {'.png': 'image/png', '.json': 'application/json', '.ogg': 'audio/ogg', '.ttf': 'font/ttf'}
# 5a.2：唔打包運行時冇用嘅資產（檔仍然留喺 repo 畀測試）：成個 reskin_4b/（src 冇路徑）、FP8／FP10（v2 只用 FP12）
SKIP_DIRS = ('reskin_4b',); SKIP_FILES = ('fp8-subset.ttf', 'fp10-subset.ttf')
# 5b.1：遊美 5b 示意圖／排版稿（runtime 冇載入；檔留喺 repo 畀 long5b.test 對數）
_B5 = 'art/series2_long/5b/ui/'
SKIP_REL = set([_B5 + n + '@3x.png' for n in ('diary_page_example', 'job_card_example', 'job_card_capped', 'toast_return', 'icon_job_lv')]
               + [_B5 + 'seg_%s_%s@3x.png' % (a, b) for a in ('expedition', 'job', 'rest') for b in ('on', 'off', 'locked')] + [_B5 + 'layout.json'])
# 5c.1：遊美 5c 示意圖／未用 UI（~268KB；runtime 只用 chip_trick_*／icon_fast／icon_inherit／swatch_*；檔留喺 repo 畀 long5c.test 對數）
_C5 = 'art/series2_long/5c/ui/'
SKIP_REL |= set([_C5 + n + '@3x.png' for n in ('parent_card_A3', 'parent_card_evo_still_moon', 'inherit_preview_bar', 'icon_trick', 'icon_pattern', 'pill_fast_on', 'pill_fast_tr', 'pill_fast_locked')] + [_C5 + 'layout.json'])
assets = {}; skipped = [0, 0]
for d in ('art', 'audio'):
    for dp, dns, fs in os.walk(os.path.join(ROOT, d)):
        for s in [x for x in dns if x in SKIP_DIRS]:
            for sp, _, sf in os.walk(os.path.join(dp, s)):
                for f in sf:
                    if os.path.splitext(f)[1] in MIME: skipped[0] += 1; skipped[1] += os.path.getsize(os.path.join(sp, f))
        dns[:] = sorted(x for x in dns if x not in SKIP_DIRS)
        for f in sorted(fs):
            ext = os.path.splitext(f)[1]
            if ext not in MIME: continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
            if f in SKIP_FILES or rel in SKIP_REL: skipped[0] += 1; skipped[1] += os.path.getsize(p); continue
            assets[rel] = [MIME[ext], base64.b64encode(open(p, 'rb').read()).decode()]
shim = r"""<script>/* 單檔 build：內嵌資產解析器（fetch／Image） */
(function () {
  var A = window.__GLIMMER_ASSETS = %s; window.__GLIMMER_SINGLE = true;
  var keys = Object.keys(A);
  function hit(u) { if (u == null) return null; u = String(u); if (/^(data|blob):/.test(u)) return null;
    try { u = decodeURIComponent(new URL(u, location.href).pathname); } catch (e) { }
    u = u.replace(/[?#].*$/, ''); for (var i = 0; i < keys.length; i++) { var k = keys[i]; if (u === k || u.slice(-k.length - 1) === '/' + k) return k; } return null; }
  function bytes(k) { var s = atob(A[k][1]), n = s.length, b = new Uint8Array(n); for (var i = 0; i < n; i++) b[i] = s.charCodeAt(i); return b; }
  var of = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function (u, o) { var k = hit(typeof u === 'string' ? u : (u && u.url)); if (k) return Promise.resolve(new Response(new Blob([bytes(k)], { type: A[k][0] }), { status: 200, headers: { 'Content-Type': A[k][0] } })); return of ? of(u, o) : Promise.reject(new Error('no fetch')); };
  var d = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
  Object.defineProperty(HTMLImageElement.prototype, 'src', { configurable: true, enumerable: d.enumerable, get: function () { return d.get.call(this); },
    set: function (v) { var k = hit(v); d.set.call(this, k ? 'data:' + A[k][0] + ';base64,' + A[k][1] : v); } });
  /* innerHTML 嘅 <img src>／inline style url(...) 唔經 setter → MutationObserver 補換（4a 細佬卡／托盤／rail icon） */
  function dataOf(k) { return 'data:' + A[k][0] + ';base64,' + A[k][1]; }
  function fix(el) { if (!el || el.nodeType !== 1) return;
    if (el.tagName === 'IMG') { var v = el.getAttribute('src'), k = hit(v); if (k) d.set.call(el, dataOf(k)); }
    var st = el.getAttribute('style'); if (st && st.indexOf('url(') >= 0) { var ch = false, ns = st.replace(/url\((['"]?)([^)'"]+)\1\)/g, function (m, q, u) { var k = hit(u); if (!k) return m; ch = true; return 'url("' + dataOf(k) + '")'; }); if (ch) el.setAttribute('style', ns); } }
  function scan(n) { if (!n || n.nodeType !== 1) return; fix(n); if (n.querySelectorAll) { var l = n.querySelectorAll('img,[style*="url("]'); for (var i = 0; i < l.length; i++) fix(l[i]); } }
  new MutationObserver(function (ms) { for (var i = 0; i < ms.length; i++) { var m = ms[i]; if (m.type === 'attributes') fix(m.target); else for (var j = 0; j < m.addedNodes.length; j++) scan(m.addedNodes[j]); } })
    .observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['src', 'style'] });
})();
</script>""" % json.dumps(assets, separators=(',', ':'))
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
print('wrote', OUT, os.path.getsize(OUT), 'bytes,', len(assets), 'assets', '| skipped', skipped[0], 'files', skipped[1], 'raw bytes')
