/* 《微光小圃》 ui.js — 輸入、HUD、彈窗、迷你遊戲流程、debug 面板（?debug=1）。原創代碼。 */
(function (root, factory) {
  root.Glimmer = root.Glimmer || {};
  root.Glimmer.ui = factory(root.Glimmer.data, root.Glimmer.sim, root.Glimmer.render);
})(typeof self !== 'undefined' ? self : this, function (D, SIM, R) {
  'use strict';
  const P = D.PARAMS;
  const $ = (s, r) => (r || document).querySelector(s);
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  let G, rd;
  const NS_BEH = { tap: (b, k, x, y, o) => window.Glimmer.behavior.tap(b, k, x, o && o.hold ? y : undefined, o), drag: (b, x, y) => window.Glimmer.behavior.drag(b, x, y), dragEnd: (b) => window.Glimmer.behavior.dragEnd(b) };
  const EVN = () => window.Glimmer.events, LT = () => window.Glimmer.light;
  const SND = (k, i) => { const a = window.Glimmer.audio; if (a && a.Engine) a.Engine.notify(k, i); };   // 音訊 cue 通知（audio.js Director 決定播咩）
  const UI = {};
  let modalQ = [], modalOpen = false, toastT = 0, popKind = null, mgs = null, lastBubble = '', evtCool = 0;

  // ── 像素圖示（程序化，10×10）──
  function iconCanvas(rows, pal) {
    const c = document.createElement('canvas'); c.width = 10; c.height = 10; const x = c.getContext('2d');
    rows.forEach((r, j) => { for (let i = 0; i < r.length; i++) if (pal[r[i]]) { x.fillStyle = pal[r[i]]; x.fillRect(i, j, 1, 1); } });
    return c;
  }
  const ICONS = {
    feed: [['..........', '...dddd...', '..dccccd..', '.dcchcccd.', '.dccccdcd.', '.dcdcccccd', '.dccccchcd', '..dccdcd..', '...dddd...', '..........'], { d: '#a8683a', c: '#f0bc6a', h: '#fff0b0' }],
    play: [['...dddd...', '..dyyyyd..', '.dyhhyyyd.', 'dyhyyyyyyd', 'dyyyydyyyd', 'dyyyyyyyyd', 'dyyyyyyydd', '.dyyyyydd.', '..ddddd...', '..........'], { d: '#b8501a', y: '#ff9a4a', h: '#fff0c8' }],
    clean: [['....bb....', '...bbbb...', '..bbhbbb..', '..bhbbbb..', '.bbhbbbbb.', '.bbbbbbdb.', '.bbbbbbdb.', '..bbbbdd..', '...dddd...', '..........'], { b: '#6ac8ff', h: '#e8f8ff', d: '#2a78c0' }],
    sleep: [['...mmmm...', '..mmmmm...', '.mmmm.....', '.mmmm.....', '.mmmm.....', '.mmmm.....', '.mmmmm....', '..mmmmmmm.', '...mmmmm..', '..........'], { m: '#cfe0ff' }],
  };
  function fillIcon(cv, key) { const [rows, pal] = ICONS[key]; const c = iconCanvas(rows, pal); cv.getContext('2d').clearRect(0, 0, 10, 10); cv.getContext('2d').drawImage(c, 0, 0); }

  function toast(msg, ms) { const t = $('#toast'); t.textContent = msg; t.style.display = 'block'; toastT = (ms || 1700) / 1000; }
  function closePop() { popKind = null; $('#pop').style.display = 'none'; }

  function modal(o) { modalQ.push(o); if (!modalOpen) nextModal(); }
  function nextModal() {
    const o = modalQ.shift();
    if (!o) { modalOpen = false; $('#modal').style.display = 'none'; return; }
    modalOpen = true; closePop();
    const b = $('#mbox');
    b.innerHTML = '';
    const h = document.createElement('h2'); h.textContent = o.title || ''; b.appendChild(h);
    (o.lines || []).forEach(l => { const p = document.createElement('p'); p.textContent = l; b.appendChild(p); });
    if (o.node) b.appendChild(o.node);
    const btns = o.buttons || [{ text: '好', primary: true }];
    const wrap = document.createElement('div');
    btns.forEach((bt, i) => {
      const e = document.createElement('div'); e.className = 'btn' + (bt.primary ? '' : ' sec'); e.textContent = bt.text; e.dataset.testid = 'modal-btn-' + i;
      e.addEventListener('click', () => { if (!bt.silent) SND(bt.primary ? 'confirm' : 'cancel'); const keep = bt.onClick && bt.onClick() === false; if (!keep) { if (bt.onClick || true) { /* close */ } $('#modal').style.display = 'none'; modalOpen = false; if (o.onClose) o.onClose(); nextModal(); } });
      wrap.appendChild(e);
    });
    b.appendChild(wrap);
    $('#modal').style.display = 'flex';
    b.dataset.kind = o.kind || '';
  }

  // ── 事件處理（來自 sim 嘅 ev）──
  function processEvents() {
    const s = G.state, ev = s.ev.splice(0, s.ev.length);
    for (const e of ev) {
      const pd = rd.petDraw, hx = pd && pd.bud ? pd.bud.x : R.CX, hy = pd ? pd.y + 20 : R.GROUND_Y - 40;
      if (e.type === 'fed') { const fd = D.FOODS.find(x => x.id === e.food); SND('fed', { kind: fd ? fd.kind : 'snack' }); rd.food = { id: e.food, until: rd.t + 1.1, dur: 1.1 }; rd.act('eat', 1.1); setTimeout(() => rd.burst('heart', R.CX, R.GROUND_Y - 50, 2, 30), 700); }
      else if (e.type === 'played') { SND('played'); rd.ball = { until: rd.t + 1.6, dur: 1.6 }; rd.act('happy', 1.6); rd.burst('heart', R.CX, R.GROUND_Y - 55, 3, 40); }
      else if (e.type === 'rinsed') { SND('rinsed'); rd.wash = { until: rd.t + 1.4, dur: 1.4 }; rd.act('happy', 1.4); rd.burst('spark', R.CX, R.GROUND_Y - 40, 4, 50); }
      else if (e.type === 'poopCleared') { SND('poop'); rd.burst('spark', R.CX, R.GROUND_Y - 20, 3, 40); }
      else if (e.type === 'eggTap') { SND('tap'); rd.eggPulse = 1; rd.act && 0; rd.burst('spark', R.CX, R.GROUND_Y - 24, 3, 40); }
      else if (e.type === 'wake') { toast('團絨瞓醒咗，精神晒！'); SND('sleep', { on: false }); }
      else if (e.type === 'hatch') {
        SND('hatch'); rd.flash = 1.2; rd.burst('spark', R.CX, R.GROUND_Y - 24, 14, 90);
        modal({ title: '孵化咗！', kind: 'hatch', lines: ['光卵裂開，一團暖暖嘅絨球探出頭嚟。', '佢係「團絨」，頭頂有撮會發光嘅小絨芽。', '餵食、玩耍、清潔、關燈瞓覺——慢慢陪佢長大。'], onClose: () => { rd.act('celebrate', 1.0); } });
      } else if (e.type === 'evolve') {
        SND('evolve'); rd.flash = 1.4; rd.burst('spark', R.CX, R.GROUND_Y - 40, 18, 110);
        const t = { bright: ['燦光形態！', '絨芽放射出光芒，你照顧得好好，佢成為最亮嘅守夜者。'], soft: ['柔光形態', '圓潤又溫柔，伴你度過每個夜晚。'], dust: ['微塵形態', '素素地都好靚。呢個唔係失敗結局，日後可以再重養。'], lumi: ['螢絨形態（隱藏）', '你陪佢喺夜晚追過螢火，佢身上嘅絨毛開始發出淡淡螢光。'] }[e.form] || [D.FORM_NAME[e.form] || e.form, ''];
        modal({ title: '成長為守夜者：' + t[0], kind: 'evolve', lines: [t[1], '（照顧品質 CQ ＝ ' + Math.round(e.cq) + '）'], onClose: () => rd.act('celebrate', 1.0) });
      }
    }
  }

  // ── 行動 ──
  function reasonMsg(r, what) {
    return { egg: '光卵仲未孵化，先輕點佢啦', sleeping: '團絨瞓緊，先開燈', full: '團絨食唔落喇', notSleepy: '團絨未眼瞓，瞓唔著' }[r] || '而家做唔到';
  }
  const act = {
    feed(id) { const r = SIM.feed(G.state, id); if (!r.ok) { toast(reasonMsg(r.reason)); SND('error'); } closePop(); processEvents(); G.save(); },
    play() { const r = SIM.play(G.state); if (!r.ok) { toast(reasonMsg(r.reason)); SND('error'); } closePop(); processEvents(); G.save(); },
    rinse() { const r = SIM.rinse(G.state); if (!r.ok) { toast(reasonMsg(r.reason)); SND('error'); } closePop(); processEvents(); G.save(); },
    sleep() { const r = SIM.toggleSleep(G.state); if (!r.ok) { toast(reasonMsg(r.reason)); SND('error'); } else { toast(r.sleeping ? '關燈，晚安 ☾' : '開燈喇'); SND('sleep', { on: r.sleeping }); } closePop(); G.save(); },
  };
  function showPop(kind) {
    const s = G.state;
    if (popKind === kind) return closePop();
    if (s.stage === 'egg') return toast('光卵仲未孵化，先輕點佢啦');
    SND('tap'); popKind = kind; const el = $('#pop'); el.innerHTML = ''; el.style.display = 'flex';
    const item = (iconKey, name, note, fn, id) => { const d = document.createElement('div'); d.className = 'pitem'; d.dataset.testid = id; const cv = document.createElement('canvas'); cv.width = 10; cv.height = 10; d.appendChild(cv); if (iconKey) fillIcon(cv, iconKey); const sp = document.createElement('span'); sp.textContent = name; d.appendChild(sp); const sm = document.createElement('small'); sm.textContent = note; d.appendChild(sm); d.addEventListener('click', fn); el.appendChild(d); };
    if (kind === 'feed') {
      const mapIcon = { snack: 'feed', meal: 'feed', soup: 'feed' };
      D.FOODS.forEach(f => item('feed', f.name, f.note, () => act.feed(f.id), 'food-' + f.id));
    } else if (kind === 'play') {
      item('play', '逗玩', '心情 +' + P.playTease, () => act.play(), 'play-tease');
      const left = G.state.mg.day === SIM.dayKey(G.now()) ? Math.max(0, P.mg.dailyFull - G.state.mg.plays) : P.mg.dailyFull;
      item('feed', '接星屑', left > 0 ? '今日全額 ' + left + '/' + P.mg.dailyFull : '今日獎勵減半', () => startMG(), 'play-mg');
    }
  }

  // ── 迷你遊戲 ──
  function startMG() {
    const s = G.state;
    if (s.stage === 'egg') return toast('光卵仲未孵化');
    if (s.sleeping) return toast('團絨瞓緊，先開燈');
    closePop();
    mgs = { mg: new SIM.Minigame((Date.now() & 0xffffff) | 1), ready: 1.6, target: P.mg.fieldW / 2, done: false };
    if (G.fixedMgSeed) mgs.mg = new SIM.Minigame(G.fixedMgSeed);
    G.mode = 'minigame'; SND('mg-start');
    $('#hud').style.display = 'none'; $('#bar').style.display = 'none'; $('#bubble').style.display = 'none'; $('#mgHud').style.display = 'block';
    rd.parT.x = 0; rd.parT.y = 0; rd.parT.active = true; rd.parT.last = rd.t + 1e6;
  }
  function endMG(quit) {
    const s = G.state; const m = mgs; mgs = null; G.mode = 'garden';
    $('#hud').style.display = 'block'; $('#bar').style.display = 'flex'; $('#mgHud').style.display = 'none'; $('#mgMsg').style.display = 'none';
    rd.parT.last = -99;
    if (quit) { G.save(); return; }
    const r = SIM.mgApply(s, m.mg.score, G.now());
    G.lastMG = r; SND('mg-result', { win: m.mg.score >= P.mg.passScore });
    const lines = ['得分 ' + r.score + (m.mg.score >= P.mg.highScore ? '　高分！' : m.mg.score >= P.mg.passScore ? '　及格' : ''), '光粒 +' + r.grains + '　心情 +' + r.mood];
    lines.push(r.full ? '今日全額 ' + Math.min(r.playIndex, P.mg.dailyFull) + '/' + P.mg.dailyFull : '今日全額次數已用完，獎勵減半');
    modal({ title: '接星屑完成', kind: 'mg-result', lines, onClose: () => { rd.act('happy', 1.6); rd.burst('heart', R.CX, R.GROUND_Y - 55, 4, 50); } });
    G.save();
  }
  function mgUpdate(dt) {
    const m = mgs; if (!m) return;
    const msg = $('#mgMsg');
    if (m.ready > 0) {
      m.ready -= dt; msg.style.display = 'block'; msg.textContent = m.ready > 0.5 ? '左右拖動籃子' : '開始！';
      if (m.ready <= 0) msg.style.display = 'none'; return;
    }
    m.mg.update(dt, m.target);
    if (m.mg.snd.length) { m.mg.snd.splice(0).forEach(k => SND('mg-' + k)); }
    $('#mgScore').textContent = '分數 ' + m.mg.score; $('#mgTime').textContent = Math.ceil(P.mg.durationSec - m.mg.t);
    if (m.mg.over && !m.done) { m.done = true; setTimeout(() => endMG(false), 300); }
  }

  // ── 設定 ──
  function openSettings() {
    const s = G.state;
    const node = document.createElement('div');
    const mkSeg = () => { const seg = document.createElement('div'); seg.className = 'seg'; [['off', '關'], ['low', '低'], ['mid', '中'], ['high', '高']].forEach(([k, n]) => { const b = document.createElement('div'); b.className = 'btn' + (s.settings.quality === k ? ' on' : ''); b.textContent = n; b.dataset.testid = 'q-' + k; b.addEventListener('click', () => { G.setQuality(k); seg.querySelectorAll('.btn').forEach(x => x.classList.remove('on')); b.classList.add('on'); }); seg.appendChild(b); }); return seg; };
    const lab = document.createElement('div'); lab.className = 'row'; lab.textContent = '畫質（後處理）'; node.appendChild(lab); node.appendChild(mkSeg());
    const hint = document.createElement('div'); hint.style.cssText = 'font-size:11px;opacity:.75;text-align:left;margin-bottom:4px'; hint.textContent = '高：景深＋bloom＋移軸＋暈影　中：景深（降頻）＋bloom　低：只有暈影　關：無後處理'; node.appendChild(hint);
    const r2 = document.createElement('div'); r2.className = 'row'; r2.innerHTML = '<span>夜間「就寢建議」提示</span>'; const tg = document.createElement('div'); tg.className = 'btn' + (s.settings.autoSuggest ? '' : ' sec'); tg.style.cssText = 'margin:0;padding:6px 16px'; tg.dataset.testid = 'toggle-suggest'; tg.textContent = s.settings.autoSuggest ? '開' : '關'; tg.addEventListener('click', () => { s.settings.autoSuggest = !s.settings.autoSuggest; tg.textContent = s.settings.autoSuggest ? '開' : '關'; tg.classList.toggle('sec', !s.settings.autoSuggest); G.save(); }); r2.appendChild(tg); node.appendChild(r2);
    const rs = document.createElement('div'); rs.className = 'row'; rs.innerHTML = '<span>聲音（配樂＋音效）</span>'; const sg = document.createElement('div'); sg.className = 'btn' + (s.settings.sound !== false ? '' : ' sec'); sg.style.cssText = 'margin:0;padding:6px 16px'; sg.dataset.testid = 'toggle-sound'; sg.textContent = s.settings.sound !== false ? '開' : '關';
    sg.addEventListener('click', () => { s.settings.sound = s.settings.sound === false; sg.textContent = s.settings.sound ? '開' : '關'; sg.classList.toggle('sec', !s.settings.sound); window.Glimmer.audio.Engine.setEnabled(s.settings.sound); G.save(); }); rs.appendChild(sg); node.appendChild(rs);
    const lv = document.createElement('div'); lv.className = 'row'; lv.textContent = '音量'; node.appendChild(lv);
    const vseg = document.createElement('div'); vseg.className = 'seg'; [['low', '細'], ['mid', '中'], ['high', '大']].forEach(([k, n]) => { const b = document.createElement('div'); b.className = 'btn' + ((s.settings.volume || 'high') === k ? ' on' : ''); b.textContent = n; b.dataset.testid = 'vol-' + k; b.addEventListener('click', () => { s.settings.volume = k; window.Glimmer.audio.Engine.setVolume(k); vseg.querySelectorAll('.btn').forEach(x => x.classList.remove('on')); b.classList.add('on'); G.save(); }); vseg.appendChild(b); }); node.appendChild(vseg);
    const r3 = document.createElement('div'); r3.className = 'row'; r3.innerHTML = '<span>重設存檔（重新開始）</span>'; const rb = document.createElement('div'); rb.className = 'btn sec'; rb.style.cssText = 'margin:0;padding:6px 16px'; rb.dataset.testid = 'reset-save'; rb.textContent = '重設'; let armed = false;
    rb.addEventListener('click', () => { if (!armed) { armed = true; rb.textContent = '再按確認'; return; } G.resetSave(); }); r3.appendChild(rb); node.appendChild(r3);
    modal({ title: '設定', node, kind: 'settings', buttons: [{ text: '關閉', primary: true, onClick: () => G.save() }] });
  }

  // ── 日記（離線溢出事件；可領獎，留 14 日）──
  function openDiary() {
    const s = G.state, EV = EVN(); EV.pruneDiary(s, G.now());
    const groups = EV.diaryGroups(s), total = EV.diary(s).length, node = document.createElement('div');
    if (!groups.length) { const p = document.createElement('p'); p.textContent = '日記入面暫時冇未領嘅小事。你唔喺度嘅時候，團絨如果有多過兩件事，就會記喺呢度，留 ' + P.events.diaryKeepDays + ' 日。'; p.style.fontSize = '13px'; node.appendChild(p); }
    const warn = EV.diaryWarn(s, G.now());
    if (warn) { const w = document.createElement('p'); w.dataset.testid = 'diary-warn'; w.textContent = '⚠ 有 ' + warn + ' 件小事 2 日後作廢（日記只留 ' + P.events.diaryKeepDays + ' 日），記得領。'; w.style.cssText = 'font-size:12px;color:#ffd27a;margin:0 0 6px'; node.appendChild(w); }
    groups.forEach((d, i) => {
      const row = document.createElement('div'); row.className = 'row'; row.dataset.testid = 'diary-row-' + d.id; row.style.cssText += ';font-size:13px';
      row.innerHTML = '<span><b>' + d.name + (d.n > 1 ? ' ×' + d.n : '') + '</b><br><small style="opacity:.8">' + d.flavor + '</small></span>';
      const bt = document.createElement('div'); bt.className = 'btn'; bt.style.cssText = 'margin:0 0 0 8px;padding:5px 10px;font-size:12px;white-space:nowrap'; bt.textContent = '領 ✦' + d.grains; bt.dataset.testid = 'diary-claim-' + d.id;
      bt.addEventListener('click', (e) => { e.stopPropagation(); const r = EV.claim(s, d.id); SND('reward'); G.save(); toast('領咗 ✦ ' + r.grains); closeDiary(); openDiary(); });
      row.appendChild(bt); node.appendChild(row);
    });
    const btns = [];
    if (total) { const tg = Math.min(P.events.diaryClaimMax, total * P.events.diaryGrains); btns.push({ text: '一鍵領取 ✦' + tg, primary: true, silent: true, onClick: () => { const r = EV.claim(s); SND('reward'); toast('領咗 ✦ ' + r.grains + (r.left ? '（單次上限，仲有 ' + r.left + ' 件，再領一次）' : '')); rd.burst('spark', R.CX, R.GROUND_Y - 40, 6, 60); G.save(); } }); }
    btns.push({ text: '關閉', primary: !total });
    modal({ title: '日記', kind: 'diary', node, buttons: btns });
  }
  function closeDiary() { $('#modal').style.display = 'none'; modalOpen = false; modalQ.length = 0; }
  UI.openDiary = openDiary;

  // ── 事件提示卡 ──
  UI.showEventCard = function (rec) {
    const c = $('#evcard'); if (!c) return;
    { const df = EVN().DEF[rec.id]; $('#evname').textContent = (df ? df.name : rec.id); }
    $('#evtext').textContent = rec.flavor;
    $('#evgain').textContent = (rec.grains || rec.mood) ? ('光粒 ✦ +' + rec.grains + (rec.mood ? '　心情 +' + rec.mood : '')) : '';
    c.dataset.event = rec.id; c.style.display = 'block';
  };
  UI.hideEventCard = function () { const c = $('#evcard'); if (c) { c.style.display = 'none'; c.dataset.event = ''; } };

  // ── 摘要 ──
  UI.showSummary = function (rep) {
    if (!rep || !rep.show) return;
    modal({ title: '你不在時發生咗咩', kind: 'summary', lines: rep.summary, buttons: [{ text: '收下光粒 ✦ +' + (rep.giftTotal || rep.gift), primary: true }], onClose: () => { SND('reward'); rd.burst('spark', R.CX, R.GROUND_Y - 40, 8, 70); rd.act('happy', 1.4); } });
  };

  // ── Debug 面板 ──
  function buildDebug() {
    const d = $('#dbg'); $('#dbgT').style.display = 'block'; $('#dbgT').addEventListener('click', () => { d.style.display = d.style.display === 'block' ? 'none' : 'block'; }); if (G.openDbg) d.style.display = 'block';
    const grp = (title, btns) => { const g = document.createElement('div'); g.className = 'g'; g.innerHTML = '<b>' + title + '</b><br>'; btns.forEach(([n, fn, id]) => { const b = document.createElement('button'); b.textContent = n; b.dataset.testid = id || ''; b.addEventListener('click', (e) => { e.stopPropagation(); fn(b); refreshDbg(); }); g.appendChild(b); }); d.appendChild(g); return g; };
    const s = () => G.state;
    grp('時間倍率', [['×1', () => G.timeScale = 1, 'ts-1'], ['×60', () => G.timeScale = 60, 'ts-60'], ['×600', () => G.timeScale = 600, 'ts-600'], ['×3600', () => G.timeScale = 3600, 'ts-3600']]);
    grp('快進（線上）', [['+1h', () => G.fastForward(3600), 'ff-1'], ['+6h', () => G.fastForward(6 * 3600), 'ff-6'], ['+24h', () => G.fastForward(24 * 3600), 'ff-24']]);
    grp('模擬離線', [['6h', () => G.simOffline(6), 'off-6'], ['12h', () => G.simOffline(12), 'off-12'], ['30h', () => G.simOffline(30), 'off-30']]);
    grp('需求', [['全滿', () => { for (const k of D.NEED_KEYS) s().needs[k] = 100; }, 'n-100'], ['全 50', () => { for (const k of D.NEED_KEYS) s().needs[k] = 50; }, 'n-50'], ['飽腹 10', () => { s().needs.hunger = 10; }, 'n-h10'], ['全 25', () => { for (const k of D.NEED_KEYS) s().needs[k] = 25; }, 'n-25'], ['精力 30', () => { s().needs.energy = 30; }, 'n-e30']]);
    grp('CQ / 階段', [['CQ 80', () => { s().cq = 80; }, 'cq-80'], ['CQ 55', () => { s().cq = 55; }, 'cq-55'], ['CQ 20', () => { s().cq = 20; }, 'cq-20'], ['芽崽將完成', () => { if (s().stage === 'sprout') s().growthSec = P.stageSec.sprout - 5; }, 'near-adult'], ['孵化', () => { if (s().stage === 'egg') s().growthSec = P.stageSec.egg - 1; }, 'hatch']]);
    grp('本地時刻', [['04', () => G.hourOverride = 4, 'h-4'], ['09', () => G.hourOverride = 9, 'h-9'], ['14', () => G.hourOverride = 14, 'h-14'], ['18', () => G.hourOverride = 18, 'h-18'], ['23', () => G.hourOverride = 23, 'h-23'], ['實時', () => G.hourOverride = null, 'h-real']]);
    const needSet = (o) => () => { Object.assign(s().needs, { hunger: 80, mood: 80, clean: 80, energy: 80 }, o); s().poops = 0; };
    grp('表情（設需求）', [['開心', needSet({ hunger: 100, mood: 100, clean: 100, energy: 100 }), 'dbg-ex-happy'], ['平靜', needSet({ hunger: 60, mood: 60, clean: 60, energy: 60 }), 'dbg-ex-neutral'], ['肚餓', needSet({ hunger: 20 }), 'dbg-ex-hungry'], ['疲倦', needSet({ energy: 20 }), 'dbg-ex-tired'], ['想玩', needSet({ mood: 20 }), 'dbg-ex-bored'], ['污糟', needSet({ clean: 20 }), 'dbg-ex-dirty'], ['不適', needSet({ hunger: 3 }), 'dbg-ex-unwell']]);
    grp('行為', ['blink', 'sway', 'yawn', 'walk', 'jump', 'play', 'nap', 'sunbathe', 'bump', 'grumpy', 'startle', 'cuddly', 'react'].map(n => [n, () => G.forceBeh(n), 'dbg-beh-' + n]));
    grp('生命感第二段', ['scratch', 'sneeze', 'sniff', 'sniff_sneeze', 'lookup', 'lookup_tip', 'swat_miss', 'swat_hit'].map(n => [n, () => G.forceBeh(n), 'dbg-beh-' + n]));
    grp('事件（強制）', D.EVENTS.filter(e => !e.special).map(e => [e.name, () => G.forceEvent(e.id), 'dbg-ev-' + e.id]).concat([['閃光日', () => { EVN().setFlashDay(s(), true); EVN().force(s(), 'flash'); }, 'dbg-ev-flash']]));
    grp('時段（早午晚深夜）', LT().ORDER.map(p => [D.PARAMS.light.periods[p].name, () => G.setPeriod(p), 'dbg-per-' + p]).concat([['實時', () => G.setPeriod(null), 'dbg-per-real']]));
    // 生命感第一段：表情／gaze／臉模式／點一下回頭（QA）
    const Q = () => window.__qa.pet;
    grp('臉 mode（F1）', ['auto', 'native', 'off'].map(m => [m, () => Q().faceMode(m), 'dbg-fm-' + m]));
    grp('眼款（F1）', D.PARAMS.face.eyes.map(e => [e, () => Q().setFace({ eyes: e }), 'dbg-eye-' + e]).concat([['自動', () => Q().setFace(null), 'dbg-eye-auto']]));
    grp('口款（F1）', D.PARAMS.face.mouths.map(m => [m, () => Q().setFace(Object.assign({}, G.beh.faceForce || {}, { mouth: m })), 'dbg-mouth-' + m]));
    grp('gaze（F2）', D.PARAMS.face.gazeBins.map(g => [g, () => Q().setGaze(g), 'dbg-gaze-' + g]).concat([['自動', () => Q().setGaze(null), 'dbg-gaze-auto']]));
    grp('觸摸（D2）', [['點背後', () => Q().tap(G.beh.x - G.beh.dir * 12, -20), 'dbg-tap-back'], ['點前面', () => Q().tap(G.beh.x + G.beh.dir * 8, -20), 'dbg-tap-front'], ['點頭頂', () => Q().tap(G.beh.x, -60), 'dbg-tap-up'], ['燈泡開關', () => { D.PARAMS.face.bulb.enabled = !D.PARAMS.face.bulb.enabled; }, 'dbg-bulb']]);
    const info = document.createElement('div'); info.id = 'dinfo'; d.appendChild(info);
  }
  function refreshDbg() {
    const i = $('#dinfo'); if (!i) return; const s = G.state, p = rd.perf;
    i.textContent = `stage ${s.stage}/${s.form || '-'}\nCQ ${s.cq.toFixed(0)} grow ${(s.growthSec / 3600).toFixed(2)}h\npoops ${s.poops} sleep ${s.sleeping ? 1 : 0}\nneeds ${D.NEED_KEYS.map(k => s.needs[k].toFixed(0)).join('/')}\nscale x${G.timeScale} hr ${G.hour().toFixed(1)}\nperiod ${G.light ? G.light.period : '-'} expr ${G.beh ? G.beh.expr : '-'}\nbeh ${G.beh ? G.beh.state + '/' + G.beh.clip + '#' + G.beh.frame : '-'}\nev ${G.ev ? G.ev.rec.id : '-'} atlas ${rd.atlasReady ? 1 : 0}\naud ${(() => { const a = window.Glimmer.audio.Engine.status(); return a.ctx + ' bgm ' + a.bgm + ' loops ' + a.loops.join(','); })()}\nq ${s.settings.quality} ${p.n ? (p.sum / p.n).toFixed(1) : '-'}ms\nface ${(() => { const f = window.__qa && window.__qa.pet && window.__qa.pet.face ? window.__qa.pet.face() : null; return f ? f.eyes + '/' + f.mouth + ' gaze ' + f.gaze + (f.faceVisible ? '' : ' (hidden)') + (f.live ? ' live' : ' native') : '-'; })()}\nlook ${G.beh ? G.beh.look.q + '(' + G.beh.look.src + ')' : '-'}`;
  }

  // ── 初始化 ──
  UI.init = function (g) {
    G = g; rd = G.renderer;
    fillIcon($('#btn-feed canvas'), 'feed'); fillIcon($('#btn-play canvas'), 'play'); fillIcon($('#btn-clean canvas'), 'clean'); fillIcon($('#btn-sleep canvas'), 'sleep');
    $('#btn-feed').addEventListener('click', () => showPop('feed'));
    $('#btn-play').addEventListener('click', () => showPop('play'));
    $('#btn-clean').addEventListener('click', () => act.rinse());
    $('#btn-sleep').addEventListener('click', () => act.sleep());
    $('#gear').addEventListener('click', () => { SND('tap'); openSettings(); });
    $('#diary').addEventListener('click', () => { SND('tap'); openDiary(); });
    $('#mgQuit').addEventListener('click', () => { SND('cancel'); endMG(true); });
    // 指標：視差、拖動籃子、輕點
    const hit = $('#hit');
    const toArt = (e) => rd.screenToArt(e.clientX, e.clientY);
    // P2：寵物觸控區＝真身實色框，按需要撐到 ≥44 CSS px（唔大過身體太多：每邊最多多 pad 到 44px 或 3 art px）
    const MIN_CSS = 44;
    function petHitBox() {
      const r = rd.petRect, cssPerArt = (G.layoutInfo ? G.layoutInfo.cssW : 390) / R.W, minA = MIN_CSS / cssPerArt, pv = rd.par.x * -1.5;
      if (!r || !(r.w > 0)) { const b = rd.petBox(); return { x: b.x, y: b.y, w: b.w, h: b.h, fallback: true, minArt: minA, cssPerArt }; }
      const pad = 3, w = Math.max(minA, r.w + pad * 2), h = Math.max(minA, r.h + pad * 2);
      return { x: r.x + pv + r.w / 2 - w / 2, y: r.y + r.h / 2 - h / 2, w, h, body: { x: r.x + pv, y: r.y, w: r.w, h: r.h }, minArt: minA, cssPerArt };
    }
    const inBox = (a, b) => a.x >= b.x && a.x <= b.x + b.w && a.y >= b.y && a.y <= b.y + b.h;
    let press = null, down = false;
    const SHORT_MS = (P.beh.look && P.beh.look.shortTapMs) || 300;
    hit.addEventListener('pointermove', (e) => {
      const a = toArt(e);
      if (G.mode === 'minigame' && mgs) { if (e.buttons || e.pointerType === 'touch' || true) mgs.target = a.x; return; }
      if (down && G.beh && !G.state.sleeping && G.state.stage !== 'egg') NS_BEH.drag(G.beh, a.x - R.CX, a.y - R.GROUND_Y);   // P2：拖動手指 → 眼神跟手指
      rd.parT.x = clamp((a.x / R.W - 0.5) * 2, -1, 1); rd.parT.y = clamp((a.y / R.H - 0.5) * 2, -1, 1); rd.parT.active = true; rd.parT.last = rd.t;
    });
    hit.addEventListener('pointerdown', (e) => {
      const a = toArt(e);
      if (G.mode === 'minigame') { if (mgs) mgs.target = a.x; return; }
      closePop(); down = true; press = null; try { hit.setPointerCapture(e.pointerId); } catch (er) { }   // 拖出 #hit（例：經過 HUD）都繼續收 move／up
      const s = G.state;
      // 便便
      for (let i = s.poops - 1; i >= 0; i--) { const p = rd.poopPos(i); if (Math.abs(a.x - (p.x + rd.par.x * -1.5)) < 11 && a.y > p.y - 18 && a.y < p.y + 8) { SIM.clearPoop(s); processEvents(); G.save(); return; } }
      const b = petHitBox();
      if (inBox(a, b)) {
        if (s.stage === 'egg') { SIM.tapEgg(s); processEvents(); G.save(); }
        else if (!s.sleeping) { if (G.beh) press = { id: e.pointerId, t0: performance.now(), x: a.x - R.CX, y: a.y - R.GROUND_Y }; else { rd.act('happy', 0.9); rd.burst('heart', R.CX, R.GROUND_Y - 55, 2, 30); } }   // P2：放手先判短 tap／長按
        else if (G.lightWake && G.lightWake()) { toast('團絨揉揉眼醒咗…仲有啲睏睏'); SND('sleep', { on: false }); }
      } else if (s.stage !== 'egg' && !s.sleeping && G.beh && a.y > R.GROUND_Y - 50 && a.y < R.GROUND_Y + 40) {
        NS_BEH.tap(G.beh, 'ground', clamp(a.x - R.CX, -70, 70), a.y - R.GROUND_Y);
      }
    });
    const release = (e, cancel) => {
      down = false; if (G.beh) NS_BEH.dragEnd(G.beh);
      const p = press; press = null; if (!p || cancel || G.mode === 'minigame' || !G.beh || G.state.sleeping) return;
      const ms = performance.now() - p.t0; G.lastPetPress = { ms: Math.round(ms), short: ms < SHORT_MS };
      if (ms < SHORT_MS) NS_BEH.tap(G.beh, 'pet', p.x, p.y);             // 短 tap：照舊（望向＋回頭 D2＋反應／連點）
      else NS_BEH.tap(G.beh, 'pet', p.x, p.y, { hold: true });           // 長按：只望住，唔回頭唔反應（蹭手留第三段）
    };
    hit.addEventListener('pointerup', (e) => release(e, false));
    hit.addEventListener('pointercancel', (e) => release(e, true));
    hit.addEventListener('pointerleave', () => { rd.parT.active = false; if (down) { down = false; press = null; if (G.beh) NS_BEH.dragEnd(G.beh); } });
    UI.petHitBox = petHitBox;
    window.addEventListener('deviceorientation', (e) => { if (e.gamma == null || G.mode === 'minigame') return; rd.parT.x = clamp(e.gamma / 22, -1, 1); rd.parT.y = clamp(((e.beta || 45) - 45) / 25, -1, 1); rd.parT.active = true; rd.parT.last = rd.t; });
    if (G.debug) buildDebug();
  };

  // ── 每幀 ──
  const lastVals = {};
  UI.update = function (dt) {
    const s = G.state;
    if (toastT > 0) { toastT -= dt; if (toastT <= 0) $('#toast').style.display = 'none'; }
    if (mgs) mgUpdate(dt);
    if (G.mode === 'minigame') return;
    // 事件（可能由 fastForward 產生）
    if (s.ev.length) processEvents();
    // 需求條
    for (const k of D.NEED_KEYS) {
      const el = $('[data-need="' + k + '"] .fill'); const v = Math.round(s.needs[k]); const key = k + v;
      if (lastVals[k] !== key) { lastVals[k] = key; el.style.width = (s.stage === 'egg' ? 100 : v) + '%'; el.className = 'fill ' + (s.stage === 'egg' ? '' : SIM.needBand(v) === 'ok' ? 'ok' : SIM.needBand(v) === 'warn' ? 'warn' : ''); el.parentNode.parentNode.title = D.NEED_LABEL[k] + ' ' + v; }
    }
    // 階段標籤
    const unwell = SIM.isUnwell(s);
    const sn = D.STAGE_NAME[s.stage]; const sub = s.stage === 'egg' ? '輕點光卵，叫佢發亮' : s.stage === 'sprout' ? D.SPROUT_SUB : D.FORM_NAME[s.form] + '形態';
    const chip = sn + '|' + sub + '|' + unwell + '|' + Math.round(SIM.stageProgress(s) * 100) + '|' + s.withdrawn.on;
    if (lastVals.chip !== chip) {
      lastVals.chip = chip; $('#stagename').textContent = sn;
      $('#substage').textContent = sub + (unwell ? ' · 不適' : s.withdrawn.on ? ' · 睏倦退縮' : '');
      $('#progf').style.width = Math.round(SIM.stageProgress(s) * 100) + '%'; $('#prog').style.display = s.stage === 'adult' ? 'none' : 'block';
    }
    const dn = s.evs && s.evs.diary ? s.evs.diary.length : 0; if (lastVals.dn !== dn) { lastVals.dn = dn; const bd = $('#diaryN'); bd.textContent = dn; bd.style.display = dn ? 'block' : 'none'; }
    const gr = '✦ ' + s.grains; if (lastVals.gr !== gr) { lastVals.gr = gr; $('#grains').textContent = gr; }
    // 按鈕狀態
    const sleeping = s.sleeping, egg = s.stage === 'egg';
    ['feed', 'play', 'clean'].forEach(k => $('#btn-' + k).classList.toggle('dis', sleeping || egg));
    $('#btn-sleep').classList.toggle('dis', egg);
    $('#btn-sleep span').textContent = sleeping ? '開燈' : '關燈';
    // 就寢建議 / 氣泡
    const hr = G.hour(); const night = hr >= P.autoSleepHintFrom || hr < P.autoSleepHintTo;
    const suggest = night && s.settings.autoSuggest && !sleeping && !egg && s.needs.energy < P.sleepMinEnergyToSleep;
    $('#btn-sleep').classList.toggle('hint', suggest);
    let msg = '';
    if (egg) msg = s.growthSec < 1 ? '輕點我，我就會發亮！' : '';
    else if (sleeping) msg = 'zZz…';
    else if (unwell) msg = '唔舒服…';
    else if (s.withdrawn.on) msg = '縮埋一角…食啲嘢、玩下先得';
    else if (suggest) msg = '夜深喇，關燈瞓覺啦 ☾';
    else { const lk = SIM.lowestNeed(s); if (s.needs[lk] < 30) msg = { hunger: '好肚餓…', mood: '悶悶地…', clean: '污糟糟…', energy: '好眼瞓…' }[lk]; else if (s.poops >= 2) msg = '有便便呀…'; }
    const b = $('#bubble');
    if (msg !== lastBubble) { lastBubble = msg; b.textContent = msg; b.style.display = msg ? 'block' : 'none'; }
    if (msg && rd.petDraw) { const top = (rd.petDraw.y + (s.stage === 'adult' ? 6 : 14)) * 2; b.style.top = Math.max(150, top - 40) + 'px'; }
    if (G.debug) refreshDbg();
  };

  UI.modal = modal; UI.toast = toast; UI.isModalOpen = () => modalOpen; UI.startMG = startMG; UI.mgState = () => mgs; UI.endMG = endMG; UI.processEvents = processEvents;
  return UI;
});
