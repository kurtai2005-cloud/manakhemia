/* 《微光小圃》 sys12ui2.js — systems12 第 2 批 UI（docs-gdd/systems12-v1.md）。原創代碼。
   掛喺第 1 批面板（G.s12）：加 4 個 tab（小遊戲／小圃／收藏／徽章）；捉迷藏 DOM 小遊戲；接光點經 ui.js startMG('catch')。
   散步收集：團絨每次開始「walk」擲一次（systems2.walkRoll）；每秒 tick：開花路線分＋徽章。冇改懸浮團絨（規格冇懸浮要求）。
   美術：收藏櫃用遊美 ACC1 col_<k>_32(_sil)＋18 件佔位 icon（tools/gen-placeholder-collectibles.py）；其餘（光點、匿位／露尾、花盆／花、飾品、徽章）未有 → 文字／色塊代替（報告列咗）。
   數值＝docs-gdd/systems12b-params.md。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.sys12ui2 = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  function install(G, NS) {
    const D = NS.data, P2 = D.PARAMS.systems12b, X2 = NS.sys12b, X = NS.sys12, UI = NS.ui, S12 = G.s12, RENDER = G.s12render;
    if (!X2 || !S12 || !RENDER) return false;
    const now = () => G.now(), S = () => G.state;
    const gain = (n, why) => { if (G.s12gain) G.s12gain(n, why); else if (UI && UI.toast) UI.toast(why); };
    const css = document.createElement('style'); css.textContent = `
      .s12tabs { flex-wrap:wrap; } .s12tabs b { min-width:22%; }
      .s12b-btn { display:inline-block; padding:4px 10px; margin:2px; border-radius:7px; background:#7a4a24; color:#fff6dc; cursor:pointer; font-weight:700; font-size:12px; min-height:28px; line-height:20px; }
      .s12b-btn.off { background:#b9a184; cursor:default; }
      .s12b-pot { display:flex; align-items:center; gap:6px; } .s12b-pot[data-state="empty"] { flex-wrap:wrap; } .s12b-pot[data-state="empty"] .t { flex:1 0 100%; } .s12b-pot[data-state="empty"] > div { display:flex; flex-wrap:wrap; } .s12b-pot .dot { width:18px; height:18px; border-radius:50%; flex:none; box-shadow:inset 0 -2px 0 rgba(0,0,0,.25); }
      .s12b-grid { display:grid; grid-template-columns:repeat(6, 1fr); gap:4px; } .s12b-grid div { aspect-ratio:1; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(74,46,26,.14); font-weight:700; color:#8a6a4a; }
      .s12b-grid div.got { background:#f3e1b8; } .s12b-badge { display:flex; justify-content:space-between; padding:3px 6px; border-bottom:1px dashed rgba(74,46,26,.25); } .s12b-badge.got b { color:#8a4f2a; } .s12b-badge:not(.got) { opacity:.55; }
      #s12hide { position:absolute; inset:0; z-index:45; display:none; flex-direction:column; align-items:center; justify-content:flex-end; padding-bottom:60px; background:rgba(5,7,26,.6); color:#fff6dc; font:13px/1.4 sans-serif; pointer-events:auto; }
      #s12hide .hd { font:700 16px sans-serif; margin-bottom:6px; } #s12hide .sp { display:flex; flex-wrap:wrap; justify-content:center; gap:10px; width:320px; margin:12px 0; }
      #s12hide .sp b { width:96px; height:72px; border-radius:12px; background:#5b3a22; display:flex; align-items:center; justify-content:center; text-align:center; cursor:pointer; box-shadow:inset 0 -4px 0 rgba(0,0,0,.3); }
      #s12hide .sp b.miss { background:#3a2a20; opacity:.6; } #s12hide .sp b.hit { background:#d9a440; color:#3a2a10; } #s12hide .sp b.tail { box-shadow:inset 0 -4px 0 rgba(0,0,0,.3), 0 0 0 2px #ffd35a; } #s12hide .sp b small { display:block; font-size:10px; color:#ffd35a; }
      .s12b-acc { display:flex; flex-wrap:wrap; gap:4px; margin-top:6px; } .s12b-acc span { padding:2px 6px; border-radius:6px; background:rgba(74,46,26,.14); font-size:11px; } .s12b-acc span.got { background:#f3e1b8; font-weight:700; }
    `; document.head.appendChild(css);
    const ROUTE_COL = { moon: '#7f8de0', bright: '#ffd35a', shroom: '#c46a5a', crystal: '#8fe0e8', ember: '#ff8a3a', tide: '#5ab4ff' };
    const STAGE_TXT = { '-1': '枯咗', 0: '種子', 1: '芽', 2: '花苞', 3: '開花' }, H2 = P2.games.hide, K2 = P2.games.catch, G2 = P2.garden;
    const cimg = (k, sil, px) => `<img data-s12b="col_${k}_32${sil ? '_sil' : ''}" width="${px}" height="${px}" style="image-rendering:pixelated;width:${px}px;height:${px}px" alt="">`;
    const hyd = r => { r.querySelectorAll('img[data-s12b]').forEach(i => { i.src = 'art/collectibles/' + i.dataset.s12b + '.png'; i.removeAttribute('data-s12b'); }); };
    const btn = (txt, act, tid, on) => `<span class="s12b-btn${on === false ? ' off' : ''}" data-act="${on === false ? '' : act}" data-testid="${tid}">${txt}</span>`;

    // ── tab 渲染 ──
    function renderGames() {
      const g = X2.gamesToday(S(), now()), C = P2.games, b = X2.st(S()).games.best;
      return `<div data-testid="s12b-games-left">今日有獎 ${g.cap - g.left}/${g.cap} 局（星星碎＝星數 0–3；之後照玩、照計火苗）</div>` +
        (G.mg2rows ? G.mg2rows(btn) : '') + (!C.v1Enabled ? '' :
        `<div class="s12row"><span class="t">${C.catch.name}<small> ${C.catch.durationSec} 秒：光點 +${K2.dots.small}、金 +${K2.dots.big}、暗 ${K2.dots.dark}；${K2.starsAt.join('／')} 分＝1／2／3★・最高 ${b.catch || 0}</small></span>${btn('開始', 'catch', 's12b-play-catch')}</div>` +
        `<div class="s12row"><span class="t">${C.hide.name}<small> ${H2.rounds} 回合，每回合撳 ≤${H2.triesPerRound} 下（${H2.ptsByTry.join('／')} 分）；${H2.starsAt.join('／')} 分＝1／2／3★・最好 ${b.hide || 0} 分</small></span>${btn('開始', 'hide', 's12b-play-hide')}</div>`);   // 舊接光點／舊捉迷藏：v1Enabled 先出
    }
    function renderGarden() {
      const gd = X2.garden(S(), now()), w = X.wallet(S(), now()), egg = S().stage === 'egg';
      const pots = gd.pots.map((p, i) => {
        if (p.empty) return `<div class="s12row s12b-pot" data-testid="s12b-pot-${i}" data-state="empty"><span class="t">空花盆 ${i + 1}<small> 種子 ${gd.price} 星星碎</small></span><div>${gd.flowers.map(f => btn(f.name, 'plant:' + i + ':' + f.k, 's12b-plant-' + i + '-' + f.k, !egg && w.total >= gd.price)).join('')}</div></div>`;
        const act = p.bloomed ? btn('剪落花瓶', 'harvest:' + i, 's12b-harvest-' + i) : p.wilted ? btn('清走', 'harvest:' + i, 's12b-clear-' + i) : btn(p.wateredToday ? '今日淋咗' : '淋水', 'water:' + i, 's12b-water-' + i, !p.wateredToday);
        return `<div class="s12row s12b-pot" data-testid="s12b-pot-${i}" data-state="${p.bloomed ? 'bloom' : p.wilted ? 'wilted' : p.droop ? 'droop' : 'grow'}" data-stage="${p.stage}"><span class="dot" style="background:${p.wilted ? '#6b5a48' : ROUTE_COL[p.route] || '#ccc'};opacity:${0.35 + Math.max(0, p.stage) * 0.22};${p.droop ? 'transform:translateY(3px) scaleY(.8)' : ''}"></span><span class="t">${p.name}・${STAGE_TXT[p.stage]}${p.droop ? '（垂頭）' : ''}<small> ${p.bloomed ? '開咗！' : p.wilted ? '冇水枯咗（團絨冇事）' : p.droop ? '琴日冇淋水，今日再唔淋就枯' : '淋水 ' + p.growth + '/' + p.need + ' 日'}</small></span>${act}</div>`;
      }).join('');
      const vase = Object.keys(gd.vase).map(k => (gd.flowers.find(f => f.k === k) || {}).name + '×' + gd.vase[k]).join('　');
      const hint = gd.hint.map(h => `<div style="font-size:11px;margin-top:4px" data-testid="s12b-hint-${h.route}">${D.FORM_NAME[h.route] || h.route}提示：${h.text}</div>`).join('');
      return `<div style="font-size:12px;margin-bottom:6px" data-testid="s12b-garden-wallet">星星碎 ${w.total}・種子 ${gd.price}・每日淋一次水升一階，最快 2 日開花；開花該路線 +${G2.bloomPts}（日菊：+${G2.daisy.shards} 星星碎＋燦光提示）；${G2.droopDryDays} 日冇水垂頭、${G2.wiltDryDays} 日枯</div>${pots}` +
        `<div style="font-size:11px;opacity:.75;margin-top:6px" data-testid="s12b-vase">花瓶：${vase || '未有'}（第 3 批房間先擺得）</div>${hint}`;
    }
    function renderCab() {
      const c = X2.cabinet(S());
      return `<div data-testid="s12b-cab-count" style="margin-bottom:6px">收藏 ${c.unique}/${c.slots.length}・今日執咗 ${c.today}/${c.perDay}</div><div class="s12b-grid" data-testid="s12b-cab">` +
        c.slots.map((x, i) => x.locked ? `<div data-testid="s12b-slot-${i}" data-locked="1">？</div>` : `<div class="${x.got ? 'got' : ''}" data-testid="s12b-slot-${i}" data-k="${x.k}" data-got="${x.got}"${x.ph ? ' data-ph="1"' : ''} title="${x.name}">${cimg(x.k, !x.got, 32)}</div>`).join('') + '</div>' +
        `<div style="font-size:12px;margin-top:8px" data-testid="s12b-acc-count">飾品 ${c.acc.filter(a => a.got).length}/${c.acc.length}（每 ${P2.walk.accPer} 件唔同小物解鎖 1 件）</div><div class="s12b-acc" data-testid="s12b-acc">` +
        c.acc.map(a => `<span class="${a.got ? 'got' : ''}" data-testid="s12b-acc-${a.k}" data-got="${a.got ? 1 : 0}">${a.got ? a.name : '？（' + a.need + ' 件）'}</span>`).join('') + '</div>';
    }
    function renderBadge() {
      const b = X2.badges(S());
      return `<div data-testid="s12b-badge-count" style="margin-bottom:6px">徽章 ${b.have}/${b.total}${b.title ? '・稱號「' + b.title + '」' : ''}</div>` +
        b.list.map(x => `<div class="s12b-badge${x.got ? ' got' : ''}" data-testid="s12b-badge-${x.k}" data-got="${x.got ? 1 : 0}"${x.big ? ' data-big="1"' : ''}><b>${x.got ? '★' : '☆'} ${x.name}${x.big ? '（大）' : ''}</b><small>${x.got ? '已得' : '+' + x.reward + ' 星星碎'}${x.title ? '・稱號「' + x.title + '」' : ''}</small></div>`).join('') +
        `<div style="font-size:11px;opacity:.7;margin-top:6px">徽章星星碎一次性、唔計每日上限</div>`;
    }
    Object.assign(RENDER, { games: renderGames, garden: renderGarden, cab: renderCab, badge: renderBadge });
    G.s12titles = Object.assign(G.s12titles || {}, { games: '小遊戲', garden: '小圃種花', cab: '收藏櫃', badge: '成就徽章' });
    S12.tabs.push(['games', '小遊戲'], ['garden', '小圃'], ['cab', '收藏'], ['badge', '徽章']);
    const redraw = () => { if (S12.open && G.s12draw) G.s12draw(); };
    (G.s12afterDraw = G.s12afterDraw || []).push(hyd);   // 第 1 批 draw 之後 hydrate 收藏櫃圖
    const pan = document.getElementById('s12p');
    if (pan) pan.addEventListener('click', e => {   // 第 2 批 tab 入面嘅掣（data-act）
      const a = e.target.closest('[data-act]'); if (!a || !a.dataset.act) return; doAct(a.dataset.act);
    });
    function doAct(act) {
      const [k, i, f] = act.split(':'), s = S(); let r = null;
      if ((k === 'catch' || k === 'hide') && !P2.games.v1Enabled) return false;   // 舊遊戲閂咗（config games.v1Enabled）
      if (k === 'catch') { G.s12close(); if (UI.startMG) UI.startMG('catch'); return true; }
      if (k === 'hide') { G.s12close(); return hideStart(); }
      if (k === 'mg2') { G.s12close(); return G.mg2 ? G.mg2.start(i) : false; }   // 小遊戲 v2
      if (k === 'plant') { r = X2.plant(s, +i, f, now()); if (!r.ok) UI.toast({ shards: '星星碎唔夠', egg: '光卵仲未孵化', busy: '呢盆有嘢種緊' }[r.reason] || '種唔到'); }
      if (k === 'water') { r = X2.water(s, +i, now()); if (!r.ok && r.reason === 'done') UI.toast('今日淋咗喇'); }
      if (k === 'harvest') r = X2.harvest(s, +i, now());
      G.save(); redraw(); return r;
    }

    // ── 捉迷藏（DOM；直向單手：大掣喺下半）──
    const hb = document.createElement('div'); hb.id = 's12hide'; hb.dataset.testid = 's12b-hide';
    (document.getElementById('ui') || document.body).appendChild(hb);
    ['pointerdown', 'touchstart', 'mousedown', 'click'].forEach(tp => hb.addEventListener(tp, e => e.stopPropagation()));
    let H = null;
    function hideDraw(flash) {
      if (!H) return; const g = H.g;
      hb.innerHTML = `<div class="hd">${P2.games.hide.name}</div><div data-testid="s12b-hide-info">${hideInfo(g)}</div>` +
        `<div class="sp">${g.spots.map((n, i) => `<b data-i="${i}" data-testid="s12b-spot-${i}" class="${g.tried.includes(i) ? 'miss' : ''}${g.tail && i === g.at ? ' tail' : ''}"${g.tail && i === g.at ? ' data-tail="1"' : ''}>${n}${g.tail && i === g.at ? '<small>露咗條尾？</small>' : ''}</b>`).join('')}</div>` +
        `<div data-testid="s12b-hide-msg" style="min-height:18px">${flash || (g.tail ? '團絨：「' + H2.tailLine + '」' : '團絨匿埋咗，佢喺邊？')}</div><span class="s12b-btn" data-testid="s12b-hide-quit" data-q="1">唔玩</span>`;
    }
    function hideInfo(g) { return `第 ${Math.min(g.round + 1, g.H.rounds)}/${g.H.rounds} 回合・${g.score} 分・剩 ${Math.ceil(g.left)} 秒・仲可以撳 ${g.tries} 下`; }
    hb.addEventListener('click', e => {
      if (!H) return; if (e.target.closest('[data-q]')) return hideEnd(true);
      const b = e.target.closest('[data-i]'); if (!b) return; const r = H.g.pick(+b.dataset.i); if (!r.ok) return;
      hideDraw(r.hit ? '第 ' + r.tryN + ' 下搵到團絨！+' + r.pts + ' 分' : r.roundOver ? '團絨自己由「' + H.lastSpots[r.at] + '」行出嚟扮勝利（0 分）' : '唔喺度…');
      H.lastSpots = H.g.spots.slice(); if (r.over) setTimeout(() => hideEnd(false), 500);
    });
    function hideStart(seed) {
      const s = S(); if (s.stage === 'egg') { UI.toast('光卵仲未孵化'); return false; } if (s.sleeping) { UI.toast('團絨瞓緊，先開燈'); return false; }
      const g = new X2.HideGame(seed || G.fixedHideSeed || ((Date.now() & 0xffffff) | 1)); H = { g, lastSpots: g.spots.slice(), done: false };
      hb.style.display = 'flex'; hideDraw(); return true;
    }
    function hideEnd(quit) {
      if (!H || H.done) return null; H.done = true; const g = H.g; H = null; hb.style.display = 'none';
      if (quit) { G.save(); return null; }
      const r = X2.gameFinish(S(), 'hide', g.score, now(), { firstHits: g.firstHits }); G.lastHide = r; if (UI.processEvents) UI.processEvents();
      UI.modal({ title: P2.games.hide.name + '完成', kind: 'mg-result', lines: ['得分 ' + g.score + '（搵到 ' + g.found + '/' + g.H.rounds + ' 回合）　' + '★'.repeat(r.stars) + '☆'.repeat(3 - r.stars), r.rewarded ? '星星碎 +' + r.shards + '（今日有獎 ' + r.playIndex + '/' + P2.games.dailyRewarded + '）' : '今日 ' + P2.games.dailyRewarded + ' 局獎勵已滿（照計火苗）'] });
      G.save(); return r;
    }
    G.s12hide = hideStart;

    // ── 通知 ──
    (G.sysListeners = G.sysListeners || []).push(e => {
      if (e.sys === 'walk' && e.what === 'pickup') gain(0, '團絨執到「' + e.name + '」' + (e.first ? '（新！）' : ''));
      if (e.sys === 'walk' && e.what === 'acc') gain(0, '解鎖飾品「' + e.name + '」');
      if (e.sys === 'garden' && e.what === 'bloom') gain(e.n || 0, e.name + '開花喇' + (e.pts ? '（' + (D.FORM_NAME[e.route] || '') + ' +' + e.pts + '）' : '') + (e.hint ? '・燦光提示：' + e.hint.text + '（已記入圖鑑燦光頁）' : ''));
      if (e.sys === 'garden' && e.what === 'wilt') gain(0, e.name + '冇水枯咗，花冇咗（團絨冇事）');
      if (e.sys === 'badge' && e.what === 'got') gain(e.n, '徽章「' + e.name + '」' + (e.title ? '・稱號「' + e.title + '」' : ''));
      redraw();
    });

    // ── tick：散步擲骰（walk 開始一刻）＋每秒開花／徽章 ──
    let prevBeh = null, acc = 0;
    const origTick = G.sysTick;
    G.sysTick = function (dt) {
      if (origTick) origTick(dt);
      const b = G.beh, st = b ? b.state : null;
      if (st === 'walk' && prevBeh !== 'walk' && G.mode !== 'minigame' && !S().sleeping) X2.walkRoll(S(), now());
      prevBeh = st;
      if (H) { H.g.update(dt); if (H.g.over) hideEnd(false); else { const inf = hb.querySelector('[data-testid="s12b-hide-info"]'); if (inf) inf.textContent = hideInfo(H.g); } }
      acc += dt; if (acc >= 1) { acc = 0; X2.tick(S(), now()); }
    };
    X2.tick(S(), now());

    // ── DEV（devpanel s12:<名>）＋ QA ──
    const forcePick = () => { const W = X2.st(S()).walk; return X2.walkRoll(S(), now(), { force: true, noRare: true }) || (W.count >= P2.walk.perDay ? 'cap' : null); };
    G.s12dev = Object.assign(G.s12dev || {}, {
      gamesOpen: () => G.s12open('games'), catch: () => doAct('catch'), hide: () => doAct('hide'),
      gamesReset: () => { const g = X2.st(S()).games; g.plays = 0; redraw(); return true; },
      gardenOpen: () => G.s12open('garden'),
      gardenPlant: () => { const w = X.st(S()).wallet; if (w.total < P2.garden.seedPrice) w.total += P2.garden.seedPrice; const i = X2.st(S()).garden.pots.findIndex(p => !p); return i < 0 ? null : doAct('plant:' + i + ':' + P2.garden.flowers[(i * 2) % 6].k); },
      gardenWater: () => { const r = X2.st(S()).garden.pots.map((p, i) => p ? X2.water(S(), i, now()).ok : false); G.save(); redraw(); return r; },
      gardenDay: () => { X2.st(S()).garden.pots.forEach(p => { if (p) { p.planted -= 1; p.w = p.w.map(d => d - 1); } }); X2.tick(S(), now()); G.save(); redraw(); return X2.garden(S(), now()).pots.map(p => p.stage); },
      cabOpen: () => G.s12open('cab'), pick: () => { const r = forcePick(); G.save(); redraw(); return r; },
      pickReset: () => { X2.st(S()).walk.count = 0; redraw(); return true; },
      badgeOpen: () => G.s12open('badge'), badgeCheck: () => { const r = X2.badgeCheck(S(), now()); G.save(); redraw(); return r; },
      badgeReset: () => { const B = X2.st(S()).badges; B.got = {}; B.pending = 0; B.title = ''; B.titles = []; redraw(); return true; },
    });
    window.__qa = window.__qa || {};
    window.__qa.sys12b = { st: () => JSON.parse(JSON.stringify(X2.st(S()))), games: () => X2.gamesToday(S(), now()), garden: () => X2.garden(S(), now()), cabinet: () => X2.cabinet(S()), badges: () => X2.badges(S()),
      hideStart, hideState: () => (H ? { at: H.g.at, spots: H.g.spots.slice(), round: H.g.round, found: H.g.found, score: H.g.score, tries: H.g.tries, tail: H.g.tail, left: H.g.left } : null), accessories: () => X2.accessories(S()), hidePick: i => { const b = hb.querySelector('[data-i="' + i + '"]'); if (b) b.click(); return !!b; },
      act: doAct, walkRoll: o => X2.walkRoll(S(), now(), o), lastHide: () => G.lastHide || null };
    return true;
  }
  return { install };
});
