/* 《微光小圃》 ui62.js — 6b.2「UI 打磨」（Kurt 親口反饋）。原創代碼；只作用喺 v2 UI（#ui.hd.v2），v1 舊 UI 停更唔改。
   ① 畫面中間講嘢句唔會消失：心聲／記憶句／6a 招呼（全部經 G.say）按字數計時（3.5 秒起，長句每字 +0.12 秒，最長 9 秒）淡出，撳一下即閂；
      狀態氣泡 #bubble（zZz…／好肚餓…／縮埋一角…）以前條件成立就一直企喺度 → 出 dur 秒後淡出，45 秒後狀態仍然係咁先再提一次；撳一下即閂。屋仔底提示 6 秒淡出。
   ② 字級：標題 FP12 24px（字距 2px）；面板內文改系統中文字 18px／行高 26；輔助字 16px／行高 22（readPass 喺 hd2dui2 跟 U.t62 分流）。HUD（名牌、rail、底掣）照用 FP12。
   ③ 間距尺 4／8／12／16；面板：半透明深色底＋模糊、細金邊＋內發光、四角簡單角飾、柔和陰影、圓角 14；打開淡入＋上移 8px。
   ④ toast／星碎提示排喺 HUD 之下、rail 左邊（唔再壓住 🛠 開發者同委託 rail）；__qa.ui62.overlap() 量兩兩可見 UI 框重疊（e2e-6b2 用）。
   ⑤ 左上頭像跟寵物而家畫緊嗰幀（hd2dui2 U.live62，10fps）。
   ⑦ 每個 rail／掣有字；每個面板標題下一句用途說明；每個功能第一次打開出一次性小提示（可閂；🛠「6b.2」可重置；localStorage glimmer.tips62）。
   ⑧ 「工作」主畫面喺 work62.js。?ui62=0 全停（返 6b.1 樣）。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.ui62 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  // 講嘢句幾耐：3.5 秒起；10 個字以上每字 +0.12 秒；最長 9 秒（純函數，unit 測）
  function speechSec(line) { const n = String(line || '').replace(/\s+/g, '').length; return Math.round(Math.min(9, 3.5 + Math.max(0, n - 10) * 0.12) * 100) / 100; }
  const SUB = {   // 面板用途說明（標題 → 一句）
    '日記': '睇返團絨每日嘅小事同記憶，未領嘅獎喺度領。', '圖鑑': '見過嘅形態、細佬同家具都記低喺度。', '細佬': '細佬嘅成長、心情同照顧方法。',
    '設定': '聲音、畫面同提示嘅開關。', '買家具': '用星星碎買家具，擺入屋仔。', '散步路': '真實行路儲步數，每 1000 步行一格，每日最多 5 粒碎。',
    '屋仔': '擺家具、睇住客；撳房門轉房。', '今日安排': '幫每隻住客揀今日：遠足、工作定休息。', '揀工作': '揀一份工，每日出糧，做得耐會升級。',
    '團絨日記': '遠足返嚟寫低嘅遊記同貼紙。', '工作': '返緊工嘅寵物：做緊乜、賺幾多、幾時收工。', '你不在時發生咗咩': '你離開咗嘅時候，團絨經歷咗呢啲。',
    '委託': '幫街坊做小事，完成有星星碎同徽章。', '家族': '家族等級、房間同族譜。', '🛠 開發者模式': '測試用掣，正式玩唔使理。',
  };
  const TIPS = {   // 第一次打開功能：一次性小提示
    diary: ['日記', '團絨每日會寫低小事；有紅點即係有獎未領，記得 2 日內領。'],
    dex: ['圖鑑', '每隻見過嘅形態都會亮起，未見過嘅係剪影，慢慢儲齊佢。'],
    kid: ['細佬', '細佬會跟團絨學嘢；每日陪佢玩、餵佢，佢就大得快。'],
    settings: ['設定', '聲音大細、震動同提示都喺度調；改完即時生效。'],
    shop: ['買家具', '撳家具睇價錢，夠星星碎就買得；買咗喺「佈置」擺。'],
    walk: ['散步路', '開咗計步，每行 1000 步團絨就行一格；權限可以唔開，唔影響遊戲。'],
    house: ['屋仔', '撳「佈置」擺家具；左上「返回」返花園；底下係住客同今日安排。'],
    plan: ['今日安排', '每隻住客揀一樣：遠足（24 小時返嚟）、工作（每日出糧）或者休息。'],
    work: ['工作', '呢度見到返緊工嘅寵物；進度條行完就收工，糧已經自動入咗袋。'],
    quest: ['委託', '街坊有小事搵你；做完 3 件有額外獎勵。'],
  };
  function install(G, NS) {
    const qs = new URLSearchParams(location.search);
    if (qs.get('ui62') === '0') return false;
    const ui = document.getElementById('ui'); if (!ui) return false;
    const U = () => G.ui2 || null, on = () => !!(U() && U().on && ui.classList.contains('v2'));
    const pnow = () => performance.now(), $ = (s) => document.querySelector(s);
    const log = [], note = (k, x) => { log.push(Object.assign({ k, t: Math.round(pnow()) }, x || {})); if (log.length > 120) log.shift(); };
    const FALL = '"Noto Sans HK","Noto Sans CJK TC","Noto Sans TC","PingFang HK","Microsoft JhengHei",sans-serif', FP = ((G.v3 && G.v3.want) ? '"GlimmerV3Sans",' : '"GlimmerFP12",') + FALL;   // #83 V3 → Noto Sans CJK TC
    const GOLD = '#E8C27A', CREAM = '#F7EEDB', MUTE = '#D9CFBC';
    ui.classList.add('u62');
    if (U()) { U().live62 = true; U().t62 = true; }
    // ── CSS（全部 scope 喺 #ui.hd.v2.u62）──
    const H = '#ui.hd.v2.u62 ';
    const corner = (c) => [['left 7px top 7px', '12px 1px'], ['left 7px top 7px', '1px 12px'], ['right 7px top 7px', '12px 1px'], ['right 7px top 7px', '1px 12px'],
      ['left 7px bottom 7px', '12px 1px'], ['left 7px bottom 7px', '1px 12px'], ['right 7px bottom 7px', '12px 1px'], ['right 7px bottom 7px', '1px 12px']].map(([p, z]) => `linear-gradient(${c},${c}) ${p} / ${z} no-repeat`).join(',');
    const PANEL = `border-image:none !important; border:1px solid rgba(232,194,122,.72) !important; border-radius:14px !important;
      background:${corner('rgba(240,206,140,.85)')}, radial-gradient(120% 70% at 50% 0%, rgba(120,110,170,.20), rgba(0,0,0,0) 60%), linear-gradient(180deg, rgba(30,33,60,.86), rgba(15,17,34,.90)) !important;
      -webkit-backdrop-filter:blur(6px); backdrop-filter:blur(6px);
      box-shadow:inset 0 0 0 1px rgba(255,240,205,.07), inset 0 0 22px rgba(232,194,122,.16), 0 12px 30px rgba(0,0,0,.42), 0 2px 6px rgba(0,0,0,.30) !important;`;
    const css = document.createElement('style'); css.id = 'ui62css';
    css.textContent = `
#ui.u62 { --s1:4px; --s2:8px; --s3:12px; --s4:16px; }
@keyframes u62in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
@keyframes u62fade { from { opacity:0; } to { opacity:1; } }
${H}#modal { -webkit-backdrop-filter:blur(2px); backdrop-filter:blur(2px); }
${H}#mbox { ${PANEL} padding:40px var(--s4) var(--s4) !important; animation:u62in 220ms cubic-bezier(.2,.8,.2,1); }
${H}#mbox > h2 { letter-spacing:2px !important; text-shadow:0 2px 6px rgba(0,0,0,.45); }
${H}#mbox > p.u62sub, ${H} .u62sub { margin:0 0 var(--s3) !important; font:500 16px/22px ${FALL} !important; letter-spacing:.5px; color:${MUTE} !important; text-align:center; white-space:normal; text-shadow:0 1px 2px rgba(0,0,0,.8); }
${H}#mbox > p { margin:var(--s2) 0 !important; }
${H}#mbox > div:last-child { display:flex; flex-wrap:wrap; justify-content:center; gap:var(--s3); margin-top:var(--s4); }
${H} .u62pan { ${PANEL} animation:u62in 220ms cubic-bezier(.2,.8,.2,1); }
${H}.abtn { margin-top:-16px !important; }   ${H}#prog { transform:translateY(4px); }
body.u62tipon #ui.hd.v2.u62 #s12voice { opacity:0 !important; pointer-events:none !important; }   /* 小提示出緊：心聲讓位（唔疊住） */
body.u62w-on #devBtn, body.u62ov #devBtn { visibility:hidden !important; }
body.u62ov #ui.hd.v2.u62 #toast { top:14px !important; } body.u62ov #ui.hd.v2.u62 #s12gain { top:14px !important; } body.u62ov.u62tg #ui.hd.v2.u62 #s12gain { opacity:0 !important; }   /* 面板開住：gain 同 toast 都去頂（唔壓面板標題牌）；兩個同時出 → gain 等 toast 走咗先出 */   /* 面板開住：toast 去頂（HUD 已被遮住），唔壓面板 */
${H}#diary { margin-top:-10px !important; } ${H}#s2house { margin-top:6px !important; }   /* 信件字牌唔撞屋仔 */
body.u62w-on #ui.hd.v2.u62 #toast { top:696px !important; } body.u62w-on #ui.hd.v2.u62 #s12gain { top:652px !important; }   /* 底掣字帶唔再壓住 dock 頂牌（重疊檢查） */
${H}#s12voice { transition:opacity 320ms ease; }
${H}#s12voice[style*="opacity: 1"] { pointer-events:auto; cursor:pointer; }
${H}#bubble { transition:opacity 360ms ease; }
${H}#bubble.u62on { pointer-events:auto; cursor:pointer; z-index:6; }
${H}#bubble.u62gone { opacity:0 !important; pointer-events:none !important; }
${H}#toast { top:206px !important; left:164px !important; max-width:296px !important; box-sizing:border-box; }
${H}#toast.sm2 { max-width:296px !important; }
${H}#s12gain { top:166px !important; left:20px !important; width:288px !important; }
${H}#s2houseV [data-testid="house-hint"] { left:72px !important; right:104px !important; }   /* 唔壓右下「佈置」掣 */
${H} [data-testid="house-hint"].u62gone { opacity:0 !important; transition:opacity 600ms ease; }
${H}#diary > i.l:not(.u62l) { display:block !important; }   /* 6b.2：每個 rail 都有字（信件） */
${H}#hdRail .ibtn > i.l.u62l, ${H} .ibtn > i.l.u62l { position:absolute; left:50%; top:calc(50% + 17px); transform:translateX(-50%); font:700 11px/14px ${FP}; font-style:normal; color:${CREAM}; white-space:nowrap; pointer-events:none; text-shadow:0 0 2px #000,0 1px 0 #000,1px 0 0 #000,-1px 0 0 #000,0 -1px 0 #000; }
#u62tip { position:absolute; left:16px; right:104px; bottom:176px; z-index:70; box-sizing:border-box; padding:var(--s4) var(--s4) var(--s3); ${PANEL} animation:u62in 240ms cubic-bezier(.2,.8,.2,1); color:${CREAM}; }
#u62tip .t { font:24px/28px ${FP}; letter-spacing:2px; color:${GOLD}; margin:0 0 var(--s2); text-shadow:0 1px 0 #000; }
#u62tip .b { font:400 18px/26px ${FALL}; color:${CREAM}; margin:0 0 var(--s3); }
#u62tip .k { float:right; min-width:112px; height:48px; padding:0 var(--s4); box-sizing:border-box; display:flex; align-items:center; justify-content:center; border-radius:24px; border:1px solid rgba(232,194,122,.8); background:rgba(232,194,122,.16); font:24px/28px ${FP}; color:${CREAM}; cursor:pointer; }
#u62tip .k:active { background:rgba(232,194,122,.3); }
#u62tip::after { content:''; display:block; clear:both; }
`;
    document.head.appendChild(css);

    // ── ① 講嘢句：按字數計時＋撳一下閂 ──
    const say0 = G.say;
    if (say0 && !say0._u62) { G.say = function (o) { if (o && o.line && on()) o = Object.assign({}, o, { sec: (o.sec > 0 && o.sec < speechSec(o.line)) ? o.sec : speechSec(o.line) }); return say0.call(this, o); }; G.say._u62 = true; }
    // 心聲泡泡唔壓右邊 rail（重疊檢查）：paint 完如果撞 rail 掣 → 收窄／左移，底邊同尾巴位保持
    const RAIL = '#diary, #dex, #s2kid, #s2house, #l6bbtn, #l5egg, #l5cbtn, #u62workbtn';
    function fitVoice() { const vb = $('#s12voice'); if (!vb || !on() || vb.style.display === 'none') return; const ui = $('#ui'); if (!ui) return; const k = ui.getBoundingClientRect().width / 390 || 1, ur = ui.getBoundingClientRect();
      const rs = [...document.querySelectorAll(RAIL)].filter(e => e.offsetWidth && getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden').map(e => { const r = e.getBoundingClientRect(); return { l: (r.left - ur.left) / k, t: (r.top - ur.top) / k, b: (r.bottom - ur.top) / k }; }).filter(r => r.l > 195);
      if (!rs.length) return; const x0 = vb.offsetLeft, y0 = vb.offsetTop, w0 = vb.offsetWidth, h0 = vb.offsetHeight; const hit = rs.filter(r => r.t < y0 + h0 && r.b > y0 && r.l < x0 + w0 + 4); if (!hit.length) return;
      const L = Math.min(...rs.map(r => r.l)) - 8, tl = vb.querySelector('.tail'), cx = x0 + (tl ? tl.offsetLeft + 16 : w0 / 2);
      if (w0 > L - 8) vb.style.setProperty('max-width', Math.max(160, L - 8) + 'px', 'important'); const w = vb.offsetWidth, h = vb.offsetHeight, x = Math.max(8, Math.min(x0, L - w));
      vb.style.left = x + 'px'; vb.style.top = Math.max(130, y0 + h0 - h) + 'px'; if (tl) tl.style.left = Math.max(8, Math.min(w - 40, cx - x - 16)) + 'px'; STAT.voiceFit = (STAT.voiceFit || 0) + 1; }
    if (G.sayPump) { const sp0 = G.sayPump; G.sayPump = function () { const r = sp0.apply(this, arguments); if (r && r.hide && !r.show) { const vb = $('#s12voice'); if (vb) vb.style.removeProperty('max-width'); } if (r && r.show) fitVoice(); return r; }; }
    function closeVoice(why) { const vb = $('#s12voice'); const Q = G.nq; if (Q && Q.cur) { Q.cur.until = pnow(); if (G.sayPump) G.sayPump(); } else if (vb) vb.style.opacity = 0; note('voiceClose', { why }); STAT.voiceClose++; }
    const STAT = { voiceClose: 0, bubbleHide: 0, bubbleTap: 0, hint: 0, tips: 0, subs: 0, labels: 0, pans: 0 };
    { const bind = () => { const vb = $('#s12voice'); if (!vb) return setTimeout(bind, 400); vb.addEventListener('pointerdown', (e) => { if (!on() || +vb.style.opacity < 0.5) return; e.stopPropagation(); }); vb.addEventListener('click', (e) => { if (!on()) return; e.stopPropagation(); closeVoice('tap'); }); }; bind(); }
    // 狀態氣泡：出 dur 秒淡出；同一句 45 秒後先再提
    const BB = { key: '', shown: 0, gone: 0 }, REPEAT = 45000;
    { const b = $('#bubble'); if (b) b.addEventListener('click', (e) => { if (!on() || !b.classList.contains('u62on')) return; e.stopPropagation(); BB.gone = pnow(); b.classList.add('u62gone'); b.classList.remove('u62on'); STAT.bubbleTap++; note('bubbleTap'); }); }
    function bubbleTick() {
      const b = $('#bubble'); if (!b) return; if (!on()) { b.classList.remove('u62gone', 'u62on'); return; }
      const t = pnow(), msg = b.style.display !== 'none' ? b.textContent : '';
      if (!msg) { BB.key = ''; b.classList.remove('u62gone', 'u62on'); return; }
      if (msg !== BB.key) { BB.key = msg; BB.shown = t; BB.gone = 0; b.classList.remove('u62gone'); }
      if (BB.gone) { if (t - BB.gone > REPEAT) { BB.shown = t; BB.gone = 0; b.classList.remove('u62gone'); } }
      else if (t - BB.shown > speechSec(msg) * 1000) { BB.gone = t; b.classList.add('u62gone'); STAT.bubbleHide++; note('bubbleHide', { msg }); }
      b.classList.toggle('u62on', !BB.gone);
    }
    // 屋仔底提示：每次換字顯示 6 秒
    const HH = { key: '', at: 0 };
    function hintTick() { const h = document.querySelector('[data-testid="house-hint"]'); if (!h) return; const k = h.textContent; if (k !== HH.key) { HH.key = k; HH.at = pnow(); h.classList.remove('u62gone'); } else if (on() && k && pnow() - HH.at > 6000 && !h.classList.contains('u62gone')) { h.classList.add('u62gone'); STAT.hint++; } }

    // ── ⑦ rail 字標籤 ──
    const LBL = { diary: '信件', dex: '圖鑑', s2kid: '細佬', s2house: '屋仔', l6bbtn: '散步', l5egg: '新蛋', l5cbtn: '承傳', u62workbtn: '工作' };
    function labelTick() {
      for (const id in LBL) { const e = document.getElementById(id); if (!e || !e.classList.contains('ibtn')) continue;
        const has = [...e.querySelectorAll('i.l, .l, span')].some(x => /[\u3400-\u9fff]/.test(x.textContent || '') && x.offsetWidth > 0);
        if (!has && !e.querySelector('i.u62l')) { const l = document.createElement('i'); l.className = 'l u62l'; l.textContent = LBL[id]; e.appendChild(l); STAT.labels++; }
        if (!e.getAttribute('aria-label')) e.setAttribute('aria-label', LBL[id]); }
    }
    // ── ⑦ 面板用途說明＋③ 面板換膚 ──
    const OVS = ['#l5bov', '#l6bov', '#l5ov', '#u62work', '#s2houseView', '[data-testid="house-view"]'];
    function subFor(t) { t = (t || '').replace(/\s+/g, ''); if (SUB[t]) return SUB[t]; for (const k in SUB) if (k.length >= 2 && t.indexOf(k) === 0) return SUB[k]; return ''; }
    function subTick() {
      if (!on()) return;
      const mb = $('#mbox'), h2 = mb && mb.querySelector(':scope > h2');
      if (h2 && getComputedStyle($('#modal')).display !== 'none') { const s = subFor(h2.textContent), cur = mb.querySelector(':scope > p.u62sub');
        if (s && (!cur || cur.textContent !== s)) { if (cur) cur.remove(); const p = document.createElement('p'); p.className = 'u62sub'; p.dataset.testid = 'u62-sub'; p.textContent = s; h2.after(p); STAT.subs++; }
        else if (!s && cur) cur.remove(); }
      document.querySelectorAll('#ui [data-testid$="-title"]').forEach((tt) => {
        if (tt.closest('#mbox') || !tt.offsetWidth) return; const s = subFor(tt.textContent); if (!s) return; const host = tt.parentElement; if (!host) return;
        let p = host.querySelector(':scope > .u62sub'); if (p && p.textContent === s) return; if (p) p.remove();
        p = document.createElement('div'); p.className = 'u62sub'; p.dataset.testid = 'u62-sub'; p.textContent = s;
        const cs = getComputedStyle(tt);
        if (cs.position === 'absolute' && parseFloat(cs.top) < 0) {   // 牌匾式標題（騎喺面板頂）
          const first = [...host.children].find(c => c !== tt && getComputedStyle(c).position !== 'absolute' && c.offsetHeight > 0);
          if (first) { p.style.cssText = 'position:relative;margin:-4px 28px var(--s3) !important;'; host.insertBefore(p, first); }   // 流排版：說明做面板第一行
          else { p.style.cssText = 'position:absolute;left:-8px;right:-8px;bottom:calc(100% + 28px);'; p.classList.add('u62above'); host.appendChild(p); }   // 全部絕對定位：說明放喺牌匾上面，唔推郁內容
        } else { p.style.cssText = `position:absolute;left:${tt.offsetLeft - 60}px;width:${tt.offsetWidth + 120}px;top:${tt.offsetTop + tt.offsetHeight + 2}px;`; host.appendChild(p); }
        STAT.subs++;
      });
      for (const sel of OVS) { const ov = document.querySelector(sel); if (!ov) continue;
        ov.querySelectorAll('div').forEach((d) => { if (d.classList.contains('u62pan') || d.dataset.u62np) return; const w = d.offsetWidth, h = d.offsetHeight; if (w < 200 || h < 100) return;
          const cs = getComputedStyle(d); if (cs.borderImageSource && cs.borderImageSource !== 'none' && cs.position !== 'static') { d.classList.add('u62pan'); d.style.setProperty('border-image', 'none', 'important'); d.style.setProperty('border-style', 'solid', 'important'); d.style.setProperty('border-width', '1px', 'important'); STAT.pans++; } else d.dataset.u62np = '1'; }); }
    }
    // ── ⑦ 第一次打開每個功能：一次性小提示 ──
    const TK = 'glimmer.tips62'; let seen = {}; try { seen = JSON.parse(localStorage.getItem(TK) || '{}') || {}; } catch (e) { seen = {}; }
    const TIPON = { on: qs.get('tips62') === '1' || (qs.get('tips62') !== '0' && !(navigator && navigator.webdriver)) };   // e2e（webdriver）預設唔自動出，?tips62=1 開
    function curFeature() {
      const md = $('#modal'), h2 = $('#mbox > h2');
      if (md && getComputedStyle(md).display !== 'none' && h2) { const t = h2.textContent.replace(/\s+/g, ''); const m = { '日記': 'diary', '圖鑑': 'dex', '細佬': 'kid', '設定': 'settings', '買家具': 'shop' }; for (const k in m) if (t.indexOf(k) === 0) return m[k]; return null; }
      if ($('#u62work')) return 'work';
      if ($('#l6bov')) return 'walk';
      const l5b = $('#l5bov'); if (l5b) return l5b.dataset.kind === 'plan' ? 'plan' : null;
      if (document.body.classList.contains('s2-house')) return 'house';
      const qp = document.querySelector('[data-testid="s12-qpanel"], #s12quest'); if (qp && qp.offsetWidth) return 'quest';
      return null;
    }
    function showTip(k, force) {
      const T = TIPS[k]; if (!T || (!force && (seen[k] || !TIPON.on))) return false; if ($('#u62tip')) return false;
      const el = document.createElement('div'); el.id = 'u62tip'; el.dataset.testid = 'u62-tip'; el.dataset.k = k;
      el.innerHTML = `<div class="t">小提示・${T[0]}</div><div class="b"></div><div class="k" data-testid="u62-tip-ok">知道喇</div>`; el.querySelector('.b').textContent = T[1];
      const close = (e) => { if (e) e.stopPropagation(); el.remove(); document.body.classList.remove('u62tipon'); note('tipClose', { k }); };
      el.addEventListener('pointerdown', (e) => e.stopPropagation()); el.addEventListener('click', (e) => e.stopPropagation()); el.querySelector('.k').addEventListener('click', close);
      seen[k] = Date.now(); try { localStorage.setItem(TK, JSON.stringify(seen)); } catch (e) { }
      ui.appendChild(el); document.body.classList.add('u62tipon'); closeVoice('tip'); STAT.tips++; note('tip', { k }); return true;
    }
    function tipTick() { document.body.classList.toggle('u62tipon', !!$('#u62tip')); if (!on()) return; const k = curFeature(), t = $('#u62tip'); if (t && t.dataset.k !== k && !t.dataset.force) t.remove(); if (k) showTip(k); }

    // ── ④ 重疊檢查（e2e＋🛠 用）：可見 UI 框兩兩相交 ──
    const CHROME = ['#ui .ibtn', '#ui .abtn', '#ui .hdTab', '#stagename', '#substage', '#prog', '#grains', '#s12chip', '[data-testid="s12-qprog"]', '#toast', '#s12gain', '#s12voice', '#bubble', '#devBtn',
      '[data-testid="uiv2-portrait"]', '#u62tip', '#u62tip .k', '[data-testid="house-back"]', '[data-testid="house-title"]', '[data-testid="house-decorate"]', '[data-testid="house-hint"]', '[data-testid="u62-sub"]',
      '#mbox > h2', '#mbox .btn', '[data-testid$="-close"]', '[data-testid$="-title"]', '[role="button"]', '[data-testid^="u62w-back"]', '[data-testid="u62w-sum"]', '[data-testid^="u62w-st-"]', '[data-testid="u62w-rest"]', '[data-testid="u62w-plan"]', '[data-testid="u62w-empty"]', '#u63hide'];
    function visBox(e) {
      if (!e || !e.isConnected) return null; const r = e.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return null;
      for (let p = e; p && p !== document.body; p = p.parentElement) { const cs = getComputedStyle(p); if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity < 0.15) return null; }
      const W = innerWidth, Hh = innerHeight; if (r.right <= 0 || r.bottom <= 0 || r.left >= W || r.top >= Hh) return null;
      const cx = Math.min(W - 1, Math.max(0, r.left + r.width / 2)), cy = Math.min(Hh - 1, Math.max(0, r.top + r.height / 2)), top = document.elementFromPoint(cx, cy);
      const md = $('#modal'); if (md && getComputedStyle(md).display !== 'none' && !e.closest('#modal') && !e.closest('#u62tip')) return null;   // 彈窗遮住後面嘅 HUD
      const ov = OVS.map(s => document.querySelector(s)).find(o => o && o.offsetWidth >= 380 && getComputedStyle(o).display !== 'none');
      if (ov && !ov.contains(e) && !e.closest('#modal') && !e.closest('#u62tip') && e.id !== 'toast' && e.id !== 's12gain' && e.id !== 'devBtn') return null;   // 全畫面層遮住
      // 6b.3：俾捲動／overflow 容器裁咗嘅部分睇唔到，唔計（例：工作 grid 捲出底嘅卡）
      let L = r.left, T = r.top, R = r.right, B = r.bottom;
      for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) { const cs = getComputedStyle(p); if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') { const q = p.getBoundingClientRect(); L = Math.max(L, q.left); T = Math.max(T, q.top); R = Math.min(R, q.right); B = Math.min(B, q.bottom); } }
      if (R - L < 2 || B - T < 2) return null;
      void top; return { x: L, y: T, w: R - L, h: B - T, r: R, b: B };
    }
    function overlap(opt) {
      opt = opt || {}; const tol = opt.tol == null ? 1 : opt.tol, list = [];
      const seenEl = new Set(); for (const s of CHROME) document.querySelectorAll(s).forEach(e => { if (!seenEl.has(e)) { seenEl.add(e); const b = visBox(e); if (b) list.push({ e, b }); } });
      const hits = [], nm = (e) => (e.id ? '#' + e.id : '') + (e.dataset.testid ? '[' + e.dataset.testid + ']' : '') + (!e.id && !e.dataset.testid ? e.tagName + '.' + String(e.className).slice(0, 12) : '');
      for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) { const A = list[i], B = list[j]; if (A.e.contains(B.e) || B.e.contains(A.e)) continue;
        const ix = Math.min(A.b.r, B.b.r) - Math.max(A.b.x, B.b.x), iy = Math.min(A.b.b, B.b.b) - Math.max(A.b.y, B.b.y); if (ix > tol && iy > tol) hits.push([nm(A.e), nm(B.e), Math.round(ix), Math.round(iy)]); }
      return { n: list.length, hits, names: list.map(x => nm(x.e)) };
    }

    // ── 主 loop ──
    function ovTick() { const md = $('#modal'), o = (md && getComputedStyle(md).display !== 'none') || !!$('#l5bov') || !!$('#l6bov') || !!$('#l5ov'); document.body.classList.toggle('u62ov', o); const t = $('#toast'); document.body.classList.toggle('u62tg', o && !!t && getComputedStyle(t).display !== 'none' && +getComputedStyle(t).opacity > 0.15); }
    try { const mo = new MutationObserver(() => ovTick()); const md0 = $('#modal'); if (md0) mo.observe(md0, { attributes: true, attributeFilter: ['style', 'class'] }); mo.observe(document.body, { childList: true, subtree: false }); const ui0 = $('#ui'); if (ui0) mo.observe(ui0, { childList: true }); } catch (e) { }   // 開／閂面板即時更新（唔等 250ms tick）
    function tick() { try { ovTick(); bubbleTick(); hintTick(); labelTick(); subTick(); tipTick(); } catch (e) { note('err', { m: String(e && e.message || e) }); } }
    setInterval(tick, 250); setTimeout(tick, 300);

    // ── 🛠「6b.2」──
    const DEV = { id: 'ui62', title: '6b.2（UI 打磨）', order: 47,
      status: () => '提示睇過 ' + Object.keys(seen).length + '／' + Object.keys(TIPS).length + '・講嘢句閂 ' + STAT.voiceClose + '・氣泡淡出 ' + STAT.bubbleHide + '・頭像即時 ' + (U() && U().live62 ? '開' : '閂'),
      items: [
        ['tips', '重置第一次小提示', () => { seen = {}; try { localStorage.removeItem(TK); } catch (e) { } const t = $('#u62tip'); if (t) t.remove(); return { ok: true, msg: '小提示已重置（再開功能會再出）' }; }],
        ['tipdemo', '預覽小提示（工作）', () => { const t = $('#u62tip'); if (t) t.remove(); showTip('work', true); const n = $('#u62tip'); if (n) n.dataset.force = '1'; return { ok: true, msg: '出咗' }; }],
        ['work', '開「工作」主畫面', () => { if (!G.work62) return { ok: false, msg: '冇 work62' }; G.work62.open(); return { ok: true, msg: '開咗' }; }],
        ['say', '試長句心聲（計時淡出）', () => { const l = '團絨今日喺花園見到一隻好大嘅蝴蝶，追咗佢成個下晝都唔肯返屋企食飯'; G.say({ line: l, src: 'dev62', urgent: true }); return { ok: true, msg: speechSec(l) + ' 秒後淡出（撳一下即閂）' }; }],
        ['live', '頭像即時 開／閂', () => { const u = U(); if (!u) return { ok: false, msg: '冇 v2' }; u.live62 = !u.live62; return { ok: true, msg: '頭像即時：' + (u.live62 ? '開' : '閂') }; }],
        ['ov', '量 UI 重疊', () => { const o = overlap(); return { ok: !o.hits.length, msg: o.n + ' 個框・重疊 ' + o.hits.length + (o.hits.length ? '：' + o.hits.slice(0, 2).map(h => h[0] + '×' + h[1]).join('、') : '') }; }],
      ].map(([k, label, run]) => ({ k, label, run })) };
    if (NS.devmode) NS.devmode.register(DEV); else (NS.devSections = NS.devSections || []).push(DEV);

    G.ui62 = { on, speechSec, overlap, showTip, closeVoice };
    window.__qa = window.__qa || {};
    window.__qa.ui62 = { st: () => ({ on: on(), stat: Object.assign({}, STAT), seen: Object.assign({}, seen), bubble: Object.assign({}, BB), feature: curFeature(), live: !!(U() && U().live62), t62: !!(U() && U().t62) }),
      overlap, speechSec, showTip, closeVoice, tick, dev: () => DEV, log: () => log.slice(), tipsOff: (v) => { TIPON.on = !v; }, resetTips: () => { seen = {}; try { localStorage.removeItem(TK); } catch (e) { } } };
    return true;
  }
  return { install, speechSec, SUB, TIPS };
});
