#!/usr/bin/env python3
"""單檔 build：python3 tools/build-single.py → dist/glimmer-live-s1.html
   inline 所有 src/*.js；art/**（png/json）＋audio/**（ogg）base64 內嵌；
   前置 shim 攔截 fetch()／Image.src 相對路徑 → 內嵌資產（雙擊 file:// 即開，手機可用）。唔改 src。"""
import base64, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'dist', 'glimmer-live-s1.html')
MIME = {'.png': 'image/png', '.json': 'application/json', '.ogg': 'audio/ogg'}
assets = {}
for d in ('art', 'audio'):
    for dp, _, fs in os.walk(os.path.join(ROOT, d)):
        for f in sorted(fs):
            ext = os.path.splitext(f)[1]
            if ext not in MIME: continue
            p = os.path.join(dp, f); rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
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
print('wrote', OUT, os.path.getsize(OUT), 'bytes,', len(assets), 'assets')
