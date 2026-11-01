/* 《微光小圃》 devmode.js — 4a.3「開發者模式」試玩畫面（獨立彈窗，唔喺設定）。原創代碼。
   主畫面左上（HUD 下面）細細「🛠 開發者」掣 → 彈窗；按功能分組（每批自己 register 一組：4a、之後 4b、5a–5c…）。
   掣可以喺彈窗入面收埋（localStorage glimmer.devBtn=0）；收埋之後喺設定撳「版本」5 下再出返。?devbtn=1／0 強制。
   API：Glimmer.devmode.register({ id, title, order, items:[{ k, label, run() → { ok, msg } }] })；未載入前可 push 落 Glimmer.devSections。
   QA：window.__qa.devmode。 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory(root);
  else { root.Glimmer = root.Glimmer || {}; root.Glimmer.devmode = factory(root); }
})(typeof self !== 'undefined' ? self : this, function (root) {
  'use strict';
  const NS = root.Glimmer || {}, KEY = 'glimmer.devBtn';
  const secs = [];
  const version = () => (NS.data && NS.data.PARAMS && NS.data.PARAMS.series2 && NS.data.PARAMS.series2.version) || '';
  function register(sec) { const i = secs.findIndex(s => s.id === sec.id); if (i >= 0) secs.splice(i, 1); secs.push(sec); secs.sort((a, b) => (a.order || 0) - (b.order || 0)); return api; }
  (NS.devSections || []).forEach(register); NS.devSections = { push: register };
  const qs = (k) => { try { return new URLSearchParams(location.search).get(k); } catch (e) { return null; } };
  function shown() { const q = qs('devbtn'); if (q === '1') return true; if (q === '0') return false; try { return localStorage.getItem(KEY) !== '0'; } catch (e) { return true; } }
  function setShown(v) { try { localStorage.setItem(KEY, v ? '1' : '0'); } catch (e) { } sync(); return shown(); }
  let btn = null;
  function sync() { if (btn) btn.style.display = shown() ? '' : 'none'; }
  function mount() {
    if (btn || typeof document === 'undefined') return; const ui = document.getElementById('ui'); if (!ui) return;
    btn = document.createElement('div'); btn.id = 'devBtn'; btn.dataset.testid = 'dev-btn'; btn.textContent = '🛠 開發者';
    btn.style.cssText = 'position:absolute;left:8px;top:112px;z-index:6;padding:3px 8px;border-radius:10px;font:700 11px/16px sans-serif;color:#fff3d6;background:rgba(20,26,54,.62);border:1px solid rgba(255,214,110,.6);cursor:pointer;user-select:none;-webkit-user-select:none';
    btn.addEventListener('click', (e) => { e.stopPropagation(); open(); }); btn.addEventListener('pointerdown', (e) => e.stopPropagation());
    ui.appendChild(btn); sync();
    const css = document.createElement('style'); css.textContent = 'body.s2-scene #devBtn{visibility:hidden!important}'; document.head.appendChild(css);
  }
  const UI = () => NS.ui;
  function closeMe() { const m = document.getElementById('mbox'); if (m && m.dataset.kind === 'devmode') { const b = m.querySelector('[data-testid=dev-close]') || m.querySelector('[data-testid=modal-btn-0]'); if (b) b.click(); } }
  function open() {
    const U = UI(); if (!U || !U.modal) return false; if (U.isModalOpen && U.isModalOpen()) return false;
    const node = document.createElement('div'); node.dataset.testid = 'dev-panel'; node.style.cssText = 'text-align:left';
    node.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><span style="font-size:11px;opacity:.8">試玩用：唔會改團絨成長、星屑、路線同懸浮寵物</span><span data-testid="dev-version" style="font-size:11px;white-space:nowrap">版本 ' + version() + '</span></div>';
    for (const s of secs) {
      const box = document.createElement('div'); box.dataset.testid = 'dev-sec-' + s.id; box.style.cssText = 'margin:6px 0;padding:7px;border-radius:10px;background:rgba(255,214,110,.14);border:1px solid rgba(255,214,110,.5)';
      const h = document.createElement('div'); h.style.cssText = 'display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px'; h.innerHTML = '<b>' + s.title + '</b>'; if (s.status) { const st = document.createElement('span'); st.dataset.testid = 'dev-status-' + s.id; st.style.cssText = 'font-size:11px;opacity:.8'; try { st.textContent = s.status(); } catch (e) { } h.appendChild(st); } box.appendChild(h);
      const g = document.createElement('div'); g.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:5px';
      for (const it of s.items) { const b = document.createElement('div'); b.className = 'btn'; b.dataset.testid = 'dev-' + s.id + '-' + it.k; b.textContent = it.label; b.style.cssText = 'margin:0;padding:7px 4px;font-size:12.5px';
        b.addEventListener('click', () => { closeMe(); setTimeout(() => { let r; try { r = it.run() || { ok: true, msg: it.label }; } catch (e) { r = { ok: false, msg: String(e && e.message || e) }; } api.calls.push({ sec: s.id, k: it.k, ok: !!r.ok }); if (U.toast) U.toast(r.msg, 2400); }, 60); });
        g.appendChild(b); }
      box.appendChild(g); node.appendChild(box);
    }
    const tg = document.createElement('div'); tg.className = 'row'; tg.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-top:6px;font-size:12px';
    tg.innerHTML = '<span>主畫面顯示「🛠 開發者」掣</span>'; const tb = document.createElement('div'); tb.className = 'btn'; tb.dataset.testid = 'dev-toggle-btn'; tb.textContent = shown() ? '收埋' : '顯示'; tb.style.cssText = 'margin:0;padding:5px 10px;font-size:12px';
    tb.addEventListener('click', () => { setShown(!shown()); tb.textContent = shown() ? '收埋' : '顯示'; if (U.toast) U.toast(shown() ? '「🛠 開發者」掣會顯示' : '已收埋（設定撳「版本」5 下再出返）', 2600); }); tg.appendChild(tb); node.appendChild(tg);
    U.modal({ title: '🛠 開發者模式', kind: 'devmode', node, buttons: [{ text: '關閉', primary: true }] }); return true;
  }
  let taps = [];
  function versionTap(t) { t = t || Date.now(); taps = taps.filter(x => t - x < 2000); taps.push(t); if (taps.length >= 5) { taps = []; setShown(true); if (UI() && UI().toast) UI().toast('「🛠 開發者」掣出返喇', 2200); return true; } return false; }
  const api = { register, open, mount, setShown, shown, versionTap, version, sections: () => secs.map(s => ({ id: s.id, title: s.title, items: s.items.map(i => i.k) })), calls: [] };
  if (typeof document !== 'undefined') { const go = () => mount(); if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else setTimeout(go, 0); root.__qa = root.__qa || {}; root.__qa.devmode = api; }
  return api;
});
