/* dialogue-ui.js — 對話 UI（DOM）。配合 src/dialogue.js 執行器。
   規格（遊策 tuning／dialogue-format）：打字機 dialog_cps（預設 30，?cps= 覆寫）；點一下＝顯示整句，再點＝下一句；選項按鈕 ≥44px（手機觸控）；
   「跳過」鍵（跳到下一個選項／結尾）；長按對話框 ≥0.4s＝快進（放手停）；鍵盤：Enter／空白／E＝推進，1–4＝揀選項；autoadvance_ms；R.blocked（阻塞型動作）期間唔接受推進。
   另有：say(speaker,text)（單句旁白，唔入 seen）、prompt(title,default)（命名對話框）。 */
(function (g) {
  'use strict';
  const CSS = `
#wr-dlg{position:fixed;left:8px;right:8px;bottom:calc(8px + env(safe-area-inset-bottom,0px));display:none;z-index:30;font:15px/1.5 system-ui,"Noto Sans TC",sans-serif;color:#f2f4ff;max-width:640px;margin:0 auto}
#wr-dlg .box{background:rgba(16,22,58,.94);border:2px solid #ffe98a;border-radius:10px;padding:8px 12px 10px;min-height:76px;position:relative}
#wr-dlg .who{color:#ffe98a;font-weight:700;font-size:13px;margin-bottom:2px;min-height:18px}
#wr-dlg .txt{white-space:pre-wrap;min-height:44px}
#wr-dlg .por{position:absolute;left:10px;bottom:100%;margin-bottom:-2px;image-rendering:pixelated;background:rgba(16,22,58,.94);border:2px solid #ffe98a;border-bottom:none;border-radius:10px 10px 0 0;display:none}
#wr-dlg .more{position:absolute;right:12px;bottom:6px;color:#ffe98a;font-size:12px;animation:wrb 1s infinite}
@keyframes wrb{50%{opacity:.2}}
#wr-dlg .ch{display:flex;flex-direction:column;gap:6px;margin-top:8px}
#wr-dlg .ch button,#wr-dlg .skip,#wr-prompt button{min-height:48px;min-width:48px;border-radius:10px;border:2px solid #ffe98a;background:#232c6b;color:#fff;font:inherit;padding:6px 12px;text-align:left;cursor:pointer}
#wr-dlg .ch button[disabled]{opacity:.45}
#wr-dlg .ch button small{display:block;color:#ffc;font-size:11px}
#wr-dlg .skip{position:absolute;right:6px;top:-56px;text-align:center;background:rgba(16,22,58,.85);border-color:rgba(255,233,138,.6);font-size:13px}
#wr-prompt{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(5,8,25,.7);z-index:40;font:15px system-ui,"Noto Sans TC",sans-serif;color:#fff}
#wr-prompt .p{background:#10163a;border:2px solid #ffe98a;border-radius:12px;padding:14px;width:min(320px,86vw)}
#wr-prompt input{width:100%;box-sizing:border-box;min-height:48px;font:inherit;padding:6px 10px;border-radius:8px;border:2px solid #556;background:#0b0e22;color:#fff;margin:8px 0}
`;
  function create(R, G, o) {
    o = o || {}; const doc = o.doc || document, tun = (G && G.tuning) || {};
    const q = new URLSearchParams(g.location ? g.location.search : ''); const cps = +(o.cps || q.get('cps') || tun.dialog_cps || 30), holdMs = (+tun.dialog_skip_hold_s || 0.4) * 1000;
    if (!doc.getElementById('wr-dlg-css')) { const st = doc.createElement('style'); st.id = 'wr-dlg-css'; st.textContent = CSS; doc.head.appendChild(st); }
    const root = doc.createElement('div'); root.id = 'wr-dlg'; root.innerHTML = '<button class="skip" style="display:none">跳過 ⏭</button><div class="box"><canvas class="por" width="64" height="64"></canvas><div class="who"></div><div class="txt"></div><div class="ch"></div><span class="more">▼</span></div>'; (o.parent || doc.body).appendChild(root);
    const $ = s => root.querySelector(s), por = root.querySelector('.por'), who = $('.who'), txt = $('.txt'), chs = $('.ch'), more = $('.more'), skipBtn = $('.skip'), box = $('.box');
    const U = { open: false, shown: 0, full: '', st: null, simple: null, ff: false, cps, endCbs: [], lines: 0 }; let raf = 0, last = 0, autoT = 0, holdT = 0, autoWait = 0;
    const speakerName = id => { const sp = (G.data.flags && G.data.flags.speakers) || {}; return G.text(sp[id] != null ? sp[id] : id); };
    // 頭像（遊美 §N.3：64×64，portrait_id＋expression；缺省 neutral，未知表情回退 neutral；整數倍縮放 nearest）
    U.portraits = null; const pctx = por.getContext('2d');
    function drawPortrait(st) {
      const P = U.portraits; let id = st.portrait || (P && P.speakerMap[st.speaker]) || '', ex = st.expression || (P && P.emoteMap[st.emote]) || 'neutral'; const e = P && id && P.map[id]; if (!e) { por.style.display = 'none'; U.portraitShown = ''; return; }
      const r = e.rects[ex] || e.rects.neutral, scale = (g.innerWidth || 390) >= 600 ? 3 : 2; por.style.width = 64 * scale + 'px'; por.style.height = 64 * scale + 'px'; pctx.clearRect(0, 0, 64, 64); pctx.imageSmoothingEnabled = false; pctx.drawImage(e.img, r[0], r[1], r[2], r[3], 0, 0, 64, 64); por.style.display = 'block'; U.portraitShown = id + ':' + (e.rects[ex] ? ex : 'neutral');
    }
    U.setPortraits = P => { U.portraits = P; };
    function show() { root.style.display = 'block'; U.open = true; if (!raf) { last = performance.now(); raf = requestAnimationFrame(loop); } }
    function hide() { root.style.display = 'none'; U.open = false; cancelAnimationFrame(raf); raf = 0; }
    function setLine(st) {
      U.st = st; U.full = Array.from(st.text).join(''); U.chars = Array.from(st.text); U.shown = cps >= 9999 ? U.chars.length : 0; autoWait = 0; U.lines++;
      drawPortrait(st); who.textContent = st.speaker === 'narrator' || st.speaker === 'system' ? '' : speakerName(st.speaker); chs.innerHTML = ''; draw();
    }
    function draw() {
      txt.textContent = U.chars.slice(0, Math.floor(U.shown)).join(''); const done = U.shown >= U.chars.length;
      skipBtn.style.display = U.open && !U.simple ? 'block' : 'none';
      more.style.display = done && U.st && !U.st.hasChoices && !G_blocked() ? 'block' : 'none';
      if (done && U.st && U.st.hasChoices && !chs.children.length) { U.st.choices.forEach(c => { const b = doc.createElement('button'); b.textContent = (c.i + 1) + '. ' + c.text; if (!c.enabled) { b.disabled = true; if (c.hint) { const s = doc.createElement('small'); s.textContent = c.hint; b.appendChild(s); } } b.addEventListener('click', ev => { ev.stopPropagation(); choose(c.i); }); chs.appendChild(b); }); }
    }
    const G_blocked = () => !!(R && R.blocked);
    function loop(ts) { raf = requestAnimationFrame(loop); const dt = Math.min(0.1, (ts - last) / 1000 || 0); last = ts; tick(dt); }
    function tick(dt) {
      if (!U.open || !U.st) return; const n = U.chars.length;
      if (U.ff && !U.simple) { U.shown = n; draw(); if (!U.st.hasChoices && !G_blocked()) { advance(true); } return; }
      if (U.shown < n) { U.shown = Math.min(n, U.shown + cps * dt); draw(); }
      else if (!U.simple && U.st.autoMs > 0 && !U.st.hasChoices && !G_blocked()) { autoWait += dt * 1000; if (autoWait >= U.st.autoMs) { autoWait = 0; advance(true); } }
    }
    function sync() { if (R.active && R.state) { if (!U.open) show(); if (U.st !== R.state) setLine(R.state); } }
    function advance(fromAuto) {
      if (U.simple) { if (U.shown < U.chars.length) { U.shown = U.chars.length; draw(); return; } const r = U.simple; U.simple = null; hide(); r(); return; }
      if (!U.open || !U.st) return; if (G_blocked()) return;
      if (U.shown < U.chars.length) { if (!fromAuto) { U.shown = U.chars.length; draw(); } return; }
      if (U.st.hasChoices) return; R.advance(); sync(); if (!R.active) closed();
      if (R.blocked) { const p = R.blocked; p.then(() => { sync(); draw(); }); }
    }
    function choose(i) { if (!U.open || G_blocked()) return; R.choose(i); sync(); if (!R.active) closed(); if (R.blocked) { const p = R.blocked; p.then(() => { sync(); draw(); }); } }
    function closed() { U.st = null; hide(); const cbs = U.endCbs.slice(); U.endCbs = []; cbs.forEach(f => f()); }
    function skip() { if (U.simple) { advance(); return; } if (!U.open || G_blocked()) return; R.skip({ choices: 'stop' }); sync(); if (!R.active) closed(); else { U.shown = U.chars.length; draw(); } }
    // 輸入
    box.addEventListener('pointerdown', ev => { if (ev.target.closest('.ch')) return; holdT = setTimeout(() => { U.ff = true; }, holdMs); });
    const rel = () => { clearTimeout(holdT); U.ff = false; };
    box.addEventListener('pointerup', ev => { const wasFF = U.ff; rel(); if (ev.target.closest('.ch')) return; if (!wasFF) advance(); }); box.addEventListener('pointerleave', rel); box.addEventListener('pointercancel', rel);
    root.addEventListener('click', ev => { if (ev.detail === 0 && !ev.target.closest('.ch') && !ev.target.closest('.skip')) advance(); });
    skipBtn.addEventListener('click', ev => { ev.stopPropagation(); skip(); });
    g.addEventListener('keydown', e => {
      if (!U.open) return; if (e.key === 'Enter' || e.key === ' ' || e.key === 'e' || e.key === 'E') { e.preventDefault(); advance(); }
      else if (/^[1-9]$/.test(e.key) && U.st && U.st.hasChoices && U.shown >= U.chars.length) { const c = U.st.choices[+e.key - 1]; if (c && c.enabled) choose(c.i); }
      else if (e.key === 'Escape') skip();
    });
    // API
    U.start = (id, opts) => new Promise(res => { U.endCbs.push(res); const st = R.start(id, opts); if (!R.active) { closed(); return; } sync(); if (R.blocked) { const p = R.blocked; p.then(() => { sync(); draw(); }); } void st; });
    U.say = (speaker, text) => new Promise(res => { U.simple = res; U.st = { speaker: speaker || 'narrator', text: G.text(text), hasChoices: false, choices: [], autoMs: 0 }; show(); setLine(U.st); });
    U.skipAll = () => { if (!U.open || U.simple || G_blocked()) return; R.skip({ choices: 'first' }); sync(); if (!R.active) closed(); else { draw(); } };
    if (R.on) R.on('end', () => { if (U.open && !U.simple) closed(); });
    U.tick = tick;
    // 命名對話框
    const pr = doc.createElement('div'); pr.id = 'wr-prompt'; pr.innerHTML = '<div class="p"><div class="t"></div><input maxlength="8" autocomplete="off"><div style="display:flex;gap:8px;justify-content:flex-end"><button class="ok">確定</button></div></div>'; (o.parent || doc.body).appendChild(pr);
    U.prompt = (title, def, max) => new Promise(res => { const inp = pr.querySelector('input'); pr.querySelector('.t').textContent = title; inp.value = def || ''; inp.maxLength = max || 8; pr.style.display = 'flex'; setTimeout(() => inp.focus(), 30); const done = () => { pr.style.display = 'none'; pr.querySelector('.ok').onclick = null; inp.onkeydown = null; res(inp.value.trim() || def || ''); }; pr.querySelector('.ok').onclick = done; inp.onkeydown = e => { e.stopPropagation(); if (e.key === 'Enter') done(); }; });
    U.state = () => ({ open: U.open, simple: !!U.simple, shown: Math.floor(U.shown), total: U.chars ? U.chars.length : 0, speaker: U.st && U.st.speaker, portrait: U.portraitShown || '', text: U.st && U.st.text, choices: U.st ? U.st.choices.map(c => c.text) : [], node: U.st && U.st.node, cps });
    U.root = root;
    return U;
  }
  g.WR = g.WR || {}; g.WR.DialogueUI = { create }; if (typeof module !== 'undefined' && module.exports) module.exports = g.WR.DialogueUI;
})(typeof globalThis !== 'undefined' ? globalThis : this);
