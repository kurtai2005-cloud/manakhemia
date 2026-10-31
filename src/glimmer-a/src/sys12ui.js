/* 《微光小圃》 sys12ui.js — systems12 第 1 批：瀏覽器膠水（main.js 掛入；DOM／renderer／hd2d）。原創代碼。
   系統 7：自動天氣寫入 G.weather（DEV 抽屜／?weather=／__qa.hd2d.weather 一改就 manual，DEV「自動」掣還原）；季節 → hd2d 季節層；
   團絨：落雨 idle 撐葉、霧／冬打冷震機率加大（renderer.sysPet overlay clip）。
   測試確定性：navigator.webdriver（Playwright）預設唔開自動天氣／季節層（?wxauto=1、?season=auto|spring|… 先開）。 */
(function () {
  'use strict';
  function install(G, NS) {
    const D = NS.data, P = D.PARAMS, X = NS.sys12, C = P.systems12, qs = new URLSearchParams(location.search), wd = !!(navigator && navigator.webdriver);
    const wq = qs.get('weather'), sq = qs.get('season');
    const wx = G.wx = {
      auto: C.weather.auto !== false && qs.get('wxauto') !== '0' && (!wd || qs.get('wxauto') === '1'),
      manual: !!(wq && P.evo6.branch.weather.states.includes(wq)),
      seasonMode: sq && (sq === 'auto' || sq === 'none' || X.SEASON_NAME[sq]) ? sq : (wd ? 'none' : 'auto'),
      season: null, autoWeather: null, acc: 1e9, shiverAt: null, log: [],
    };
    if (wx.manual) G.weather = wq === 'clear' ? null : wq;
    G.wxTick = function (force) {
      const now = G.now(), w = X.weatherAt(now, G.state.seed >>> 0);
      wx.autoWeather = w;
      if (wx.auto && !wx.manual) { const nw = w === 'clear' ? null : w; if ((G.weather || null) !== nw) { wx.log.push({ t: now, from: G.weather || 'clear', to: w }); if (wx.log.length > 50) wx.log.shift(); } G.weather = nw; }
      const ss = wx.seasonMode === 'auto' ? X.seasonOf(now) : wx.seasonMode === 'none' ? null : wx.seasonMode;
      wx.season = ss; if (G.hd) G.hd.season = ss;
      return { weather: G.weather || 'clear', auto: w, manual: wx.manual, season: ss };
    };
    /* DEV／QA：'auto' → 跟返自動；其他（clear／overcast／rain／fog）→ manual 覆蓋 */
    G.weatherSet = function (w) {
      if (w === 'auto') { wx.manual = false; wx.auto = true; } else { wx.manual = true; G.weather = w && w !== 'clear' && P.evo6.branch.weather.states.includes(w) ? w : null; }
      return G.wxTick(true);
    };
    G.seasonSet = function (m) { wx.seasonMode = m === 'auto' || m === 'none' || X.SEASON_NAME[m] ? m : 'auto'; if (G.hd && wx.seasonMode !== 'none' && wx.seasonMode !== 'auto') G.hd.loadSeason(wx.seasonMode); return G.wxTick(true); };
    /* 團絨天氣小動作：落雨 → 撐葉（idle 循環）；每 shiverEverySec 擲一次打冷震（霧／冬 ×倍數） */
    const rd = G.renderer, SP = rd.sysPet = rd.sysPet || { umbrella: false, one: null };
    G.sysPlay = function (clip, o) { const Cd = D.SYS_CLIPS[clip]; if (!Cd) return false; o = o || {}; SP.one = { clip, start: rd.t || 0, dur: o.dur || Cd.frames / Cd.fps * (Cd.repeat || 1), tell: !!Cd.tell || !!o.any }; return true; };
    function petTick(dt) {
      const s = G.state, W = C.weather, rain = (G.weather || 'clear') === 'rain' && s.stage !== 'egg' && !s.sleeping;
      SP.umbrella = rain;
      if (s.stage === 'egg' || s.sleeping) return;
      const t = rd.t || 0; if (wx.shiverAt == null) wx.shiverAt = t + W.shiverEverySec[0] + Math.random() * (W.shiverEverySec[1] - W.shiverEverySec[0]);
      if (t >= wx.shiverAt) {
        wx.shiverAt = t + W.shiverEverySec[0] + Math.random() * (W.shiverEverySec[1] - W.shiverEverySec[0]);
        const mul = X.shiverMul(G.weather || 'clear', wx.season), p = mul > 1 ? Math.min(1, W.shiverBaseChance * mul) : 0;   // 只喺霧／冬先打冷震
        if (!SP.one && !rain && Math.random() < p) G.sysPlay('shiver');
      }
    }
    // ── 系統 1：每日小委託（面板＝遊美 b1 panel_commission／row／checkbox／icon；星星碎 icon 16／32）──
    const ART = 'art/systems12/', AJ = {}; const uiRoot = document.getElementById('ui');
    const NINE = {};
    function nine(el, name, sl, k) {                     // 9-slice：canvas → dataURL → CSS border-image（單檔 build 都得：Image.src 會被攔截）
      k = k || 2; const ap = (u) => { el.style.borderStyle = 'solid'; el.style.borderWidth = `${sl[0] * k}px ${sl[1] * k}px ${sl[2] * k}px ${sl[3] * k}px`; el.style.borderImage = `url(${u}) ${sl[0]} ${sl[1]} ${sl[2]} ${sl[3]} fill / ${sl[0] * k}px ${sl[1] * k}px ${sl[2] * k}px ${sl[3] * k}px round`; };
      if (NINE[name]) return ap(NINE[name]);
      const im = new Image(); im.onload = () => { try { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; c.getContext('2d').drawImage(im, 0, 0); NINE[name] = c.toDataURL();
        el.style.borderStyle = 'solid'; el.style.borderWidth = `${sl[0] * k}px ${sl[1] * k}px ${sl[2] * k}px ${sl[3] * k}px`; el.style.borderImage = `url(${c.toDataURL()}) ${sl[0]} ${sl[1]} ${sl[2]} ${sl[3]} fill / ${sl[0] * k}px ${sl[1] * k}px ${sl[2] * k}px ${sl[3] * k}px round`; } catch (e) { } };
      im.src = ART + name + '.png';
    }
    /* innerHTML 嘅 <img src> 唔經 HTMLImageElement.src setter（單檔 build 攔截唔到）→ 先寫 data-s12，之後 hyd() 用 .src 設 */
    const hyd = (root) => { if (root) root.querySelectorAll('img[data-s12]').forEach(i => { i.src = ART + i.dataset.s12 + '.png'; i.removeAttribute('data-s12'); }); return root; };
    const pimg = (name, px, cls) => `<img data-s12="${name}" width="${px}" height="${px}" class="${cls || ''}" style="image-rendering:pixelated;width:${px}px;height:${px}px" alt="">`;
    const css = document.createElement('style'); css.textContent = `
      #devp [data-testid^="dev-s12"] button,#devp [data-testid="dev-season-row"] button,#devp [data-testid="dev-weather-auto"]{min-height:var(--devhit,48px);min-width:var(--devhit,48px)}   /* systems12 DEV 掣 ≥48dp：跟 v10 --devhit（按 uiScale 補償） */
      #s12chip { position:absolute; right:10px; top:122px; padding:3px 8px 3px 5px; display:flex; align-items:center; gap:4px; font:700 12px/1 sans-serif; color:var(--warm); cursor:pointer; pointer-events:auto; z-index:6; }
      #s12chip img { display:block; } #s12chip.pulse { animation:s12p .5s 2; } @keyframes s12p { 50% { transform:scale(1.12); } }
      #s12chip .q { opacity:.85; font-weight:600; }
      #s12gain { position:absolute; right:14px; top:150px; font:700 13px sans-serif; color:#ffe27a; text-shadow:0 1px 0 #3a2a10, 0 0 3px #3a2a10, 0 0 6px #0b1030; pointer-events:none; opacity:0; transition:opacity .3s, transform .9s; z-index:7; }
      #s12p { position:absolute; inset:0; z-index:40; display:none; align-items:center; justify-content:center; background:rgba(5,7,26,.55); }
      #s12box { width:330px; color:#4a2e1a; font:13px/1.45 sans-serif; image-rendering:pixelated; box-sizing:border-box; }
      #s12box h3 { position:absolute; left:0; right:0; top:-31px; margin:0; text-align:center; text-shadow:0 1px 0 #2f5a1e; font-size:14px; color:#fff6dc; letter-spacing:2px; }
      #s12body { max-height:560px; overflow:auto; } .s12tabs { display:flex; gap:4px; margin:0 0 8px; } .s12tabs b { flex:1; text-align:center; padding:4px 0; border-radius:6px; background:rgba(74,46,26,.12); cursor:pointer; font-size:12px; } .s12tabs b.on { background:#c0783f; color:#fff6dc; }
      .s12row { display:flex; align-items:center; gap:8px; margin:0 0 6px; min-height:28px; box-sizing:border-box; image-rendering:pixelated; }
      .s12row .t { flex:1; } .s12row small { opacity:.75; } .s12row .rt { font-size:10px; padding:1px 5px; border-radius:6px; color:#fff; margin-left:4px; }
      .s12foot { display:flex; align-items:center; gap:6px; justify-content:space-between; margin-top:8px; font-size:12px; }
      #s12voice { position:absolute; z-index:9; max-width:230px; padding:0; font:600 13px/1.4 sans-serif; color:#4a2e1a; pointer-events:none; opacity:0; transition:opacity .35s; image-rendering:pixelated; box-sizing:border-box; text-align:center; }
      #s12voice .tail { position:absolute; width:32px; height:28px; bottom:-24px; left:calc(50% - 16px); image-rendering:pixelated; }
      .s12bar { height:12px; background:#e9d6ae; border:2px solid #c0783f; border-radius:6px; overflow:hidden; margin:2px 0 8px; } .s12bar i { display:block; height:100%; background:linear-gradient(90deg,#ff9fb5,#ffd36a); }
      .s12line { font-size:12px; margin:0 0 3px; } .s12line.lock { opacity:.45; } .s12tier { font-weight:700; margin:8px 0 3px; font-size:12px; color:#8a4f2a; }
      .s12mem { font-size:12px; padding:3px 0; border-top:1px dashed rgba(74,46,26,.3); }
      .s12dnav { display:flex; align-items:center; justify-content:space-between; gap:6px; margin-bottom:6px; font-size:12px; } .s12dnav b { cursor:pointer; padding:2px 10px; border-radius:6px; background:#e9d6ae; } .s12dnav b.off { opacity:.3; pointer-events:none; }
      .s12dsrc { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:6px; } .s12dsrc i { font-style:normal; font-size:11px; padding:2px 8px; border-radius:8px; background:#e9d6ae; cursor:pointer; } .s12dsrc i.on { background:#c0783f; color:#fff; }
      .s12page { box-sizing:border-box; min-height:250px; color:#4a2e1a; font-size:13px; line-height:1.55; image-rendering:pixelated; position:relative; }
      .s12page p { margin:0 0 4px; } .s12page .dt { font-weight:700; margin-bottom:6px; color:#8a4f2a; } .s12page[data-kind="offline"] p { font-style:italic; opacity:.8; }
      .s12page .stk { display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; } .s12page .sp { font-weight:700; color:#c0503f; margin-bottom:4px; }
      .s12x { position:absolute; right:22px; top:16px; cursor:pointer; font:700 18px sans-serif; color:#fff6dc; }
    `; document.head.appendChild(css);
    const chip = document.createElement('div'); chip.id = 's12chip'; chip.className = 'panel'; chip.dataset.testid = 's12-chip';
    chip.innerHTML = `${pimg('icon_star_shard_16', 16)}<span data-testid="s12-shards">0</span><span class="q" data-testid="s12-qprog"></span>`; hyd(chip);
    const gain = document.createElement('div'); gain.id = 's12gain'; gain.dataset.testid = 's12-gain';
    const pan = document.createElement('div'); pan.id = 's12p'; pan.dataset.testid = 's12-panel';
    pan.innerHTML = `<div id="s12box" style="position:relative"><h3 data-testid="s12-title">每日小委託</h3><div class="s12tabs" data-testid="s12-tabs"></div><div id="s12body"></div></div><i class="s12x" data-testid="s12-close">✕</i>`;
    if (uiRoot) { uiRoot.appendChild(chip); uiRoot.appendChild(gain); uiRoot.appendChild(pan); }
    nine(pan.querySelector('#s12box'), 'panel_commission_9s', [18, 12, 12, 12]);
    const S12 = G.s12 = { tab: 'quest', tabs: [['quest', '委託'], ['diary', '日記'], ['bond', '親密'], ['surp', '小驚喜']], dsrc: 'cur', dpage: null, open: false, log: [] };
    const now = () => G.now();
    function shardTxt() { const w = X.wallet(G.state, now()); return w; }
    function renderQuest() {
      const q = X.quests(G.state, now()), w = shardTxt(), RC = P.evo6.route.colors;
      if (!q.list.length) return `<div class="s12row" data-testid="s12-q-none"><span class="t">光卵孵咗先有委託㗎。</span></div>`;
      return q.list.map((x, i) => `<div class="s12row s12q" data-testid="s12-q-${i}" data-k="${x.k}" data-done="${x.n >= x.need ? 1 : 0}">${pimg(x.icon, 24)}<span class="t">${x.label}<small> ${Math.min(x.n, x.need)}/${x.need}</small>${x.route ? `<span class="rt" style="background:${RC[x.route] || '#888'}" data-testid="s12-q-route">${D.FORM_NAME[x.route] || x.route}</span>` : ''}</span>${pimg(x.n >= x.need ? 'checkbox_done' : 'checkbox_empty', 20)}</div>`).join('') +
        `<div class="s12foot"><span>3 個齊即刻 ${pimg('icon_star_shard_16', 16)} +${q.reward * q.list.length}${q.paid ? '（已領）' : ''}${q.route ? `<span class="rt" style="background:${RC[q.route] || '#888'}" data-testid="s12-q-route">${D.FORM_NAME[q.route] || q.route}+1</span>` : ''}</span><span data-testid="s12-wallet">${pimg('icon_star_shard_16', 16)} ${w.total}｜今日 ${w.today}/${w.cap}</span></div>`;
    }
    // ── 系統 6：親密度＋心聲（心聲泡＝遊美 bubble_thought_9s＋tail）──
    const vb = document.createElement('div'); vb.id = 's12voice'; vb.dataset.testid = 's12-voice';
    vb.innerHTML = `<span data-testid="s12-voice-text"></span><img class="tail" data-s12="bubble_thought_tail" alt="">`; hyd(vb);
    if (uiRoot) uiRoot.appendChild(vb); nine(vb, 'bubble_thought_9s', [11, 11, 11, 11], 2);
    let vbHide = 0;
    function showVoice(r) {
      const b = NS.ui.petHitBox ? NS.ui.petHitBox() : { x: 80, y: 120, w: 36, h: 40 }; const sp = vb.querySelector('span'); sp.textContent = r.line; if (r.icon) { sp.insertAdjacentHTML('afterbegin', pimg(r.icon, 16) + ' '); hyd(sp); }
      vb.style.opacity = 0; vb.style.left = '0px'; vb.style.top = '0px'; vb.style.display = 'block';
      const w = vb.offsetWidth, h = vb.offsetHeight, cx = (b.x + b.w / 2) * 2, x = Math.max(8, Math.min(390 - 8 - w, cx - w / 2)), y = Math.max(130, b.y * 2 - h - 26);
      vb.style.left = x + 'px'; vb.style.top = y + 'px'; vb.querySelector('.tail').style.left = Math.max(8, Math.min(w - 40, cx - x - 16)) + 'px'; vb.style.opacity = 1;
      clearTimeout(vbHide); vbHide = setTimeout(() => { vb.style.opacity = 0; }, C.bond.voice.showSec * 1000);
      S12.lastVoice = r; G.state.ev.push({ type: 'sys12', sys: 'bond', what: 'voice', line: r.line, tier: r.tier, src: r.src });
    }
    G.sysVoice = function (o) { const r = X.voiceTry(G.state, now(), o); if (r.ok) showVoice(r); S12.lastTry = r; return r; };
    /* ui.js 撳寵物鬆手：長撳（≥ SHORT_MS）→ 親密 +2；短撳 → 心聲（30%、冷卻 10 分鐘、同懸浮共用） */
    G.sysPress = function (p) { if (!p || G.state.stage === 'egg') return null; X.notePat(G.state, now(), G.state.ev);   /* v10.2 委託「摸摸佢個頭」：短撳／長撳都計 */ if (!p.short) return { bond: X.onLongPress(G.state, now(), G.state.ev) }; return { voice: G.sysVoice({ src: 'app' }) }; };
    function renderBond() {
      const s = G.state, b = X.bond(s, now()), L = C.bond.lines, mem = (s.memorial || []).slice(-6).reverse();
      return `<div data-testid="s12-bond-v">親密度 <b>${Math.round(b.v)}</b> / 100　第 ${b.tier} 段心聲<small>（今日 +${b.todayGain}/${b.cap}）</small></div><div class="s12bar"><i style="width:${b.v}%"></i></div>` +
        L.map((arr, i) => `<div class="s12tier">第 ${i + 1} 段（${(i + 1) * C.bond.tierEvery}）${i < b.tier ? '' : '🔒'}</div>` + arr.map(l => `<div class="s12line${i < b.tier ? '' : ' lock'}">${i < b.tier ? l : '？？？'}</div>`).join('')).join('') +
        `<div class="s12tier">紀念冊</div>` + (mem.length ? mem.map(m => `<div class="s12mem" data-testid="s12-mem">第 ${m.gen} 代・${D.FORM_NAME[m.form] || m.form || ''}　親密度 ${m.bond != null ? m.bond : '—'}${m.bondElder != null ? '（靜光 ' + m.bondElder + '）' : ''}${m.diary ? '　日記 ' + m.diary.length + ' 篇' : ''}</div>`).join('') : `<div class="s12mem">未有紀念</div>`);
    }
    // ── 系統 12：懸浮小驚喜（設定＋懸浮 replay 入帳；主程式淨係 DEV 預覽）──
    const UC = C.surprise;
    G.evo.sys12Overlay = () => X.overlaySys12(G.state, now());                       // fpet-bridge → snapshot.sys12（只讀）
    G.evo.sys12Apply = (items) => { const r = X.applyOverlay(G.state, items, now(), G.state.ev); if (r.drop || r.voice || r.set) G.save && G.save(); return r; };
    const SURP_ROWS = [['drop', '懸浮掉星星碎（每 2–4 粒鐘一粒，每日最多 5）'], ['water', '飲水提醒'], ['sleep', '早瞓提醒']];
    function setSurp(k, v) { X.surpSet(G.state, k, v, now()); G.save && G.save(); G.state.ev.push({ type: 'sys12', sys: 'surp', what: 'set', key: k, val: v }); if (window.__fpetBridge && __fpetBridge.writeSnapshot) __fpetBridge.writeSnapshot(); }
    G.sysSettings = function (node) {                    // ui.js 設定彈窗：逐項開／閂（同懸浮設定同步）
      const u = X.surp(G.state), mk = (txt, on, tid, fn) => { const b = document.createElement('div'); b.className = 'btn' + (on ? '' : ' sec'); b.style.cssText = 'margin:0;padding:6px 16px'; b.dataset.testid = tid; b.textContent = on ? '開' : '關'; b.addEventListener('click', () => { const v = b.classList.contains('sec'); fn(v); b.textContent = v ? '開' : '關'; b.classList.toggle('sec', !v); }); return b; };
      const h = document.createElement('div'); h.className = 'row'; h.style.cssText = 'font-weight:700;margin-top:6px'; h.textContent = '懸浮小驚喜'; node.appendChild(h);
      for (const [k, n] of SURP_ROWS) { const r = document.createElement('div'); r.className = 'row'; r.innerHTML = `<span>${n}</span>`; r.appendChild(mk(n, u.on[k], 'toggle-surp-' + k, (v) => setSurp(k, v))); node.appendChild(r); }
      const seg = (opts, cur, tid, fn, lab) => { const s0 = document.createElement('div'); s0.className = 'seg'; s0.dataset.testid = tid; opts.forEach(o => { const b = document.createElement('div'); b.className = 'btn' + (o.v === cur ? ' on' : ''); b.textContent = o.n; b.dataset.testid = tid + '-' + String(o.v).replace(':', ''); b.addEventListener('click', () => { fn(o.v); s0.querySelectorAll('.btn').forEach(x => x.classList.remove('on')); b.classList.add('on'); }); s0.appendChild(b); }); const l = document.createElement('div'); l.className = 'row'; l.style.fontSize = '12px'; l.textContent = lab; node.appendChild(l); node.appendChild(s0); };
      seg(UC.water.hours.map(v => ({ v, n: v + ' 粒鐘' })), u.waterH, 'surp-waterH', (v) => setSurp('waterH', v), `飲水提醒間隔（${UC.water.fromH}:00–${UC.water.toH}:00）`);
      seg(UC.sleep.times.map(v => ({ v, n: v })), u.sleepAt, 'surp-sleepAt', (v) => setSurp('sleepAt', v), '早瞓提醒時間');
    };
    function renderSurp() {
      const u = X.surp(G.state), k = NS.sim.dayKey(now()), o = X.overlaySys12(G.state, now()).surp;
      const ic = { drop: 'icon_star_shard_16', water: 'icon_remind_water', sleep: 'icon_remind_sleep' };
      return `<div style="font-size:12px;margin-bottom:6px">懸浮團絨會偶然送你小驚喜；閂咗就完全唔會出。</div>` + SURP_ROWS.map(([key, n]) => `<div class="s12row s12q" data-done="${u.on[key] ? 1 : 0}" data-testid="s12-surp-${key}">${pimg(ic[key], 24)}<span class="t">${n}<small>${key === 'water' ? `（${u.waterH} 粒鐘）` : key === 'sleep' ? `（${u.sleepAt}）` : ''}</small></span><b style="margin:0 6px">${u.on[key] ? '開' : '關'}</b>${pimg(u.on[key] ? 'checkbox_done' : 'checkbox_empty', 20)}</div>`).join('') +
        `<div style="font-size:12px;margin-top:8px">${pimg('icon_star_shard_16', 16)} 今日懸浮已送 ${u.drops[k] || 0}／${UC.drop.perDay} 粒（尚餘 ${o.drop.room}）</div><div style="font-size:11px;opacity:.7;margin-top:4px">開關喺「設定」或者撳上面一行。</div>`;
    }
    pan.addEventListener('click', (e) => { const r = e.target.closest('[data-testid^="s12-surp-"]'); if (!r) return; const k = r.dataset.testid.slice(9); setSurp(k, !X.surp(G.state).on[k]); draw(); });
    function previewRemind(what) {                       // DEV：主程式預覽提醒泡（真提醒喺懸浮）
      const L = UC.lines[what]; showVoice({ line: L[Math.floor(Math.random() * L.length)], tier: 0, src: 'remind', icon: what === 'water' ? 'icon_remind_water' : 'icon_remind_sleep' }); vb.dataset.kind = what; return { ok: true, what, on: X.surp(G.state).on[what] };
    }
    // ── 系統 3：團絨日記（遊美 diary_page_9s／diary_page_special_9s＋貼紙）──
    G.sysFed = (id) => X.diaryNote(G.state, 'food', id, now());
    function diaryPages() {
      const s = G.state; if (S12.dsrc === 'cur') { const d = X.diary(s, now()); return d.list.concat(d.today ? [d.today] : []); }
      const m = (s.memorial || [])[+S12.dsrc]; return m && m.diary ? m.diary.map(e => Object.assign({ gen: m.gen }, e)) : [];
    }
    function renderDiary() {
      const s = G.state, pages = diaryPages(), mems = (s.memorial || []).map((m, i) => ({ m, i })).filter(x => x.m.diary && x.m.diary.length);
      let i = S12.dpage == null || S12.dpage >= pages.length ? pages.length - 1 : S12.dpage; S12.dcur = i;
      const src = `<div class="s12dsrc" data-testid="s12-dsrc"><i data-dsrc="cur" class="${S12.dsrc === 'cur' ? 'on' : ''}">今代（第 ${s.gen || 1} 代）</i>${mems.map(x => `<i data-dsrc="${x.i}" data-testid="s12-dsrc-mem" class="${String(S12.dsrc) === String(x.i) ? 'on' : ''}">紀念冊・第 ${x.m.gen} 代${D.FORM_NAME[x.m.form] ? '（' + D.FORM_NAME[x.m.form] + '）' : ''}</i>`).join('')}</div>`;
      if (!pages.length) return src + `<div class="s12row"><span class="t" data-testid="s12-diary-none">光卵孵咗之後，團絨每日會寫一篇日記。</span></div>`;
      const e = pages[i], dt = e.d.split('-'), SPN = { evolve: '✦ 特別頁：進化日', fade: '✦ 特別頁：化光日' };
      return src + `<div class="s12dnav"><b data-dnav="-1" class="${i > 0 ? '' : 'off'}" data-testid="s12-diary-prev">◀</b><span data-testid="s12-diary-pos">${+dt[1]} 月 ${+dt[2]} 日${e.draft ? '（今日・寫緊）' : ''}　${i + 1}／${pages.length}</span><b data-dnav="1" class="${i < pages.length - 1 ? '' : 'off'}" data-testid="s12-diary-next">▶</b></div>` +
        `<div class="s12page" data-testid="s12-diary-page" data-kind="${e.kind}" data-special="${e.special ? 1 : 0}">${e.special ? `<div class="sp">${SPN[e.kind] || ''}</div>` : ''}${e.lines.map(l => `<p>${l}</p>`).join('')}<div class="stk">${(e.stickers || []).map(k => pimg('sticker_' + k, 32)).join('')}</div></div>` +
        `<div style="font-size:11px;opacity:.7;margin-top:6px">日記留最近 ${C.diary.keepDays} 日；化光之後成本日記入紀念冊。</div>`;
    }
    pan.addEventListener('click', (e) => { const n = e.target.closest('[data-dnav]'), sr = e.target.closest('[data-dsrc]'); if (n) { S12.dpage = Math.max(0, (S12.dcur || 0) + +n.dataset.dnav); draw(); } else if (sr) { S12.dsrc = sr.dataset.dsrc; S12.dpage = null; draw(); } });
    const RENDER = { quest: renderQuest, diary: renderDiary, bond: renderBond, surp: renderSurp }; G.s12render = RENDER;
    G.s12dev = Object.assign(G.s12dev || {}, {   // DEV 抽屜（devpanel s12:<名>）
      bondUp: () => { const b = X.bondOf(G.state); b.v = Math.min(100, b.v + 10); lastChip = ''; return X.bond(G.state, now()); },
      bondDown: () => { const b = X.bondOf(G.state); b.v = Math.max(0, b.v - 10); return X.bond(G.state, now()); },
      voice: () => G.sysVoice({ force: true, src: 'dev' }),
      diaryOpen: () => { S12.dsrc = 'cur'; S12.dpage = null; return G.s12open('diary'); },
      diaryWrite: () => { const tr = X.diaryTrack(G.state, now(), G.state.ev); const e = X.buildEntry(G.state, tr); tr.done = true; G.state.sys12.diary.list.push(e); return e; },
      diaryEvolve: () => { const tr = X.diaryTrack(G.state, now(), G.state.ev); if (G.state.stage !== 'egg') tr.stages.push(G.state.stage); return X.buildEntry(G.state, tr); },
      diaryOffline: () => { const tr = X.diaryTrack(G.state, now(), G.state.ev), d = new Date(now()); d.setDate(d.getDate() - 4); tr.day = NS.sim.dayKey(d.getTime()); tr.done = false; return X.diaryTrack(G.state, now(), G.state.ev) && X.diary(G.state, now()).list.length; },
      diaryFill: () => { const o = G.state.sys12.diary, L = o.list; for (let i = 40; i >= 1; i--) { const d = new Date(now()); d.setDate(d.getDate() - i); const tr = { day: NS.sim.dayKey(d.getTime()), gen: G.state.gen || 1, foods: i % 3 ? { meal: 1 } : {}, care: { feed: 1 }, n: 1 + (i % 7), stages: i === 12 ? ['juvenile'] : [], st0: G.state.stage, stLast: G.state.stage, mood: [60 + i % 30, 1], mt: 0, wt: 0, wx: {}, fade: false }; if (!L.some(e => e.d === tr.day && e.gen === tr.gen)) L.push(X.buildEntry(G.state, tr)); } L.sort((a, b) => (a.d < b.d ? -1 : 1)); while (L.length > C.diary.keepDays) L.shift(); return L.length; },
      drop: () => G.evo.sys12Apply([{ k: 'drop', t: now() }]), drop5: () => G.evo.sys12Apply([0, 1, 2, 3, 4, 5].map(i => ({ k: 'drop', t: now() - i }))),
      water: () => previewRemind('water'), sleep: () => previewRemind('sleep'), surpOpen: () => G.s12open('surp'),
      surpDrop: () => setSurp('drop', !X.surp(G.state).on.drop), surpWater: () => setSurp('water', !X.surp(G.state).on.water), surpSleep: () => setSurp('sleep', !X.surp(G.state).on.sleep), ignore: () => window.__qa.sys12.ignoreDay(), bondOpen: () => G.s12open('bond'),
    });
    function draw() {
      if (!S12.open) return; const body = pan.querySelector('#s12body'), tabs = pan.querySelector('.s12tabs');
      tabs.innerHTML = S12.tabs.length > 1 ? S12.tabs.map(([k, l]) => `<b data-tab="${k}" data-testid="s12-tab-${k}" class="${k === S12.tab ? 'on' : ''}">${l}</b>`).join('') : '';
      pan.querySelector('h3').textContent = { quest: '每日小委託', diary: '團絨日記', bond: '親密度', surp: '懸浮小驚喜' }[S12.tab] || '';
      body.innerHTML = (RENDER[S12.tab] || renderQuest)(); hyd(body);
      body.querySelectorAll('.s12row').forEach(r => { if (!r.dataset.nine) { r.dataset.nine = 1; nine(r, 'panel_commission_row_9s', [6, 6, 6, 6], 1.5); } });
      body.querySelectorAll('.s12page').forEach(p => nine(p, p.dataset.special === '1' ? 'diary_page_special_9s' : 'diary_page_9s', [12, 10, 12, 18], 2));
    }
    G.s12open = function (tab) { S12.open = true; if (tab) S12.tab = tab; pan.style.display = 'flex'; draw(); return true; };
    G.s12close = function () { S12.open = false; pan.style.display = 'none'; };
    G.s12draw = draw;
    chip.addEventListener('click', (e) => { e.stopPropagation(); G.s12open('quest'); });
    ['pointerdown', 'touchstart', 'mousedown'].forEach(tp => { chip.addEventListener(tp, e => e.stopPropagation()); pan.addEventListener(tp, e => e.stopPropagation()); });
    pan.addEventListener('click', (e) => { e.stopPropagation(); const tb = e.target.closest('[data-tab]'); if (tb) { S12.tab = tb.dataset.tab; draw(); return; } if (e.target === pan || e.target.closest('.s12x')) G.s12close(); });
    let lastChip = '';
    function chipTick() {
      const w = X.wallet(G.state, now()), q = X.quests(G.state, now()), dn = q.list.filter(x => x.n >= x.need).length;
      const txt = w.total + '|' + dn + '/' + q.list.length; if (txt === lastChip) return; lastChip = txt;
      chip.querySelector('[data-testid="s12-shards"]').textContent = w.total;
      chip.querySelector('[data-testid="s12-qprog"]').textContent = q.list.length ? `委託 ${dn}/${q.list.length}` : '';
      if (S12.open) draw();
    }
    function showGain(n, why) { gain.textContent = n ? `+${n} 星星碎${why ? '　' + why : ''}` : why; gain.style.transition = 'none'; gain.style.opacity = 1; gain.style.transform = 'translateY(0)'; void gain.offsetWidth; gain.style.transition = 'opacity .6s 1.4s, transform 2s'; gain.style.opacity = 0; gain.style.transform = 'translateY(-14px)'; chip.classList.remove('pulse'); void chip.offsetWidth; chip.classList.add('pulse'); }
    G.sysEvent = function (e) {
      S12.log.push(Object.assign({ t: now() }, e)); if (S12.log.length > 60) S12.log.shift();
      if (e.sys === 'quest' && e.what === 'paid' && e.n > 0) showGain(e.n, e.late ? '（委託補發）' : '（委託完成）');
      if (e.sys === 'surp' && e.what === 'replay' && e.drop) showGain(e.drop, '（懸浮團絨送嘅）');
      if (e.sys === 'bond' && e.what === 'tier') showGain(0, '親密度 ' + Math.round(e.v) + '：解鎖第 ' + e.tier + ' 段心聲');
      if (e.sys === 'quest' && e.what === 'step') { chip.classList.remove('pulse'); void chip.offsetWidth; chip.classList.add('pulse'); }
      lastChip = ''; chipTick();
      (G.sysListeners || []).forEach(fn => { try { fn(e); } catch (er) { } });
    };
    function questTick() { const ev = G.state.ev; X.questTick(G.state, now(), ev); X.bondTick(G.state, now(), ev); }
    G.sysTick = function (dt) { wx.acc += dt; if (wx.acc >= 1) { wx.acc = 0; G.wxTick(); questTick(); chipTick(); if (G.weather && G.state.stage !== 'egg') X.diaryNote(G.state, 'wx', G.weather, now()); } petTick(dt); };
    questTick(); chipTick();
    G.wxTick(true);
    window.__qa = window.__qa || {};
    window.__qa.sys12 = Object.assign(window.__qa.sys12 || {}, {
      weather: (w) => (w !== undefined ? G.weatherSet(w) : G.wxTick()), season: (m) => (m !== undefined ? G.seasonSet(m) : G.wxTick()),
      wx: () => Object.assign({}, wx, { weatherNow: NS.sim.weatherNow(), scene: G.hd ? G.hd.current().variant : null, umbrella: SP.umbrella, one: SP.one && SP.one.clip, shown: rd.sysShown || null, sysLog: rd.sysLog || [] }),
      play: (c, o) => G.sysPlay(c, o), simulate: (seed, from, days) => X.simulate(seed, from, days),
      quests: () => X.quests(G.state, G.now()), wallet: () => X.wallet(G.state, G.now()), questTick: () => X.questTick(G.state, G.now(), G.state.ev),
      questDo: (i) => { const x = X.st(G.state).quests.list[i]; if (!x) return null; X.onCare(G.state, P.systems12.quests.kinds[x.k].counts[0], G.now(), G.state.ev); return X.quests(G.state, G.now()); },   // DEV：當做咗 1 次（走真 hook 路徑）
      questFill: () => { const q = X.st(G.state).quests; q.list.forEach(x => { let g = 9; while (x.n < x.need && g--) X.onCare(G.state, P.systems12.quests.kinds[x.k].counts[0], G.now(), G.state.ev); }); return X.quests(G.state, G.now()); },
      questReset: () => { const q = X.st(G.state).quests; q.day = ''; return X.questTick(G.state, G.now(), G.state.ev); },
      grant: (n, src) => X.grant(G.state, n, src || 'dev', G.now()),
      diary: () => X.diary(G.state, G.now()), diaryPage: () => { const p = document.querySelector('[data-testid="s12-diary-page"]'); return p ? { kind: p.dataset.kind, special: p.dataset.special, txt: p.textContent, pos: document.querySelector('[data-testid="s12-diary-pos"]').textContent } : null; },
      surp: () => X.surp(G.state), overlay: () => X.overlaySys12(G.state, G.now()), apply: (items) => G.evo.sys12Apply(items),
      bond: () => X.bond(G.state, G.now()), bondSet: (v) => { X.bondOf(G.state).v = Math.max(0, Math.min(100, v)); return X.bond(G.state, G.now()); }, voice: (o) => G.sysVoice(o || { force: true, src: 'dev' }), lastVoice: () => S12.lastVoice || null, lastTry: () => S12.lastTry || null,
      ignoreDay: () => { const b = X.bondOf(G.state), d = new Date(G.now()); d.setDate(d.getDate() - 2); b.chk = NS.sim.dayKey(d.getTime()); G.state.careDays = (G.state.careDays || []).filter(k => k !== NS.sim.dayKey(G.now() - 86400e3)); return X.bondTick(G.state, G.now(), G.state.ev); }, open: (tab) => G.s12open(tab), close: () => G.s12close(), log: () => S12.log.slice(),
    });
  }
  window.Glimmer = window.Glimmer || {}; window.Glimmer.sys12ui = { install };
})();
