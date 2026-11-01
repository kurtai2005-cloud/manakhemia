/* 《微光小圃》 uisfx.js — HD-2D UI 音效排程（純邏輯，Node 可測）。原創代碼。
   規格：遊音 audio/README.md §7.11（hook → 檔）＋ 遊美 kit_hd2d/MOTION_HD2D.md（時間；每個檔 0 ms ＝ hook 觸發點）。
   plan(st, hook, info, nowMs) → [{ file, t(ms，相對 hook), gain, rate, hook }]；Engine.uiPlay 用 WebAudio start(ctx.currentTime + t/1000) 準時播。
   規則：
   - 轉場 transition：veil_close t=0、veil_open t=420；返回 back：只播 veil_open t=0（rate 1，冇 1.12）。
   - toast：toast_in t=0；貨幣 toast 加 coin t=140。
   - 主掣確認 primary：confirm＋btn_sparkle 同時 t=0。
   - §7 委託完成 stamp：sparkle t=0（可關）、confirm t=20（stamp 關鍵幀 100 ms − confirm 重音 80 ms）。
   - badge（紅點 wiggle）：冷卻 ≥5 s、同一個畫面只響一次；出現冇聲。
   - 卡 pop cards：popup_open 0.5 音量、rate 隨機 0.95–1.08，只播頭 3 張（t0＋40·i）；pointerup 冇聲。
   - tab／squish（btn_press）／sparkle（primary／stamp）之後唔再疊 sfx_tap（legacy 'tap' 喺窗口內食咗）。
   - legacy hook：tap → ui8_tap_a／_b 交替；coin → ui8_coin。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.uisfx = factory(); }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const F = (n) => 'sfx_ui8_' + n;
  const DEF = {
    veilOpenAt: 420,            // MOTION §6：新頁出現
    coinAt: 140,                // MOTION §4：數字 140 起
    stampConfirmAt: 20,         // stamp_done 100 ms 落章 − confirm 檔內 80 ms 重音
    stampSparkle: true,         // 父 brief：sparkle t=0（README 只列 confirm → 可關）
    badgeCdMs: 5000,
    card: { max: 3, t0: 520, step: 40, gain: 0.5, rate: [0.95, 1.08] },
    tapSuppressMs: 350,         // tab／press／sparkle 之後呢個窗口內嘅 legacy tap 唔播
    popupAfterOwnMs: 400,       // tab／轉場啱啱播完，同一下 open 唔再疊 popup_open
    dedupeMs: 120,              // 同一個 hook 120 ms 內重複（例如 pointerdown＋legacy 通知）只播一次
    dedupe: { disabled: 600, cards: 0, screen: 0, badge: 0, appear: 0, cardUp: 0 },   // disabled：pointerdown 已報 error，click 後 legacy error 唔再疊
    stampToastMs: 600,          // 委託完成 stamp 之後嘅貨幣 toast：唔再疊 toast_in，只留 coin t=140
  };
  function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function create(seed, cfg) {
    const c = Object.assign({}, DEF, cfg || {}); c.card = Object.assign({}, DEF.card, (cfg && cfg.card) || {});
    return { cfg: c, rnd: mulberry(seed == null ? 7 : seed), tab: 0, tap: 0, lastOwn: -1e9, lastNav: -1e9, badgeAt: -1e9, screen: 'home', badgeScreens: {}, last: {}, stampAt: -1e9, log: [] };
  }
  const it = (file, t, o) => Object.assign({ file: F(file), t: t || 0, gain: 1, rate: 1 }, o || {});
  function cards(st, n, t0) {
    const C = st.cfg.card, out = [];
    for (let i = 0; i < Math.min(C.max, n | 0); i++) out.push(it('popup_open', t0 + C.step * i, { gain: C.gain, rate: +(C.rate[0] + st.rnd() * (C.rate[1] - C.rate[0])).toFixed(3) }));
    return out;
  }
  function plan(st, hook, info, now) {
    info = info || {}; now = now == null ? 0 : now; const C = st.cfg; let out = [];
    const win = C.dedupe && C.dedupe[hook] != null ? C.dedupe[hook] : C.dedupeMs;
    if (win > 0 && !info.force && st.last[hook] != null && now - st.last[hook] < win) { st.log.push({ hook, now, n: 0, dup: true }); if (st.log.length > 200) st.log.shift(); return []; }
    st.last[hook] = now;
    const own = () => { st.lastOwn = now; };
    switch (hook) {
      case 'tab': out = [it(st.tab++ % 2 ? 'tab_switch_b' : 'tab_switch_a')]; own(); st.lastNav = now; break;           // tab 返回都用佢（冇 tab_pop 檔）
      case 'transition': out = [it('transition_veil_close', 0), it('transition_veil_open', C.veilOpenAt)]; if (info.cards) out = out.concat(cards(st, info.cards, C.card.t0)); own(); st.lastNav = now; enter(st, info.screen || 'page'); break;
      case 'back': out = [it('transition_veil_open', 0)]; own(); st.lastNav = now; enter(st, info.screen || 'home'); break;   // 返回 600 ms：冇卡 pop
      case 'cards': out = cards(st, info.n, info.t0 == null ? 0 : info.t0); break;
      case 'press': out = [it(st.rnd() < 0.5 ? 'btn_press_a' : 'btn_press_b')]; own(); break;                              // 一般掣 pointerdown（squish）
      case 'medal': out = [it(info.seg ? 'tap_a' : (st.tap++ % 2 ? 'tap_b' : 'tap_a'))]; own(); break;                    // 圓章／seg
      case 'tap': if (now - st.lastOwn < C.tapSuppressMs) { out = []; break; } out = [it(st.tap++ % 2 ? 'tap_b' : 'tap_a')]; break;   // legacy sfx_tap
      case 'coin': out = [it('coin')]; break;                                                                                // legacy sfx_coin
      case 'primary': out = [it('confirm', 0), it('btn_sparkle', 0)]; own(); break;
      case 'confirm': out = [it('confirm', 0)]; break;
      case 'stamp': out = (C.stampSparkle ? [it('btn_sparkle', 0)] : []).concat([it('confirm', C.stampConfirmAt)]); own(); st.stampAt = now; break;
      case 'cancel': out = [it('cancel')]; break;
      case 'disabled': out = [it('error')]; break;
      case 'popupOpen': out = now - st.lastNav < C.popupAfterOwnMs ? [] : [it('popup_open')]; break;
      case 'popupClose': out = [it('popup_close')]; break;
      case 'toast': out = (now - st.stampAt < C.stampToastMs ? [] : [it('toast_in', 0)]).concat(info.currency ? [it('coin', C.coinAt)] : []); break;   // stamp 啱啱落：只留 coin
      case 'badge': {
        const sc = info.screen || st.screen;
        if (st.badgeScreens[sc] || now - st.badgeAt < C.badgeCdMs) { out = []; break; }
        st.badgeScreens[sc] = true; st.badgeAt = now; out = [it('badge_wiggle')]; break;
      }
      case 'toggle': out = [it(info.on ? 'toggle_on' : 'toggle_off')]; break;
      case 'screen': enter(st, info.screen || 'home'); break;
      case 'cardUp': case 'appear': default: out = []; break;                                                              // pointerup／紅點出現：冇聲
    }
    out.forEach(x => { x.hook = hook; });
    st.log.push({ hook, now, n: out.length }); if (st.log.length > 200) st.log.shift();
    return out;
  }
  function enter(st, sc) { if (sc !== st.screen) { st.screen = sc; st.badgeScreens = {}; } }   // 換畫面：紅點聲「一個畫面一次」重新計
  const LEGACY = { tap: 'tap', confirm: 'primary', cancel: 'cancel', error: 'disabled', coin: 'coin' };
  return { create, plan, DEF, LEGACY, FILES: ['tap_a', 'tap_b', 'tab_switch_a', 'tab_switch_b', 'btn_press_a', 'btn_press_b', 'btn_sparkle', 'confirm', 'cancel', 'error', 'popup_open', 'popup_close', 'toast_in', 'coin', 'badge_wiggle', 'toggle_on', 'toggle_off', 'transition_veil_close', 'transition_veil_open'].map(F) };
});
