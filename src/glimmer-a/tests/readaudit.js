/* 5a.1 字清晰度審查（共用）：喺頁面入面搵所有可見文字元素 → 有效字號（360dp 實際 CSS px）、字型、顏色／描邊；
   再用「文字透明」截圖量背景亮度 → WCAG 對比。audit(page, rootSel) 回 { items, bad } */
const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
async function collect(page, rootSel) {
  return page.evaluate((rootSel) => {
    const roots = rootSel ? [...document.querySelectorAll(rootSel)] : [document.body], out = [], seen = new Set();
    const rgb = (s) => { const m = String(s).match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return p.length >= 3 ? [p[0], p[1], p[2], p.length > 3 ? p[3] : 1] : null; };
    const shadowCol = (ts) => { if (!ts || ts === 'none') return null; const m = ts.match(/rgba?\([^)]+\)/); return m ? rgb(m[0]) : null; };
    const ui = document.getElementById('ui'), uiR = ui ? ui.getBoundingClientRect() : null, k = ui && ui.offsetWidth ? uiR.width / ui.offsetWidth : 1;
    for (const R of roots) { const w = document.createTreeWalker(R, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { const t = n.nodeValue.replace(/\s+/g, ''); if (!t) continue; const el = n.parentElement; if (!el || seen.has(el)) continue; seen.add(el);
        const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue; const rg = document.createRange(); rg.selectNodeContents(n); const rr = rg.getBoundingClientRect(); if (rr.width < 2 || rr.height < 2) continue;
        if (rr.bottom < 0 || rr.top > innerHeight || rr.right < 0 || rr.left > innerWidth) continue;
        let a = el, op = 1; while (a && a !== document.documentElement) { const c = getComputedStyle(a); op *= +c.opacity; if (c.display === 'none' || c.visibility === 'hidden') { op = 0; break; } a = a.parentElement; } if (op < 0.05) continue;
        // 只計最上面嗰層（俾蓋住嘅唔計）
        const cx = Math.min(innerWidth - 1, Math.max(0, rr.left + rr.width / 2)), cy = Math.min(innerHeight - 1, Math.max(0, rr.top + rr.height / 2)), top = document.elementFromPoint(cx, cy); if (top && !(el === top || el.contains(top) || top.contains(el))) continue;
        const fs = parseFloat(cs.fontSize), eb = el.getBoundingClientRect(), sc = eb.width && el.offsetWidth ? eb.width / el.offsetWidth : k;
        out.push({ t: t.slice(0, 24), tid: el.dataset.testid || el.id || el.className && String(el.className).slice(0, 30) || el.tagName, fs, eff: +(fs * sc).toFixed(2), sc: +sc.toFixed(3), fam: cs.fontFamily.split(',')[0].replace(/"/g, ''), col: rgb(cs.color), ol: shadowCol(cs.textShadow), smooth: cs.webkitFontSmoothing || '', op: +op.toFixed(2), r: [rr.left, rr.top, rr.width, rr.height].map(v => Math.round(v)), sys: el.closest('.sysf') ? 1 : 0, fbk: el.dataset.fbk || '' });
      } }
    return out;
  }, rootSel);
}
async function bgSample(page, items) {
  // 5a.2：inline !important 收字（樣式表 !important 高 specificity 都蓋得到）
  await page.evaluate(() => document.querySelectorAll('body *').forEach(e => { e.dataset.raHide = e.getAttribute('style') || ''; for (const [k, v] of [['color', 'transparent'], ['text-shadow', 'none'], ['-webkit-text-stroke', '0'], ['caret-color', 'transparent']]) e.style.setProperty(k, v, 'important'); }));
  await page.waitForTimeout(60); const buf = await page.screenshot({ type: 'png' });
  await page.evaluate(() => document.querySelectorAll('body [data-ra-hide]').forEach(e => { if (e.dataset.raHide) e.setAttribute('style', e.dataset.raHide); else e.removeAttribute('style'); delete e.dataset.raHide; }));
  return page.evaluate(async ([b64, items]) => {
    const im = new Image(); await new Promise(r => { im.onload = r; im.src = 'data:image/png;base64,' + b64; }); const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const g = c.getContext('2d'); g.drawImage(im, 0, 0);
    const d = devicePixelRatio; return items.map(it => { const [x, y, w, h] = it.r, X = Math.max(0, Math.round(x * d)), Y = Math.max(0, Math.round(y * d)), W = Math.max(1, Math.min(c.width - X, Math.round(w * d))), H = Math.max(1, Math.min(c.height - Y, Math.round(h * d)));
      const px = g.getImageData(X, Y, W, H).data; const L = []; const s = [0, 0, 0]; let n = 0; const step = Math.max(1, Math.floor(Math.sqrt(W * H / 900)));
      for (let j = 0; j < H; j += step) for (let i = 0; i < W; i += step) { const o = (j * W + i) * 4; L.push([px[o], px[o + 1], px[o + 2]]); s[0] += px[o]; s[1] += px[o + 1]; s[2] += px[o + 2]; n++; }
      return { mean: s.map(v => Math.round(v / n)), px: L }; });
  }, [buf.toString('base64'), items]);
}
async function audit(page, rootSel, opt) {
  opt = opt || {}; const minEff = opt.minEff || 14, minCr = opt.minCr || 4.5;
  const items = await collect(page, rootSel); if (!items.length) return { items, bad: [] }; const bg = await bgSample(page, items);
  items.forEach((it, i) => { const b = bg[i], col = it.col || [0, 0, 0];
    // 背景：取同文字色最接近嘅 10% 像素（最差情況）＋平均
    const ds = b.px.map(p => cr(p, col)).sort((x, y) => x - y), worst = ds[Math.floor(ds.length * 0.1)] || ds[0], mean = cr(b.mean, col);
    const olc = it.ol && it.ol[3] > 0.5 ? cr(it.ol, col) : 0; it.bg = b.mean; it.crMean = +mean.toFixed(2); it.crWorst = +worst.toFixed(2); it.crOl = +olc.toFixed(2);
    it.cr = +Math.max(olc >= minCr ? olc : 0, Math.min(mean, worst * 1.4)).toFixed(2);   // 有深色描邊（≥4.5）就以描邊計
  });
  const bad = items.filter(it => it.eff < minEff - 0.01 || it.cr < minCr || /GlimmerFP8|GlimmerFP10/.test(it.fam) || (/GlimmerFP12/.test(it.fam) && it.fs % 12 !== 0));
  return { items, bad };
}
module.exports = { audit, collect, cr, lum };
