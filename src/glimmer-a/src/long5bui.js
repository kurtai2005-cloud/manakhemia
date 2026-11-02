/* 《微光小圃》 long5bui.js — 第 5 批 5b 介面（遠足＋小職業；遊策 5a–5c spec §5b＋遊美 art/series2_long/5b）。原創代碼。
   邏輯全部喺 long5b.js（s.fam.b5）；呢度只做：屋仔「今日安排」掣＋每日安排面板（遠足／工作／休息三段）、揀工作 2×2、
   返屋 toast（點開日記）、「團絨日記」、屋入面出發／返屋動畫＋頭頂手信、工作帽（按等級 t1–t4）、每秒 scan、🛠 開發者模式「5b」。
   字一律 FP12 24px（UI v2 規則：唔縮細字，改換行）；圖用 Image.src。?l5b=0（或 ?l5=0／?house=0／?s2=0）全停；?ev=0 唔自動彈 toast。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.long5bui = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const B = NS.long5b, FAM = NS.long5a, SR = NS.series2, UI = NS.ui; if (!B || !FAM || !SR || !UI || !G.s2Art) return false;
    const qs = new URLSearchParams(location.search);
    if (qs.get('l5b') === '0' || qs.get('l5') === '0' || qs.get('house') === '0' || qs.get('s2') === '0') { B.setOn(false); return false; }
    B.setOn(true);
    const QUIET = qs.get('ev') === '0';
    const S = () => G.state, now = () => (G.now ? G.now() : Date.now()), pnow = () => performance.now(), SA = G.s2Art, R = G.renderer, LB5 = 'art/series2_long/5b/';
    const save = () => { if (G.save) G.save(); };
    const UIS = (h, i) => { const a = NS.audio; if (a && a.Engine && a.Engine.ui) try { a.Engine.ui(h, i || {}); } catch (e) { } };
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 80) log.shift(); };
    const toasts = []; const toast = (m, ms) => { toasts.push(m); if (toasts.length > 30) toasts.shift(); UI.toast(m, ms || 2000); };
    const H5 = () => G.house5;
    const U = () => (G.ui2 && G.ui2.on && G.ui2.bi ? G.ui2 : null);
    const ui5b = (n) => LB5 + 'ui/' + n + '@3x.png', medal = (sv) => LB5 + 'souvenir/' + sv + '_medal@3x.png', sv1 = (sv) => LB5 + 'souvenir/' + sv + '_1x.png';
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif';
    const F8 = () => (U() ? '"GlimmerFP8",' : '') + FALL, F12 = () => (U() ? '"GlimmerFP12",' : '') + FALL;
    const CREAM = '#FFF5DC', GOLD = '#FFE08A', INK = '#3A2840', SUB = '#E8DDBE';
    const OL = 'text-shadow:-2px 0 0 #24172C,2px 0 0 #24172C,0 -2px 0 #24172C,0 2px 0 #24172C,-2px -2px 0 #24172C,2px -2px 0 #24172C,-2px 2px 0 #24172C,2px 2px 0 #24172C;';
    const FB = { panel_navy: 'background:#2A2450;border:4px solid #F0D58A;border-radius:12px;', card: 'background:#3A3466;border:3px solid #C9B27A;border-radius:8px;', card_sel: 'background:#3A3466;border:3px solid #FFE08A;border-radius:8px;',
      plaque_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:6px;', btn_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;',
      btn16_pri: 'background:#F3A64A;border:3px solid #6B3A1E;border-radius:8px;', btn16_sec: 'background:#69B7C9;border:3px solid #24485A;border-radius:8px;', btn16_violet: 'background:#9C86D8;border:3px solid #3C2E6A;border-radius:8px;', btn16_dis: 'background:#8C8796;border:3px solid #4A4656;border-radius:8px;',
      chip: 'background:#2A2450;border:2px solid #C9B27A;border-radius:8px;', panel_inset: 'background:#1E1A3E;border:2px solid #574F8A;border-radius:6px;', bar_trough_h7: 'background:#1E1A3E;border-radius:4px;', card_locked: 'background:#4A4656;border:3px solid #6E6A7A;border-radius:8px;',
      close: 'background:#E46C8C;border:3px solid #fff;border-radius:50%;', med40_gold: 'background:#F6C85A;border:4px solid #6B3A1E;border-radius:50%;' };
    const bi = (n) => { const u = U(); const c = u ? u.bi(n) : ''; return c || FB[n] || ''; };
    const sp = (n) => { const u = U(); return (u && u.sp(n)) || FB[n] || ''; };
    const mk = (tag, css, txt, tid) => { const e = document.createElement(tag); if (css) e.style.cssText = css; if (txt != null) e.textContent = txt; if (tid) e.dataset.testid = tid; return e; };
    const img = (src, css) => { const i = new Image(); i.draggable = false; i.alt = ''; i.style.cssText = 'position:absolute;image-rendering:pixelated;pointer-events:none;' + (css || ''); i.src = src; return i; };
    const TXT = (size, color, extra) => `font:${U() ? (size <= 24 ? 24 : 36) : Math.max(size, 20)}px/1.2 ${U() ? F12() : F8()};color:${color || CREAM};${color === INK ? '' : OL}-webkit-font-smoothing:none;` + (extra || '');
    function btn(label, kind, w, h, tid, onClick, icn) {
      const b = mk('div', `position:absolute;width:${w}px;min-height:${h}px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:4px;cursor:pointer;padding:2px 6px;${bi(kind)}` + TXT(24), null, tid);
      if (icn) b.appendChild(img(icn, 'position:relative;width:26px;height:26px;flex:0 0 26px'));
      b.appendChild(mk('span', 'position:relative;text-align:center', label));
      b.addEventListener('click', (e) => { e.stopPropagation(); if (b.dataset.dis === '1') { if (b._why) toast(b._why, 1800); UIS('tap'); return; } UIS('tap'); onClick && onClick(e); });
      return b;
    }
    // 圖 cache（canvas 用）
    const IMC = new Map(); function imI(src) { let i = IMC.get(src); if (!i) { i = new Image(); i.src = src; IMC.set(src, i); } return i.complete && i.naturalWidth ? i : null; }
    let J5 = null; G.l5bLoad = fetch(LB5 + 'long_5b.json').then(r => (r.ok ? r.json() : null)).then(j => { if (j) { J5 = { ex: j.expedition, jobs: j.jobs, sor: j.expedition.souvenirOnReturn || { dy: -10, frames: [5, 6, 7, 8, 9], bobPx: [0, -1, 0, 1, 0] } }; note('json'); } return J5; }).catch(e => { note('jsonErr', { e: String(e) }); return null; });

    // ── 樣式 ──
    const css = document.createElement('style'); css.id = 'l5bcss';
    css.textContent = `#l5bov{position:absolute;left:0;top:0;width:390px;height:844px;z-index:59;user-select:none;-webkit-user-select:none;touch-action:manipulation}
#l5bov .bd{position:absolute;inset:0;background:rgba(18,12,30,.62)}
body.l5b-on #toast{z-index:72 !important}
#l5bov .scr{position:absolute;overflow-y:auto;overflow-x:hidden;-webkit-overflow-scrolling:touch;scrollbar-width:none}
#l5bov .scr::-webkit-scrollbar{display:none}
#l5bov .l5bprow{position:relative;display:flex;gap:8px;box-sizing:border-box;margin:0 0 8px;padding:8px}
#l5bov .l5bseg{position:relative;flex:1 1 0;min-width:0;min-height:40px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:2px;cursor:pointer;padding:2px 2px}
#l5bov .l5bseg.lk{opacity:.92}
#l5bov .l5bjc{position:relative;width:150px;min-height:214px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;gap:4px;padding:8px 6px;cursor:pointer}
#l5btoast{position:absolute;left:28px;top:200px;width:334px;z-index:61;box-sizing:border-box;display:flex;align-items:center;gap:10px;padding:8px 10px;cursor:pointer;transform:translateY(-260px);transition:transform 260ms cubic-bezier(.34,1.56,.64,1)}
#l5btoast.in{transform:translateY(0)}
#l5bhud{position:absolute;left:314px;top:674px;width:60px;height:60px;z-index:5;cursor:pointer;box-sizing:border-box;pointer-events:auto}
@keyframes l5bdot{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}`;
    document.head.appendChild(css);

    // ── 疊層 ──
    const OV = { el: null, kind: null, data: null };
    function ov(kind, data) {
      closeOv(true); const host = document.getElementById('ui') || document.body;
      const el = OV.el = mk('div', '', null, 'l5b-' + kind); el.id = 'l5bov'; el.dataset.kind = kind; OV.kind = kind; OV.data = data || null;
      const bd = mk('div', ''); bd.className = 'bd'; bd.addEventListener('click', () => { UIS('tap'); closeOv(); }); el.appendChild(bd);
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation());
      host.appendChild(el); document.body.classList.add('l5b-on'); note('ov', { kind }); return el;
    }
    function closeOv(quiet) { if (!OV.el) return false; const k = OV.kind; OV.el.remove(); OV.el = null; OV.kind = null; OV.data = null; document.body.classList.remove('l5b-on'); if (!quiet) note('ovClose', { kind: k }); return true; }
    const busy = () => !!OV.el || !!document.getElementById('l5ov') || (UI.isModalOpen && UI.isModalOpen()) || document.body.classList.contains('s2-scene');
    function panel(el, x, y, w, h, title, tid) {
      const p = mk('div', `position:absolute;left:${x}px;top:${y}px;width:${w}px;${h ? 'height:' + h + 'px;' : ''}box-sizing:border-box;${bi('panel_navy')}`, null, tid); el.appendChild(p);
      if (title) { const pl = mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:200px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;white-space:nowrap;${bi('plaque_pri')}` + TXT(24, CREAM), title, tid + '-title'); p.appendChild(pl); }
      const x0 = mk('div', `position:absolute;right:-12px;top:-14px;width:44px;height:44px;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;justify-content:center;${sp('close') || bi('close')}` + TXT(24, CREAM), sp('close') ? '' : '✕', tid + '-close');
      x0.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeOv(); }); p.appendChild(x0); return p;
    }
    // 頭像（團絨 atlas／細佬 strip）
    const TRIM = new Map();
    function trim(src) { const key = (src.img.src || '').slice(-40) + ':' + src.sx + ':' + src.sy + ':' + src.sw + ':' + src.sh; if (TRIM.has(key)) return TRIM.get(key); let r = { x: 0, y: 0, w: src.sw, h: src.sh };
      try { const c = document.createElement('canvas'); c.width = src.sw; c.height = src.sh; const g = c.getContext('2d'); g.drawImage(src.img, src.sx, src.sy, src.sw, src.sh, 0, 0, src.sw, src.sh); const d = g.getImageData(0, 0, src.sw, src.sh).data;
        let x0 = src.sw, y0 = src.sh, x1 = -1, y1 = -1; for (let y = 0; y < src.sh; y++) for (let x = 0; x < src.sw; x++) if (d[(y * src.sw + x) * 4 + 3] > 16) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
        if (x1 >= x0) r = { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 }; } catch (e) { } TRIM.set(key, r); return r; }
    function portrait(r, size, dim) {
      const c = mk('canvas', `position:relative;flex:0 0 ${size}px;width:${size}px;height:${size}px;image-rendering:pixelated;pointer-events:none;${dim ? 'filter:brightness(.45) saturate(.5);' : ''}`); c.width = size; c.height = size; let tries = 0;
      const draw = () => { const g = c.getContext('2d'); g.imageSmoothingEnabled = false; g.clearRect(0, 0, size, size); let src = null;
        if (r.kind === 'kid') { const im = SA.strip(r.fk, 'idle'); if (im && im.complete !== false && im.width) src = { img: im, sx: 0, sy: 0, sw: 48, sh: 48 }; }
        else { const a = SA.atlasSrc(r.fk, 'idle', 0, true); if (a && a.src && a.src.img && a.src.img.width) src = a.src; }
        if (!src) return false; const bb = trim(src), k = Math.max(1, Math.floor((size * 0.9) / Math.max(bb.w, bb.h))), w = bb.w * k, h = bb.h * k;
        g.drawImage(src.img, src.sx + bb.x, src.sy + bb.y, bb.w, bb.h, Math.round((size - w) / 2), Math.round((size - h) / 2), w, h); c.dataset.fk = r.fk; return true; };
      const go = () => { if (!draw() && ++tries < 16) setTimeout(go, 250); }; setTimeout(go, 0); return c;
    }
    const nm = (r) => r.name || (r.kind === 'kid' ? '細佬' : '團絨');
    const svName = (sv) => { const x = FAM.SOUV.find(q => q.id === sv); return x ? x.zh || x.name || sv : sv; };
    const hhmm = (ms) => { const m = Math.max(0, Math.ceil(ms / 60000)); return Math.floor(m / 60) + ':' + String(m % 60).padStart(2, '0'); };
    const WHY = { off: '5b 已關', who: '搵唔到佢', main: '主養唔使安排', away: '佢遠足緊', done: '今日已經安排咗', notHike: '', full: '今日遠足 2/2 滿咗', act: '揀唔到' };
    const hikeWhy = (r) => (r.kind === 'kid' ? '細佬要大到 S6 先去得遠足' : '團絨要到靜光先去得遠足');

    // ── 每日安排 ──
    function planView() {
      const s = S(), P = B.plan(s, now()), o = B.st(s), el = ov('plan'); const pn = panel(el, 8, 214, 374, 0, '今日安排', 'l5b-plan'); pn.style.bottom = '40px'; pn.style.height = 'auto';
      const chips = mk('div', 'position:absolute;left:12px;right:12px;top:34px;display:flex;gap:8px;justify-content:center'); pn.appendChild(chips);
      const chip = (icn, t, tid) => { const c = mk('div', `position:relative;flex:1 1 auto;min-height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:4px;padding:2px 4px;white-space:nowrap;${bi('chip')}` + TXT(24, CREAM), null, tid); c.appendChild(img(icn, 'position:relative;width:26px;height:26px;flex:0 0 26px')); c.appendChild(mk('span', 'position:relative', t)); return c; };
      chips.appendChild(chip(ui5b('icon_expedition'), '遠足 ' + P.ex + '/' + P.exMax, 'l5b-chip-ex'));
      chips.appendChild(chip(ui5b('icon_shards'), '今日 ' + P.sh + '/' + P.shMax + ' 碎', 'l5b-chip-sh'));
      const sc = mk('div', 'left:10px;right:10px;top:90px;bottom:70px', null, 'l5b-rows'); sc.className = 'scr'; pn.appendChild(sc);
      if (!P.rows.length) sc.appendChild(mk('div', 'position:relative;padding:40px 16px;text-align:center;' + TXT(24, SUB), '屋企未有成年住客。揀新蛋養大咗，佢就會住入屋、可以遠足同返工。', 'l5b-empty'));
      for (const r of P.rows) {
        const row = mk('div', bi('card'), null, 'l5b-row-' + r.id); row.className = 'l5bprow'; row.dataset.a = r.a; sc.appendChild(row);
        const pc = mk('div', 'position:relative;flex:0 0 64px;width:64px;height:64px;align-self:flex-start'); pc.appendChild(portrait(r, 64, !!r.away)); row.appendChild(pc);
        if (r.away) pc.appendChild(img(ui5b('icon_expedition'), 'right:-6px;bottom:-6px;width:32px;height:32px'));
        if (r.a === 'job' && r.info) pc.appendChild(img(ui5b('badge_job_lv' + Math.min(6, Math.max(1, r.info.lv))), 'left:-6px;top:-6px;width:28px;height:28px'));
        const col = mk('div', 'position:relative;flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:4px'); row.appendChild(col);
        col.appendChild(mk('div', 'position:relative;' + TXT(24, GOLD), nm(r), 'l5b-name-' + r.id));
        const segs = mk('div', 'position:relative;display:flex;gap:4px'); col.appendChild(segs);
        const SEG = [['expedition', '遠足', 'icon_expedition', '#E8893A'], ['job', '工作', r.job ? 'icon_job_' + r.job : 'icon_job_post', '#2F95A8'], ['rest', '休息', 'icon_rest', '#7E66C4']];
        for (const [a, zh, ic, on] of SEG) {
          const lk = r.lock[a] && r.a !== a, sel = r.a === a, sg = mk('div', (sel ? `background:${on};border:3px solid ${GOLD};border-radius:8px;box-shadow:0 3px 0 #24172C;` : lk ? 'background:#4A4656;border:2px solid #6E6A7A;border-radius:8px;' : 'background:#1E1A3E;border:2px solid #8A80C0;border-radius:8px;') + TXT(24, lk ? '#D9D2E6' : CREAM), null, 'l5b-seg-' + a + '-' + r.id); sg.className = 'l5bseg' + (lk ? ' lk' : ''); sg.dataset.on = sel ? '1' : '0'; sg.dataset.lk = lk ? '1' : '0';
          sg.appendChild(img(ui5b(ic), 'position:relative;width:24px;height:24px;flex:0 0 24px;' + (lk ? 'filter:grayscale(1) brightness(.8);' : ''))); sg.appendChild(mk('span', 'position:relative;white-space:nowrap', zh)); segs.appendChild(sg);
          sg.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap');
            if (lk) { const why = r.away ? '佢遠足緊，' + hhmm(r.away.left) + ' 後返嚟' : a === 'expedition' && !r.hike ? hikeWhy(r) : a === 'expedition' && P.ex >= P.exMax ? WHY.full : WHY.done; toast(why, 1800); return; }
            if (a === 'job') return jobsView(r.id);
            if (sel && a !== 'expedition') return;
            act(r.id, a); });
        }
        col.appendChild(mk('div', 'position:relative;' + TXT(24, SUB), statusOf(r, o), 'l5b-st-' + r.id));
      }
      const ok = btn('好！', 'btn_pri', 170, 46, 'l5b-ok', () => closeOv()); ok.style.left = '98px'; ok.style.bottom = '12px'; pn.appendChild(ok);
      return { ok: true, rows: P.rows.length };
    }
    function statusOf(r, o) {
      if (r.away) return '遠足中・仲有 ' + hhmm(r.away.left);
      if (r.a === 'job' && r.info) { const i = r.info; return i.zh + ' Lv' + i.lv + '・' + (i.capped ? (i.lv6Locked ? '家族 Lv7 開 Lv6' : '最高級') : '再做 ' + i.toNext + ' 日升級') + (r.paid ? '・今日 +' + i.pay + ' 碎' : r.job === 'watch' ? '・夜晚先出糧' : ''); }
      if (r.done === 'expedition') return '啱啱遠足返・休息緊 zZ';
      if (!o.plan[r.id]) return r.hike ? '未揀' : '未揀・' + (r.kind === 'kid' ? '大到 S6 先去得遠足' : '靜光先去得遠足');
      return '休息緊 zZ';
    }
    function act(id, a, job) {
      const s = S(), r = B.choose(s, id, a, job, now()); note('choose', { id, a, job, ok: r.ok, reason: r.reason });
      if (!r.ok) { toast(WHY[r.reason] || (r.reason === 'notHike' ? hikeWhy(FAM.st(s).res.find(q => q.id === id) || {}) : '揀唔到'), 1800); return r; }
      handle(r.ev || []); save(); if (OV.kind === 'plan' || OV.kind === 'jobs') planView(); refreshHouse(); return r;
    }

    // ── 揀工作 2×2 ──
    function jobsView(id) {
      const s = S(), r = B.residents(s).find(q => q.id === id); if (!r) return { ok: false };
      const cur = B.st(s).plan[id], el = ov('jobs', { id }), pn = panel(el, 20, 214, 350, 0, '揀工作', 'l5b-jobs'); pn.style.height = 'auto'; pn.style.paddingBottom = '14px';
      pn.appendChild(mk('div', 'position:relative;margin:30px 14px 8px;text-align:center;' + TXT(24, GOLD), nm(r) + '今日做咩？'));
      const grid = mk('div', 'position:relative;display:flex;flex-wrap:wrap;gap:10px;justify-content:center;padding:0 10px'); pn.appendChild(grid);
      for (const j of B.JOB_IDS) {
        const i = B.jobInfo(s, id, j), sel = cur && cur.a === 'job' && cur.job === j, c = mk('div', bi(sel ? 'card_sel' : 'card'), null, 'l5b-job-' + j); c.className = 'l5bjc'; c.dataset.lv = i.lv; grid.appendChild(c);
        const md = mk('div', `position:relative;width:72px;height:72px;flex:0 0 72px;box-sizing:border-box;${bi('med40_gold')}`); md.appendChild(img(ui5b('icon_job_' + j), 'left:50%;top:50%;width:54px;height:54px;transform:translate(-50%,-50%)'));
        if (!i.never) md.appendChild(img(ui5b('badge_job_lv' + Math.min(6, i.lv)), 'right:-12px;top:-8px;width:32px;height:32px')); c.appendChild(md);
        c.appendChild(mk('div', 'position:relative;text-align:center;' + TXT(24, CREAM), i.zh));
        c.appendChild(mk('div', 'position:relative;text-align:center;' + TXT(24, GOLD), i.never ? '未做過' : 'Lv' + i.lv));
        const bar = mk('div', `position:relative;width:118px;height:12px;box-sizing:border-box;${bi('bar_trough_h7')}`); bar.appendChild(mk('div', `position:absolute;left:0;top:0;bottom:0;width:${Math.round(i.pct * 100)}%;background:${i.capped ? GOLD : '#6FE0D0'};border-radius:4px`)); c.appendChild(bar);
        c.appendChild(mk('div', 'position:relative;text-align:center;' + TXT(24, i.lv6Locked ? '#FFC2D0' : SUB), i.lv6Locked ? '家族 Lv7 開 Lv6' : '+' + i.pay + ' 碎/日', 'l5b-job-pay-' + j));
        c.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); if (sel) { closeOv(); return planView(); } const rr = act(id, 'job', j); if (rr && rr.ok && OV.kind !== 'plan') planView(); });
      }
      pn.appendChild(mk('div', 'position:relative;margin:12px 14px 0;text-align:center;' + TXT(24, SUB), '做滿 5 日升 1 級・每日最多 12 碎'));
      return { ok: true };
    }

    // ── 團絨日記 ──
    function diaryView(ix) {
      const o = B.st(S()), N = o.trips.length; ix = N ? Math.max(0, Math.min(N - 1, ix == null ? N - 1 : ix)) : 0;
      const el = ov('diary', { ix }), pn = mk('div', `position:absolute;left:24px;top:206px;width:342px;box-sizing:border-box;padding:30px 16px 12px;background:#FFF3DA;border:4px solid #8A5A34;border-radius:12px;box-shadow:0 6px 0 #24172C`, null, 'l5b-diary'); el.appendChild(pn);
      const pl = mk('div', `position:absolute;left:50%;top:-22px;transform:translateX(-50%);min-width:200px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;padding:0 14px;${bi('plaque_pri')}` + TXT(24, CREAM), '團絨日記', 'l5b-diary-title'); pn.appendChild(pl);
      const x0 = mk('div', `position:absolute;right:-12px;top:-14px;width:44px;height:44px;box-sizing:border-box;cursor:pointer;display:flex;align-items:center;justify-content:center;${sp('close') || bi('close')}` + TXT(24, CREAM), sp('close') ? '' : '✕', 'l5b-diary-close'); x0.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); closeOv(); }); pn.appendChild(x0);
      const tx = (t, c, tid, ex) => mk('div', 'position:relative;text-align:center;' + TXT(24, c || INK, ex), t, tid);
      if (!N) { pn.appendChild(tx('仲未有遠足日記。', INK, 'l5b-diary-empty')); pn.appendChild(tx('喺「今日安排」揀一隻靜光團絨或者 S6 細佬去遠足啦！', '#5A3E5C')); }
      else {
        const t = o.trips[ix]; pn.dataset.ix = ix;
        pn.appendChild(tx('第 ' + t.day + ' 日・' + t.name + '嘅遠足', INK, 'l5b-diary-date'));
        const cv = mk('canvas', 'position:relative;display:block;margin:8px auto;width:302px;height:224px;image-rendering:pixelated;border:3px solid #8A5A34;border-radius:6px;box-sizing:content-box', null, 'l5b-diary-pic'); cv.width = 151; cv.height = 112; pn.appendChild(cv); drawPic(cv, t);
        for (let i = 0; i < 3; i++) pn.appendChild(tx(t.lines[i] || '', INK, 'l5b-diary-l' + i));
        const loot = mk('div', 'position:relative;display:flex;flex-wrap:wrap;gap:6px;justify-content:center;align-items:center;margin-top:8px'); pn.appendChild(loot);
        loot.appendChild(img(medal(t.sv), 'position:relative;width:48px;height:48px;flex:0 0 48px'));
        const ch = (icn, s, tid) => { const c = mk('div', `position:relative;display:flex;align-items:center;gap:4px;min-height:40px;padding:2px 8px;box-sizing:border-box;${bi('chip')}` + TXT(24, CREAM), null, tid); if (icn) c.appendChild(img(icn, 'position:relative;width:26px;height:26px')); c.appendChild(mk('span', 'position:relative', s)); return c; };
        loot.appendChild(ch(ui5b('icon_shards'), '+' + t.sh, 'l5b-diary-sh'));
        if (t.furn) loot.appendChild(ch(null, '家具：' + svName(t.furn), 'l5b-diary-furn'));
        const nav = mk('div', 'position:relative;display:flex;align-items:center;justify-content:space-between;margin-top:10px'); pn.appendChild(nav);
        const nb = (lab, d, tid) => { const b = btn(lab, ix + d < 0 || ix + d >= N ? 'btn16_dis' : 'btn16_sec', 56, 44, tid, () => { if (ix + d >= 0 && ix + d < N) diaryView(ix + d); }); b.style.position = 'relative'; if (ix + d < 0 || ix + d >= N) b.dataset.dis = '1'; return b; };
        nav.appendChild(nb('◀', -1, 'l5b-diary-prev')); nav.appendChild(tx((ix + 1) + ' / ' + N, INK, 'l5b-diary-n')); nav.appendChild(nb('▶', 1, 'l5b-diary-next'));
      }
      const got = B.STICKERS.filter(k => o.stk[k]); const sk = mk('div', 'position:relative;margin-top:12px;padding-top:8px;border-top:2px dashed #C9A27A;display:flex;flex-wrap:wrap;gap:4px;justify-content:center;align-items:center', null, 'l5b-stk'); pn.appendChild(sk);
      sk.appendChild(tx('守夜貼紙 ' + got.length + '/' + B.STICKERS.length, INK, 'l5b-stk-n', 'width:100%'));
      for (const k of B.STICKERS) sk.appendChild(img('art/series2/ui/dream_bubbles/' + k + '@3x.png', 'position:relative;width:32px;height:32px;' + (o.stk[k] ? '' : 'filter:brightness(0) opacity(.18);')));
      return { ok: true, ix, n: N };
    }
    function drawPic(cv, t) {
      const g = cv.getContext('2d'); let tries = 0; const SX = 36, SY = 200;
      const go = () => { g.imageSmoothingEnabled = false; g.clearRect(0, 0, 151, 112); let miss = 0;
        for (const l of ['sky', 'far', 'mid']) { const i = imI('art/hd2d/' + t.scene + '/' + l + '.png'); if (i) g.drawImage(i, SX, SY, 151, 112, 0, 0, 151, 112); else miss++; }
        const f = J5 && J5.ex.forms[t.fk], c = f && f.return, I = c && imI(LB5 + c.png), s1 = imI(sv1(t.sv));
        if (I) { const X = 75 - c.pivot[0], Y = 104 - c.pivot[1]; g.drawImage(I, 9 * c.frameW, 0, c.frameW, c.frameH, X, Y, c.frameW, c.frameH);
          if (s1) { const ht = f.headTop || [c.frameW / 2, 18]; g.drawImage(s1, Math.round(X + ht[0] - s1.width / 2), Math.round(Y + ht[1] - 10 - s1.height), s1.width, s1.height); } } else miss++;
        if (miss && ++tries < 20) setTimeout(go, 200); };
      go();
    }

    // ── 返屋 toast ──
    const TQ = { el: null, until: 0, shown: 0 };
    function showToast(item) {
      if (!item) return false; if (TQ.el) TQ.el.remove(); const host = document.getElementById('ui') || document.body;
      const el = TQ.el = mk('div', bi('panel_navy'), null, 'l5b-toast'); el.id = 'l5btoast'; host.appendChild(el);
      const md = mk('div', 'position:relative;flex:0 0 60px;width:60px;height:60px'); md.appendChild(img(medal(item.sv), 'left:0;top:0;width:60px;height:60px')); el.appendChild(md);
      const col = mk('div', 'position:relative;flex:1 1 auto;min-width:0'); el.appendChild(col);
      col.appendChild(mk('div', 'position:relative;' + TXT(24, GOLD), item.name + '返嚟喇！'));
      col.appendChild(mk('div', 'position:relative;' + TXT(24, CREAM), '帶咗' + svName(item.sv) + (item.furn ? '・新家具' : '')));
      const sh = mk('div', `position:relative;flex:0 0 auto;display:flex;align-items:center;gap:2px;padding:2px 6px;min-height:40px;box-sizing:border-box;${bi('chip')}` + TXT(24, CREAM)); sh.appendChild(img(ui5b('icon_shards'), 'position:relative;width:24px;height:24px')); sh.appendChild(mk('span', 'position:relative', '+' + item.n)); el.appendChild(sh);
      el.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); hideToast(); const o = B.st(S()); let ix = -1; for (let i = o.trips.length - 1; i >= 0; i--) if (o.trips[i].id === item.id && o.trips[i].sv === item.sv) { ix = i; break; } diaryView(ix < 0 ? null : ix); });
      requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('in'))); TQ.until = pnow() + 260 + 2600; TQ.shown++; note('toast', { id: item.id, sv: item.sv }); return true;
    }
    function hideToast() { if (!TQ.el) return; const el = TQ.el; TQ.el = null; el.classList.remove('in'); setTimeout(() => el.remove(), 280); }

    // ── 屋仔：HUD 掣、出發／返屋動畫、工作帽 ──
    const AN = new Map(), STAT = { hats: 0, anims: 0, drawn: 0, sv: 0 };
    const showAway = (id) => AN.has(id);
    function refreshHouse() { const h = H5(); if (h && h.isOpen()) try { h.refresh(); } catch (e) { } }
    const deco = () => !!(window.__qa && __qa.house && __qa.house.st && __qa.house.st().deco);
    G.l5bHud = function (hud) {
      if (!hud) return; let b = hud.querySelector('#l5bhud'); const s = S(), n = B.residents(s).length, show = n > 0 && !deco();
      if (!b) { b = mk('div', `${bi('med40_gold')}`, null, 'l5b-hud'); b.id = 'l5bhud';
        b.appendChild(img(ui5b('icon_expedition'), 'left:50%;top:44%;width:44px;height:44px;transform:translate(-50%,-50%)'));
        b.appendChild(mk('div', 'position:absolute;left:50%;bottom:-6px;transform:translateX(-50%);white-space:nowrap;padding:0 4px;' + TXT(24, CREAM), '安排', 'l5b-hud-label'));
        b.appendChild(mk('div', 'position:absolute;right:-4px;top:-4px;width:16px;height:16px;border-radius:50%;background:#E4566E;border:2px solid #FFF5DC;display:none;animation:l5bdot 1.2s ease-in-out infinite', null, 'l5b-hud-dot'));
        b.addEventListener('click', (e) => { e.stopPropagation(); UIS('tap'); planView(); }); b.addEventListener('pointerdown', (e) => e.stopPropagation()); hud.appendChild(b); }
      b.style.display = show ? 'block' : 'none'; const o = B.st(s), dot = b.lastChild; dot.style.display = show && B.residents(s).some(r => !o.plan[r.id] && !o.away[r.id]) ? 'block' : 'none';
    };
    G.h5x = {
      hide: (id) => { const s = S(); return !!(s && B.isOn() && B.st(s).away[id]) && !showAway(id); },
      draw(x, p, tint, tinted) {
        const a = AN.get(p.id); if (!a || !J5) return false; const fm = J5.ex.forms[p.fk], c = fm && fm[a.k]; if (!c) { AN.delete(p.id); return false; }
        const I = imI(LB5 + c.png); if (!I) { if (pnow() - a.t0 > 3000) AN.delete(p.id); return false; } if (!a.go) { a.go = pnow(); p.mode = 'clip'; p.tgt = null; p.dir = 1; }
        p.until = pnow() + 400; const f = Math.floor((pnow() - a.go) / 120);
        if (f >= 10) { AN.delete(p.id); p.dx = 0; p.mode = 'idle'; note('animEnd', { id: p.id, k: a.k }); if (a.k === 'depart') { p.box = null; refreshHouse(); return true; } return false; }
        const dx = a.k === 'depart' ? (f > 3 ? (f - 3) * 2 : 0) : (f < 4 ? (4 - f) * 2 : 0), al = a.k === 'depart' && f >= 7 ? Math.max(0, 1 - (f - 6) / 3.5) : 1; p.dx = dx;
        const X0 = Math.round(p.x + dx), Y0 = Math.round(p.y); x.save(); x.globalAlpha = al; x.drawImage(tinted ? tinted(I, tint) : I, f * c.frameW, 0, c.frameW, c.frameH, X0 - c.pivot[0], Y0 - c.pivot[1], c.frameW, c.frameH); x.restore();
        p.at = [X0, Y0, 1, f, c.pivot[0], c.pivot[1]]; p.box = [X0 - 14, Y0 - 40, X0 + 14, Y0]; p.last = { clip: a.k, frame: f }; a.f = f; a.al = al; STAT.anims++;
        if (a.k === 'return' && a.sv && f >= J5.sor.frames[0]) { const s1 = imI(sv1(a.sv)); if (s1) { const ht = fm.headTop || [c.frameW / 2, 18], bob = J5.sor.bobPx[Math.min(J5.sor.bobPx.length - 1, f - J5.sor.frames[0])] || 0;
          x.drawImage(s1, Math.round(X0 - c.pivot[0] + ht[0] - s1.width / 2), Math.round(Y0 - c.pivot[1] + ht[1] + J5.sor.dy - s1.height + bob)); STAT.sv++; } }
        return true;
      },
      post(x, p, tint, tinted) {
        if (!J5 || !p.at || !B.isOn()) return; const s = S(), pl = B.st(s).plan[p.id]; if (!pl || pl.a !== 'job') return; const jf = J5.jobs.forms[p.fk], hj = jf && jf[pl.job]; if (!hj) return;
        const a = AN.get(p.id); if (a && a.f == null) return; const lv = B.jobInfo(s, p.id, pl.job).lv, tier = lv >= 6 ? 't4' : lv >= 5 ? 't3' : lv >= 3 ? 't2' : 't1';
        const c0 = a ? a.k : (p.last && p.last.clip) || 'idle', TRC = ['sit', 'prank_do', 'prank_got', 'interact'], KC = ['walk', 'sleep', 'sit', 'prank_do', 'prank_got', 'interact', 'cry', 'eat'];
        const clip = a ? a.k : p.kind === 'tr' ? (TRC.includes(c0) ? c0 : 'base') : (KC.includes(c0) ? c0 : 'idle');
        const rw = hj.rows.find(q => q.tier === tier && q.clip === clip) || hj.rows.find(q => q.tier === tier && (q.clip === 'base' || q.clip === 'idle')); const I = imI(LB5 + hj.png); if (!rw || !I) return;
        const fr = clip === 'base' ? 0 : Math.max(0, Math.min(rw.frames - 1, p.at[3] | 0)); x.save(); x.globalAlpha = a && a.al != null ? a.al : 1; x.translate(p.at[0], p.at[1]); x.scale(p.at[2] < 0 ? -1 : 1, 1);
        x.drawImage(tinted ? tinted(I, tint) : I, fr * rw.frameW, rw.y, rw.frameW, rw.frameH, -rw.pivot[0], -rw.pivot[1], rw.frameW, rw.frameH); x.restore(); STAT.hats++;
      },
    };
    function animate(id, k, sv) { const h = H5(); if (!h || !h.isOpen()) return false; const r = FAM.st(S()).res.find(q => q.id === id); if (!r || r.room !== h.room()) return false; AN.set(id, { k, sv, t0: pnow() }); refreshHouse(); note('anim', { id, k }); return true; }

    // ── 事件 ──
    const T = { n: 0, last: 0, boot: true, evs: [] };
    function handle(ev) {
      for (const e of ev) { T.evs.push(Object.assign({ at: Math.round(pnow()) }, e)); if (T.evs.length > 60) T.evs.shift();
        if (e.what === 'depart') { animate(e.id, 'depart'); if (!QUIET) toast(e.name + '出發去遠足！聽日返嚟', 2000); }
        else if (e.what === 'back') { animate(e.id, 'return', e.sv); }
        else if (e.what === 'pay' && !QUIET) toast(e.name + '做' + B.JOB[e.job].zh + '：+' + e.n + ' 碎' + (e.n < e.want ? '（今日到頂 12）' : ''), 2000);
        else if (e.what === 'lvUp' && !QUIET) toast(e.name + '嘅' + B.JOB[e.job].zh + '升到 Lv' + e.lv + '！', 2400);
        else if (e.what === 'perk' && !QUIET) toast(e.stk ? '守夜發咗個夢：' + e.stkName + '貼紙' : e.decor ? '園丁搵到花園擺設：' + e.decorName : '郵差幫手：委託進度 +1', 2400);
      }
    }
    function tick(force) {
      const t = pnow(); if (!force && t - T.last < 1000) return; T.last = t; const s = S(); if (!s || !s.fam) return; T.n++;
      let ev; try { ev = B.scan(s, now(), { boot: T.boot }); } catch (e) { note('scanErr', { e: String(e && e.message || e) }); return; } T.boot = false;
      if (ev.length) { handle(ev); save(); refreshHouse(); if (OV.kind === 'plan') planView(); }
      if (TQ.el && pnow() > TQ.until) hideToast();
      if (!QUIET && !TQ.el && !busy()) { const o = B.st(s); if (o.q.length) showToast(o.q.shift()), save(); }
    }
    const s2t = G.s2Tick; G.s2Tick = function () { const r = s2t ? s2t.apply(this, arguments) : undefined; try { tick(); } catch (e) { note('tickErr', { e: String(e && e.message || e) }); } return r; };
    setTimeout(() => { try { tick(true); } catch (e) { } }, 700);

    // ── 🛠 開發者模式「5b」 ──
    const prep = (n) => { const q = window.__qa && __qa.l5; if (!q) return { ok: false, msg: '冇 5a' }; const D = q.dev(), it = D.items.find(i => i.k === 'prep'); const e = it && it.run(); if (e && e.ok === false) return e;
      const s = S(); let k = 0; while (B.residents(s).length < (n || 3) && k++ < 6) if (!q.addRes(B.residents(s).length % 2 ? 'kid' : 'tr', H5() && H5().isOpen() ? H5().room() : null)) break; save(); return null; };
    const houseIn = () => { const h = H5(); if (!h) return { ok: false, msg: '冇屋仔' }; if (!h.isOpen() && !h.open()) return { ok: false, msg: '開唔到屋仔' }; return null; };
    const firstHiker = () => { const s = S(), P = B.plan(s, now()), h = H5(), rm = h && h.isOpen() ? h.room() : null; return P.rows.find(r => r.hike && !r.lock.expedition && (!rm || r.room === rm)) || P.rows.find(r => r.hike && !r.lock.expedition); };
    const firstRes = () => { const h = H5(), rm = h && h.isOpen() ? h.room() : null, xs = B.plan(S(), now()).rows.filter(r => !r.away); return xs.find(r => !rm || r.room === rm) || xs[0]; };
    const nightAt = () => { const d = new Date(now()); if (!B.isNight(now())) d.setHours(22, 0, 0, 0); return d.getTime(); };
    const DEV = { id: 'l5b', title: '5b（遠足＋小職業）', order: 43,
      status: () => { const s = S(), m = B.summary(s, now()); return '遠足 ' + m.ex + '/2・今日 ' + m.sh + '/12 碎・遠足中 ' + m.away.length + '・日記 ' + m.trips + '・貼紙 ' + m.stk.length + '/8'; },
      items: [
        ['prep', '準備：屋企有 3 隻成年住客（開屋）', () => { const e = prep(3) || houseIn(); if (e) return e; refreshHouse(); return { ok: true, msg: '住客 ' + B.residents(S()).length + ' 隻' }; }],
        ['plan', '開「今日安排」', () => { const e = prep(1); if (e) return e; planView(); return { ok: true, msg: '今日安排' }; }],
        ['hike', '第 1 隻可遠足嘅即刻出發', () => { const e = prep(3) || houseIn(); if (e) return e; const r = firstHiker(); if (!r) return { ok: false, msg: '冇可遠足嘅（今日 2/2 或者冇靜光／S6）' }; const h = H5(); if (h.room() !== r.room) h.goRoom(r.room, true); const x = act(r.id, 'expedition'); return x.ok ? { ok: true, msg: r.name + '出發遠足' } : { ok: false, msg: WHY[x.reason] || x.reason }; }],
        ['back', '遠足即刻返屋（當 24 小時過咗）', () => { const s = S(); if (!Object.keys(B.st(s).away).length) return { ok: false, msg: '冇人遠足緊' }; const ev = B.devReturn(s, null, now()); handle(ev); save(); refreshHouse(); return { ok: true, msg: ev.length + ' 隻返嚟' }; }],
        ['job', '第 1 隻揀工作（開揀工作）', () => { const e = prep(3); if (e) return e; const r = firstRes(); if (!r) return { ok: false, msg: '冇住客' }; jobsView(r.id); return { ok: true, msg: r.name + '揀工作' }; }],
        ['hats', '全部住客返工（戴帽：郵差／園丁／守夜／廚師）', () => { const e = prep(3) || houseIn(); if (e) return e; const s = S(); let n = 0; B.devNewDay(s, now()); B.plan(s, now()).rows.forEach((r, i) => { if (!r.away && B.choose(s, r.id, 'job', B.JOB_IDS[i % 4], now()).ok) n++; }); save(); refreshHouse(); return { ok: true, msg: n + ' 隻返工' }; }],
        ['days5', '而家做緊嘅工作 +5 日（升 1 級）', () => { const s = S(), o = B.st(s); let n = 0, lv = 0; for (const id in o.plan) if (o.plan[id].a === 'job') { lv = B.devDays(s, id, o.plan[id].job, 5).lv; n++; } save(); refreshHouse(); return n ? { ok: true, msg: n + ' 隻 +5 日（Lv' + lv + '）' } : { ok: false, msg: '冇人返工' }; }],
        ['lv5', '工作去到 Lv5（家族 Lv7 前封頂）', () => { const s = S(), o = B.st(s); let n = 0; for (const id in o.plan) if (o.plan[id].a === 'job') { const J = o.jobs[id] || (o.jobs[id] = {}); J[o.plan[id].job] = Math.max(J[o.plan[id].job] | 0, 20); n++; } save(); refreshHouse(); return n ? { ok: true, msg: n + ' 隻 Lv5' } : { ok: false, msg: '冇人返工' }; }],
        ['fam7', '家族 Lv7（開工作 Lv6）', () => { const q = window.__qa && __qa.l5; if (!q) return { ok: false, msg: '冇 5a' }; q.xpTo(7); const s = S(), o = B.st(s); for (const id in o.plan) if (o.plan[id].a === 'job') { const J = o.jobs[id] || (o.jobs[id] = {}); J[o.plan[id].job] = Math.max(J[o.plan[id].job] | 0, 25); } save(); refreshHouse(); return { ok: true, msg: '家族 Lv' + FAM.st(s).lv }; }],
        ['night', '守夜：當而家係夜晚出糧', () => { const s = S(), ev = B.scan(s, nightAt(), {}); handle(ev); save(); refreshHouse(); const st = ev.filter(e => e.stk).length; return { ok: true, msg: ev.filter(e => e.what === 'pay').length + ' 份糧' + (st ? '・' + st + ' 張貼紙' : '') }; }],
        ['diary', '開「團絨日記」', () => { diaryView(); return { ok: true, msg: '日記 ' + B.st(S()).trips.length + ' 篇' }; }],
        ['toast', '返屋 toast 預覽', () => { const o = B.st(S()), t = o.trips[o.trips.length - 1]; showToast(t ? { id: t.id, name: t.name, sv: t.sv, n: t.sh, furn: t.furn } : { id: 'demo', name: '滴滴', sv: 'sv_pinecone', n: 7, furn: 'sv_pinecone' }); return { ok: true, msg: 'toast' }; }],
        ['newday', '換日（重設今日安排同上限）', () => { const s = S(); B.devNewDay(s, now()); const o = B.st(s); for (const id in o.plan) if (o.plan[id].a !== 'job') delete o.plan[id]; save(); refreshHouse(); return { ok: true, msg: '新一日' }; }],
        ['reset', '重設 5b（清遠足／工作資料）', () => { const s = S(); if (s.fam) delete s.fam.b5; B.st(s); AN.clear(); closeOv(true); hideToast(); save(); refreshHouse(); return { ok: true, msg: '5b 資料清咗' }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.l5b = { plan: planView, jobs: jobsView, diary: diaryView, close: () => closeOv(), open: () => OV.kind, tick: () => tick(true) };
    window.__qa = window.__qa || {};
    window.__qa.l5b = {
      st: () => Object.assign(B.summary(S(), now()), { ov: OV.kind, ovData: OV.data, quiet: QUIET, ticks: T.n, toast: !!TQ.el, toastN: TQ.shown, anims: [...AN.keys()], stat: Object.assign({}, STAT), json: !!J5, q: B.st(S()).q.length }),
      plan: planView, jobs: jobsView, diary: diaryView, toast: showToast, close: () => closeOv(), choose: (id, a, j) => act(id, a, j), rows: () => B.plan(S(), now()).rows,
      back: (id) => { const ev = B.devReturn(S(), id, now()); handle(ev); save(); refreshHouse(); return ev; }, tick: () => tick(true), log: () => log.slice(), evs: () => T.evs.slice(), toasts: () => toasts.slice(), dev: () => DEV, raw: () => JSON.parse(JSON.stringify(B.st(S()))) };
    return true;
  }
  return { install };
});
