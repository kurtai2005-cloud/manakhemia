/* 《微光小圃》 work62.js — 6b.2 ⑧「工作」主畫面（5b 小職業）。原創代碼；邏輯全部照用 long5b.js（B.plan），呢度只做顯示。
   ・入口：花園主 rail「工作」掣（散步下面）；左上「返回」返主畫面。
   ・全畫面場景：每隻返緊工嘅寵物一個工作站（工作地點背景＝洋紅虛線 placeholder＋工作 icon），寵物用現有 walk／idle clip 輪住郁（10fps）。
   ・每隻顯示：工作名、Lv、今日已賺／日薪、更份進度條、幾時收工。全家今日 n／12 上限喺頂。
   ・更份只係顯示（5b 冇「返工時間」概念，糧照舊喺揀工作嗰下出、守夜 21:00 後出）：日更 09:00–17:00；守夜 21:00–05:00。
   ・美術缺件：work_bg_<job> 175×120（@3x 525×360）×4、各形態專用工作 clip（團絨 64×64、細佬 48×48，6–8 幀）——見 docs MISSING_ART_6b2.md。
   ・?ui62=0／?l5b=0 全停。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.work62 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const SHIFT = { post: [9, 17], garden: [9, 17], chef: [9, 17], watch: [21, 29] };   // 29 ＝ 翌日 05:00
  const pad2 = (n) => (n < 10 ? '0' : '') + n, hm = (h) => pad2(Math.floor(h) % 24) + ':' + pad2(Math.round((h % 1) * 60));
  // 更份進度（純函數，unit 測）：h＝而家鐘數（0–24，可帶小數）
  function shift(job, h) {
    const S = SHIFT[job] || SHIFT.post, a = S[0], b = S[1]; let x = h; if (b > 24 && h < b - 24) x = h + 24;
    if (x < a) return { pct: 0, state: 'before', label: hm(a) + ' 開工', end: hm(b) };
    if (x >= b) return { pct: 1, state: 'done', label: '收咗工（' + hm(b) + '）', end: hm(b) };
    return { pct: (x - a) / (b - a), state: 'on', label: hm(b) + ' 收工・剩 ' + (function (m) { return m >= 60 ? Math.floor(m / 60) + ' 小時' + (m % 60 ? ' ' + (m % 60) + ' 分' : '') : m + ' 分鐘'; })(Math.max(1, Math.round((b - x) * 60))), end: hm(b) };
  }
  function install(G, NS) {
    const qs = new URLSearchParams(location.search); if (qs.get('ui62') === '0') return false;
    const B = NS.long5b; if (!B || (B.isOn && !B.isOn())) return false;
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now(), $ = (s) => document.querySelector(s);
    const UIS = (h) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, {}); } catch (e) { } };
    const LB5 = 'art/series2_long/5b/ui/', FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK",sans-serif', FP = ((G.v3 && G.v3.want) ? '"GlimmerV3Sans",' : '"GlimmerFP12",') + FALL;   // #83 V3 → Noto Sans CJK TC
    const STAT = { opens: 0, frames: 0, ph: 0 };
    const css = document.createElement('style'); css.textContent = `
#u62work { position:absolute; left:0; top:0; width:390px; height:844px; z-index:52; overflow:hidden; color:#F7EEDB; touch-action:pan-y; user-select:none; animation:u62fade 220ms ease;
  background:radial-gradient(90% 40% at 50% 0%, rgba(255,214,150,.18), rgba(0,0,0,0) 70%), linear-gradient(180deg,#1d2140 0%,#2a2a4c 46%,#3a3040 100%); }
#u62work .hd { position:absolute; left:0; right:0; top:0; height:140px; }
#u62work .back { position:absolute; left:12px; top:20px; width:96px; height:52px; box-sizing:border-box; display:flex; align-items:center; justify-content:center; gap:4px; border-radius:26px; border:1px solid rgba(232,194,122,.75); background:rgba(20,22,42,.72); font:24px/28px ${FP}; color:#F7EEDB; cursor:pointer; }
#u62work .ttl { position:absolute; left:120px; right:120px; top:22px; height:48px; display:flex; align-items:center; justify-content:center; font:24px/28px ${FP}; letter-spacing:4px; color:#F4D58C; text-shadow:0 2px 6px rgba(0,0,0,.6); }
#u62work .hd .u62sub { position:absolute; left:20px; right:20px; top:78px; margin:0 !important; }
#u62work .sum { position:absolute; left:20px; right:20px; top:120px; height:22px; display:flex; align-items:center; gap:8px; font:500 16px/22px ${FALL}; color:#E9DFC9; }
#u62work .sum .bar { flex:1; height:8px; border-radius:4px; background:rgba(255,255,255,.12); overflow:hidden; } #u62work .sum .bar i { display:block; height:100%; background:linear-gradient(90deg,#E8C27A,#FFE3A0); }
#u62work .grid { position:absolute; left:14px; right:14px; top:156px; bottom:156px; overflow-y:auto; display:grid; grid-template-columns:1fr 1fr; gap:12px; align-content:start; padding-bottom:12px; }
#u62work .st { position:relative; box-sizing:border-box; border-radius:14px; overflow:hidden; border:1px solid rgba(232,194,122,.6); background:rgba(14,16,32,.78); box-shadow:0 8px 20px rgba(0,0,0,.35), inset 0 0 16px rgba(232,194,122,.12); animation:u62in 260ms cubic-bezier(.2,.8,.2,1) both; }
#u62work .sc { position:relative; height:120px; box-sizing:border-box; border:2px dashed #ff00ff; background:repeating-linear-gradient(135deg, rgba(255,0,255,.10) 0 8px, rgba(255,0,255,.03) 8px 16px); }
#u62work .sc .phl { position:absolute; left:6px; top:4px; width:110px; font:500 16px/20px ${FALL}; color:#FFC4FF; white-space:pre-line; word-break:break-all; text-shadow:0 1px 1px #000; }
#u62work .sc img.ic { position:absolute; right:6px; top:6px; width:36px; height:36px; image-rendering:pixelated; }
#u62work .sc canvas { position:absolute; left:50%; bottom:2px; width:96px; height:96px; margin-left:-48px; image-rendering:pixelated; }
#u62work .sc .gnd { position:absolute; left:0; right:0; bottom:0; height:18px; background:linear-gradient(180deg, rgba(0,0,0,0), rgba(0,0,0,.35)); }
#u62work .inf { padding:8px 12px 12px; }
#u62work .nm { font:500 18px/26px ${FALL}; color:#F7EEDB; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
#u62work .jb { font:500 16px/22px ${FALL}; color:#F4D58C; }
#u62work .er { font:500 16px/22px ${FALL}; color:#E9DFC9; }
#u62work .pb { height:8px; margin:6px 0 4px; border-radius:4px; background:rgba(255,255,255,.14); overflow:hidden; } #u62work .pb i { display:block; height:100%; border-radius:4px; background:linear-gradient(90deg,#8FD3C1,#E8C27A); transition:width .6s ease; }
#u62work .en { font:500 16px/22px ${FALL}; color:#D9CFBC; }
#u62work .ft { position:absolute; left:16px; right:16px; bottom:20px; height:60px; display:flex; align-items:center; gap:12px; }
#u62work .ft .rs { flex:1; font:500 16px/22px ${FALL}; color:#D9CFBC; overflow:hidden; max-height:44px; }
#u62work .ft .go { flex:0 0 auto; min-width:136px; height:52px; padding:0 16px; box-sizing:border-box; display:flex; align-items:center; justify-content:center; border-radius:26px; border:1px solid rgba(232,194,122,.85); background:rgba(232,194,122,.18); font:24px/28px ${FP}; color:#F7EEDB; cursor:pointer; }
#u62work .empty { grid-column:1 / span 2; padding:32px 16px; text-align:center; font:500 18px/26px ${FALL}; color:#E9DFC9; }
#u62workbtn { cursor:pointer; } #u62workbtn > i.i { position:absolute; left:50%; top:50%; width:36px; height:36px; margin:-18px 0 0 -18px; pointer-events:none; }
`; document.head.appendChild(css);
    const mk = (tag, cls, txt, tid) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, cls) => { const i = new Image(); i.alt = ''; i.draggable = false; if (cls) i.className = cls; i.src = src; return i; };
    const OV = { el: null, cards: [], t0: 0 };
    const gameHour = () => { const d = new Date(now()); const h = G.hour ? G.hour() : d.getHours(); return h + d.getMinutes() / 60; };
    const rowsWork = () => { try { const p = B.plan(S(), now()); return { p, w: p.rows.filter(r => r.a === 'job' && r.job), rest: p.rows.filter(r => !(r.a === 'job' && r.job)) }; } catch (e) { return { p: { sh: 0, shMax: 12, rows: [] }, w: [], rest: [] }; } };
    function open() {
      close(true); const host = $('#ui') || document.body; const el = OV.el = mk('div', '', null, 'u62w-screen'); el.id = 'u62work'; OV.t0 = pnow();
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      const hd = mk('div', 'hd'); el.appendChild(hd);
      const bk = mk('div', 'back', '‹ 返回', 'u62w-back'); bk.setAttribute('role', 'button'); bk.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); close(); }); hd.appendChild(bk);
      hd.appendChild(mk('div', 'ttl', '工作', 'u62w-title'));
      const sum = mk('div', 'sum', null, 'u62w-sum'); hd.appendChild(sum);
      el.appendChild(mk('div', 'grid', null, 'u62w-grid'));
      const ft = mk('div', 'ft', null, 'u62w-foot'); ft.appendChild(mk('div', 'rs', '', 'u62w-rest')); const go = mk('div', 'go', '安排工作', 'u62w-plan'); go.setAttribute('role', 'button');
      go.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); close(true); if (G.l5b && G.l5b.plan) G.l5b.plan(); }); ft.appendChild(go); el.appendChild(ft);
      host.appendChild(el); document.body.classList.add('u62w-on'); STAT.opens++; build(); return el;
    }
    function close(quiet) { if (!OV.el) return false; OV.el.remove(); OV.el = null; OV.cards = []; document.body.classList.remove('u62w-on'); if (!quiet) UIS('close'); return true; }
    let sig = '';
    function build() {
      if (!OV.el) return; const { p, w, rest } = rowsWork(), grid = OV.el.querySelector('.grid'); sig = w.map(r => r.id + r.job + (r.info ? r.info.lv : '') + r.paid).join('|');
      grid.textContent = ''; OV.cards = [];
      if (!w.length) grid.appendChild(mk('div', 'empty', '今日仲未有寵物返工。撳下面「安排工作」幫佢哋揀一份工。', 'u62w-empty'));
      w.forEach((r, i) => {
        const st = mk('div', 'st', null, 'u62w-st-' + r.id); st.style.animationDelay = (i * 60) + 'ms'; st.dataset.job = r.job;
        const sc = mk('div', 'sc', null, 'u62w-sc-' + r.id); sc.dataset.ph = '6b2:work_bg_' + r.job; sc.appendChild(mk('div', 'phl', r.job + '\n175×120')); STAT.ph++;
        sc.appendChild(img(LB5 + 'icon_job_' + r.job + '@3x.png', 'ic')); const cv = document.createElement('canvas'); cv.width = 96; cv.height = 96; cv.dataset.testid = 'u62w-pet-' + r.id; sc.appendChild(cv); sc.appendChild(mk('div', 'gnd'));
        st.appendChild(sc); const inf = mk('div', 'inf'); st.appendChild(inf);
        inf.appendChild(mk('div', 'nm', r.name || '住客', 'u62w-name-' + r.id));
        inf.appendChild(mk('div', 'jb', (r.info ? r.info.zh : B.JOB[r.job].zh) + '・Lv' + (r.info ? r.info.lv : 1), 'u62w-job-' + r.id));
        inf.appendChild(mk('div', 'er', '', 'u62w-earn-' + r.id)); const pb = mk('div', 'pb', null, 'u62w-bar-' + r.id); pb.appendChild(mk('i')); inf.appendChild(pb); inf.appendChild(mk('div', 'en', '', 'u62w-end-' + r.id));
        grid.appendChild(st); OV.cards.push({ r, st, cv, ph: (i * 977) % 4000 });
      });
      refresh(p, rest);
    }
    function refresh(p, rest) {
      if (!OV.el) return; if (!p) { const o = rowsWork(); p = o.p; rest = o.rest; const s2 = o.w.map(r => r.id + r.job + (r.info ? r.info.lv : '') + r.paid).join('|'); if (s2 !== sig) return build(); }
      const sum = OV.el.querySelector('.sum'); sum.innerHTML = ''; sum.appendChild(mk('span', '', '全家今日 ' + p.sh + '／' + p.shMax + ' 粒')); const bar = mk('div', 'bar'); const bi = mk('i'); bi.style.width = Math.round(100 * Math.min(1, p.sh / Math.max(1, p.shMax))) + '%'; bar.appendChild(bi); sum.appendChild(bar);
      const h = gameHour();
      for (const c of OV.cards) { const r = (p.rows.find(x => x.id === c.r.id) || c.r), pay = r.info ? r.info.pay : 0, sf = shift(r.job, h);
        const er = c.st.querySelector('.er'); er.textContent = r.paid ? '今日已賺 ' + pay + '／' + pay + ' 粒' : (r.job === 'watch' ? '今晚出糧 0／' + pay + ' 粒' : (r.info && r.info.capped ? '今日到頂 0／' + pay + ' 粒' : '今日已賺 0／' + pay + ' 粒'));
        c.st.querySelector('.pb i').style.width = Math.round(sf.pct * 100) + '%'; c.st.querySelector('.en').textContent = sf.label; c.st.dataset.shift = sf.state; c.st.dataset.pct = sf.pct.toFixed(3); }
      const rs = OV.el.querySelector('.rs'); rs.textContent = rest && rest.length ? '休息／遠足中：' + rest.map(r => r.name).join('、') : '全部住客都有安排。';
    }
    // 寵物工作動畫：walk 2.4 秒（左右行）→ idle 2.4 秒；團絨 atlas／細佬 strip
    function anim() {
      if (!OV.el) return; const SA = G.s2Art; if (!SA) return; const t = pnow() - OV.t0;
      for (const c of OV.cards) { const g = c.cv.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, 96, 96);
        const ct = t + c.ph, cyc = ct % 4800, walk = cyc < 2400, clip = walk ? 'walk' : 'idle', u = walk ? cyc / 2400 : 0, dx = walk ? Math.round(Math.sin(u * Math.PI * 2) * 14) : 0, flip = walk && Math.cos(u * Math.PI * 2) < 0;
        let src = null, k = 2; const r = c.r;
        if (r.kind === 'kid') { const im = SA.strip(r.fk, clip) || SA.strip(r.fk, 'idle'); if (im && im.width) { const n = Math.max(1, Math.round(im.width / 48)), f = SA.kidFrame ? SA.kidFrame(r.fk, clip, ct) % n : 0; src = { img: im, sx: f * 48, sy: 0, sw: 48, sh: 48 }; } }
        else { const a = SA.atlasSrc(r.fk, clip, ct); if (a && a.src && a.src.img) src = a.src; k = 1.5; }
        if (!src || !src.img) continue; const w = src.sw * k, hh = src.sh * k; g.save(); g.translate(48 + dx, 96); if (flip) g.scale(-1, 1); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, -w / 2, -hh, w, hh); g.restore(); c.cv.dataset.clip = clip; STAT.frames++; }
    }
    { const loop = () => { try { anim(); } catch (e) { } setTimeout(loop, 100); }; setTimeout(loop, 200); }
    { const loop = () => { try { if (OV.el) refresh(); railTick(); } catch (e) { } setTimeout(loop, 1000); }; setTimeout(loop, 600); }
    // ── 主 rail「工作」掣（散步下面）──
    const RB = { el: null };
    function railTick() {
      const s = S(); let rows = 0; try { rows = s && s.fam ? B.plan(s, now()).rows.length : 0; } catch (e) { rows = 0; }
      const show = !!s && s.stage !== 'egg' && rows > 0 && !document.body.classList.contains('s2-scene'); let el = RB.el;
      if (!el) { if (!show) return; const host = document.getElementById('hdRail') || document.getElementById('top-r'); if (!host) return;
        el = RB.el = mk('div', 'ibtn panel', null, 'u62w-rail'); el.id = 'u62workbtn'; el.title = '工作'; el.setAttribute('aria-label', '工作');
        el.innerHTML = '<i class="m"></i><i class="i"></i><i class="l">工作</i>'; const ic = img(LB5 + 'icon_job_post@3x.png'); ic.style.cssText = 'position:absolute;left:0;top:0;width:36px;height:36px;image-rendering:pixelated;pointer-events:none'; el.querySelector('i.i').appendChild(ic);
        el.addEventListener('click', (e) => { e.stopPropagation(); if ((NS.ui && NS.ui.isModalOpen && NS.ui.isModalOpen()) || $('#l5bov') || $('#l6bov')) return; UIS('tap'); open(); }); host.appendChild(el); }
      el.style.display = show ? '' : 'none'; if (!show) return;
      const wb = document.getElementById('l6bbtn'), vis = (e) => !!(e && e.style.display !== 'none' && e.offsetParent !== null);
      if (vis(wb)) { const step = 70; el.style.left = wb.style.left; el.style.top = (parseFloat(wb.style.top) + step) + 'px'; }
      else { const u = G.ui2, rl = u && u.rail; if (rl && rl.kid && rl.dex) { el.style.left = rl.kid.x + 'px'; el.style.top = (rl.kid.y + (rl.kid.y - rl.dex.y)) + 'px'; } else { el.style.left = '360px'; el.style.top = '384px'; } }
    }
    G.work62 = { open, close, isOpen: () => !!OV.el, shift };
    window.__qa = window.__qa || {}; window.__qa.work62 = { open, close, isOpen: () => !!OV.el, st: () => ({ open: !!OV.el, cards: OV.cards.map(c => ({ id: c.r.id, job: c.r.job, shift: c.st.dataset.shift, pct: +c.st.dataset.pct, clip: c.cv.dataset.clip || null })), stat: Object.assign({}, STAT) }), shift, rail: () => railTick() };
    return true;
  }
  return { install, shift, SHIFT };
});
