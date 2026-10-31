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
    function nine(el, name, sl, k) {                     // 9-slice：canvas → dataURL → CSS border-image（單檔 build 都得：Image.src 會被攔截）
      k = k || 2; const im = new Image(); im.onload = () => { try { const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; c.getContext('2d').drawImage(im, 0, 0);
        el.style.borderStyle = 'solid'; el.style.borderWidth = `${sl[0] * k}px ${sl[1] * k}px ${sl[2] * k}px ${sl[3] * k}px`; el.style.borderImage = `url(${c.toDataURL()}) ${sl[0]} ${sl[1]} ${sl[2]} ${sl[3]} fill / ${sl[0] * k}px ${sl[1] * k}px ${sl[2] * k}px ${sl[3] * k}px round`; } catch (e) { } };
      im.src = ART + name + '.png';
    }
    const pimg = (name, px, cls) => `<img src="${ART}${name}.png" width="${px}" height="${px}" class="${cls || ''}" style="image-rendering:pixelated;width:${px}px;height:${px}px" alt="">`;
    const css = document.createElement('style'); css.textContent = `
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
      .s12x { position:absolute; right:22px; top:16px; cursor:pointer; font:700 18px sans-serif; color:#fff6dc; }
    `; document.head.appendChild(css);
    const chip = document.createElement('div'); chip.id = 's12chip'; chip.className = 'panel'; chip.dataset.testid = 's12-chip';
    chip.innerHTML = `${pimg('icon_star_shard_16', 16)}<span data-testid="s12-shards">0</span><span class="q" data-testid="s12-qprog"></span>`;
    const gain = document.createElement('div'); gain.id = 's12gain'; gain.dataset.testid = 's12-gain';
    const pan = document.createElement('div'); pan.id = 's12p'; pan.dataset.testid = 's12-panel';
    pan.innerHTML = `<div id="s12box" style="position:relative"><h3 data-testid="s12-title">每日小委託</h3><div class="s12tabs" data-testid="s12-tabs"></div><div id="s12body"></div></div><i class="s12x" data-testid="s12-close">✕</i>`;
    if (uiRoot) { uiRoot.appendChild(chip); uiRoot.appendChild(gain); uiRoot.appendChild(pan); }
    nine(pan.querySelector('#s12box'), 'panel_commission_9s', [18, 12, 12, 12]);
    const S12 = G.s12 = { tab: 'quest', tabs: [['quest', '委託'], ['bond', '親密']], open: false, log: [] };
    const now = () => G.now();
    function shardTxt() { const w = X.wallet(G.state, now()); return w; }
    function renderQuest() {
      const q = X.quests(G.state, now()), w = shardTxt(), RC = P.evo6.route.colors;
      if (!q.list.length) return `<div class="s12row" data-testid="s12-q-none"><span class="t">光卵孵咗先有委託㗎。</span></div>`;
      return q.list.map((x, i) => `<div class="s12row s12q" data-testid="s12-q-${i}" data-k="${x.k}" data-done="${x.n >= x.need ? 1 : 0}">${pimg(x.icon, 24)}<span class="t">${x.label}<small> ${Math.min(x.n, x.need)}/${x.need}</small>${x.route ? `<span class="rt" style="background:${RC[x.route] || '#888'}" data-testid="s12-q-route">${D.FORM_NAME[x.route] || x.route}</span>` : ''}</span>${pimg(x.n >= x.need ? 'checkbox_done' : 'checkbox_empty', 20)}</div>`).join('') +
        `<div class="s12foot"><span>3 個齊即刻 ${pimg('icon_star_shard_16', 16)} +${q.reward * q.list.length}${q.paid ? '（已領）' : ''}</span><span data-testid="s12-wallet">${pimg('icon_star_shard_16', 16)} ${w.total}｜今日 ${w.today}/${w.cap}</span></div>`;
    }
    // ── 系統 6：親密度＋心聲（心聲泡＝遊美 bubble_thought_9s＋tail）──
    const vb = document.createElement('div'); vb.id = 's12voice'; vb.dataset.testid = 's12-voice';
    vb.innerHTML = `<span data-testid="s12-voice-text"></span><img class="tail" src="${ART}bubble_thought_tail.png" alt="">`;
    if (uiRoot) uiRoot.appendChild(vb); nine(vb, 'bubble_thought_9s', [11, 11, 11, 11], 2);
    let vbHide = 0;
    function showVoice(r) {
      const b = NS.ui.petHitBox ? NS.ui.petHitBox() : { x: 80, y: 120, w: 36, h: 40 }; vb.querySelector('span').textContent = r.line;
      vb.style.opacity = 0; vb.style.left = '0px'; vb.style.top = '0px'; vb.style.display = 'block';
      const w = vb.offsetWidth, h = vb.offsetHeight, cx = (b.x + b.w / 2) * 2, x = Math.max(8, Math.min(390 - 8 - w, cx - w / 2)), y = Math.max(130, b.y * 2 - h - 26);
      vb.style.left = x + 'px'; vb.style.top = y + 'px'; vb.querySelector('.tail').style.left = Math.max(8, Math.min(w - 40, cx - x - 16)) + 'px'; vb.style.opacity = 1;
      clearTimeout(vbHide); vbHide = setTimeout(() => { vb.style.opacity = 0; }, C.bond.voice.showSec * 1000);
      S12.lastVoice = r; G.state.ev.push({ type: 'sys12', sys: 'bond', what: 'voice', line: r.line, tier: r.tier, src: r.src });
    }
    G.sysVoice = function (o) { const r = X.voiceTry(G.state, now(), o); if (r.ok) showVoice(r); S12.lastTry = r; return r; };
    /* ui.js 撳寵物鬆手：長撳（≥ SHORT_MS）→ 親密 +2；短撳 → 心聲（30%、冷卻 10 分鐘、同懸浮共用） */
    G.sysPress = function (p) { if (!p || G.state.stage === 'egg') return null; if (!p.short) return { bond: X.onLongPress(G.state, now(), G.state.ev) }; return { voice: G.sysVoice({ src: 'app' }) }; };
    function renderBond() {
      const s = G.state, b = X.bond(s, now()), L = C.bond.lines, mem = (s.memorial || []).slice(-6).reverse();
      return `<div data-testid="s12-bond-v">親密度 <b>${Math.round(b.v)}</b> / 100　第 ${b.tier} 段心聲<small>（今日 +${b.todayGain}/${b.cap}）</small></div><div class="s12bar"><i style="width:${b.v}%"></i></div>` +
        L.map((arr, i) => `<div class="s12tier">第 ${i + 1} 段（${(i + 1) * C.bond.tierEvery}）${i < b.tier ? '' : '🔒'}</div>` + arr.map(l => `<div class="s12line${i < b.tier ? '' : ' lock'}">${i < b.tier ? l : '？？？'}</div>`).join('')).join('') +
        `<div class="s12tier">紀念冊</div>` + (mem.length ? mem.map(m => `<div class="s12mem" data-testid="s12-mem">第 ${m.gen} 代・${D.FORM_NAME[m.form] || m.form || ''}　親密度 ${m.bond != null ? m.bond : '—'}${m.bondElder != null ? '（靜光 ' + m.bondElder + '）' : ''}${m.diary ? '　日記 ' + m.diary.length + ' 篇' : ''}</div>`).join('') : `<div class="s12mem">未有紀念</div>`);
    }
    const RENDER = { quest: renderQuest, bond: renderBond }; G.s12render = RENDER;
    G.s12dev = Object.assign(G.s12dev || {}, {   // DEV 抽屜（devpanel s12:<名>）
      bondUp: () => { const b = X.bondOf(G.state); b.v = Math.min(100, b.v + 10); lastChip = ''; return X.bond(G.state, now()); },
      bondDown: () => { const b = X.bondOf(G.state); b.v = Math.max(0, b.v - 10); return X.bond(G.state, now()); },
      voice: () => G.sysVoice({ force: true, src: 'dev' }), ignore: () => window.__qa.sys12.ignoreDay(), bondOpen: () => G.s12open('bond'),
    });
    function draw() {
      if (!S12.open) return; const body = pan.querySelector('#s12body'), tabs = pan.querySelector('.s12tabs');
      tabs.innerHTML = S12.tabs.length > 1 ? S12.tabs.map(([k, l]) => `<b data-tab="${k}" data-testid="s12-tab-${k}" class="${k === S12.tab ? 'on' : ''}">${l}</b>`).join('') : '';
      pan.querySelector('h3').textContent = { quest: '每日小委託', diary: '團絨日記', bond: '親密度', set: '小驚喜設定' }[S12.tab] || '';
      body.innerHTML = (RENDER[S12.tab] || renderQuest)();
      body.querySelectorAll('.s12row').forEach(r => { if (!r.dataset.nine) { r.dataset.nine = 1; nine(r, 'panel_commission_row_9s', [6, 6, 6, 6], 1.5); } });
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
      if (e.sys === 'bond' && e.what === 'tier') showGain(0, '親密度 ' + Math.round(e.v) + '：解鎖第 ' + e.tier + ' 段心聲');
      if (e.sys === 'quest' && e.what === 'step') { chip.classList.remove('pulse'); void chip.offsetWidth; chip.classList.add('pulse'); }
      lastChip = ''; chipTick();
      (G.sysListeners || []).forEach(fn => { try { fn(e); } catch (er) { } });
    };
    function questTick() { const ev = G.state.ev; X.questTick(G.state, now(), ev); X.bondTick(G.state, now(), ev); }
    G.sysTick = function (dt) { wx.acc += dt; if (wx.acc >= 1) { wx.acc = 0; G.wxTick(); questTick(); chipTick(); } petTick(dt); };
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
      bond: () => X.bond(G.state, G.now()), bondSet: (v) => { X.bondOf(G.state).v = Math.max(0, Math.min(100, v)); return X.bond(G.state, G.now()); }, voice: (o) => G.sysVoice(o || { force: true, src: 'dev' }), lastVoice: () => S12.lastVoice || null, lastTry: () => S12.lastTry || null,
      ignoreDay: () => { const b = X.bondOf(G.state), d = new Date(G.now()); d.setDate(d.getDate() - 2); b.chk = NS.sim.dayKey(d.getTime()); G.state.careDays = (G.state.careDays || []).filter(k => k !== NS.sim.dayKey(G.now() - 86400e3)); return X.bondTick(G.state, G.now(), G.state.ev); }, open: (tab) => G.s12open(tab), close: () => G.s12close(), log: () => S12.log.slice(),
    });
  }
  window.Glimmer = window.Glimmer || {}; window.Glimmer.sys12ui = { install };
})();
