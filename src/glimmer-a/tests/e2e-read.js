/* 5a.1 e2e：UI v2 字清晰度（Kurt：「新ui有問題，d字完全睇唔清楚」）
   ① 7 個畫面（設定／圖鑑／手帳／開發者／細佬卡／屋仔／主畫面）@360×780 DPR3：每段可見字 ≥14 CSS px 實際、唔用 FP8／FP10、FP12 只用 12 嘅整數倍、對比 ≥4.5:1
   ② 開發者「清晰字型（系統字）」開咗都要過 ①
   ③ 子集冇嘅字 → 成句轉系統字（data-fbk）；開關記得（localStorage）
   node tests/e2e-read.js（要 localhost:8240） */
const path = require('path'), fs = require('fs'), os = require('os'), cp = require('child_process'); let chromium;
for (const p of [process.env.PW, 'playwright-core', '/workspace/qa-live-s1/node_modules/playwright-core']) { try { if (p) { chromium = require(p).chromium; break; } } catch (e) { } }
const BASE = process.env.BASE || 'http://localhost:8240/index.html';
let pass = 0, fail = 0; const ok = (c, m) => { if (c) { pass++; console.log('  ✓ ' + m); } else { fail++; console.log('  ✗ ' + m); } };
(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'e2eread-'));
  for (const [tag, env] of [['px', {}], ['sys', { SYSF: '1' }]]) {
    console.log('# ' + (tag === 'px' ? '像素字 FP12' : '清晰字型（系統字）'));
    cp.execFileSync('node', [path.join(__dirname, 'readshots.js'), tag], { env: Object.assign({}, process.env, env, { SHOTS: dir + '/' }), stdio: 'pipe', timeout: 240000 });
    const A = JSON.parse(fs.readFileSync(dir + '/' + tag + '-audit.json', 'utf8'));
    for (const k of ['settings', 'dex', 'journal', 'dev', 'kidcard', 'house', 'garden']) {
      const a = A[k]; ok(a && a.n > 0, k + '：有字（' + (a && a.n) + ' 段）');
      ok(a && a.bad === 0, k + '：唔合格 0 段' + (a && a.bad ? ' ← ' + JSON.stringify(a.worst.slice(0, 3)) : ''));
      ok(a && a.minEff >= 14, k + '：最細實際字號 ' + (a && a.minEff) + ' ≥ 14');
      ok(a && a.minCr >= 4.5, k + '：最低對比 ' + (a && a.minCr) + ' ≥ 4.5');
      ok(a && !a.fams.some(f => /GlimmerFP(8|10)@/.test(f)), k + '：冇 FP8／FP10');
      if (tag === 'px') ok(a && a.fams.every(f => !/^GlimmerFP12@/.test(f) || +f.split('@')[1] % 12 === 0), k + '：FP12 只用 12 嘅整數倍 ' + (a && a.fams.join(',')));
      if (tag === 'sys') ok(a && !a.fams.some(f => /^GlimmerFP/.test(f)), k + '：系統字模式冇像素字');
    }
  }
  console.log('# 缺字後備＋開關');
  const browser = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 360, height: 780 }, deviceScaleFactor: 3 }); const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(BASE + '?q=low&ev=0'); await page.evaluate(() => localStorage.clear()); await page.goto(BASE + '?q=low&ev=0');
  await page.waitForFunction(() => window.__qa && __qa.uiv2 && __qa.uiv2.st().ready && __qa.uiv2.st().on, null, { timeout: 15000 });
  await page.waitForTimeout(400);
  const r0 = await page.evaluate(() => __qa.uiv2.read()); ok(r0.cov > 1500, 'FP12 子集 cmap 讀到 ' + r0.cov + ' 字');
  const fb = await page.evaluate(async () => { const a = document.createElement('div'), b = document.createElement('div'); a.textContent = '團絨𠝹字'; b.textContent = '團絨食飯'; a.style.cssText = b.style.cssText = 'position:absolute;left:0;top:300px;font-size:10px'; document.getElementById('ui').append(a, b); await new Promise(r => setTimeout(r, 120));
    const o = { a: a.dataset.fbk || '', b: b.dataset.fbk || '', fa: getComputedStyle(a).fontFamily, fb: getComputedStyle(b).fontFamily, sa: getComputedStyle(a).fontSize }; a.remove(); b.remove(); return o; });
  ok(fb.a === '1' && !/^"?GlimmerFP/.test(fb.fa), '缺字（𠝹）→ 成句系統字：' + fb.fa.slice(0, 30));
  ok(fb.b === '' && /GlimmerFP12/.test(fb.fb), '全部有字 → 照用 FP12');
  ok(fb.sa === '24px', '後加 10px 細字 → floor 到 24px（' + fb.sa + '）');
  await page.evaluate(() => __qa.devmode.setShown(true)); await page.locator('[data-testid=dev-btn]').click(); await page.waitForTimeout(400);
  ok(await page.locator('[data-testid=dev-uiv2-sysf]').count() === 1, '開發者「UI v2」有「清晰字型（系統字）」掣');
  ok(/清晰字型（系統字）/.test(await page.locator('[data-testid=dev-uiv2-sysf]').textContent()), '掣字：清晰字型（系統字）');
  await page.locator('[data-testid=dev-uiv2-sysf]').click(); await page.waitForTimeout(300);
  const s1 = await page.evaluate(() => ({ on: __qa.uiv2.read().sysf, cls: document.getElementById('ui').classList.contains('sysf'), ls: localStorage.getItem('glimmer.sysf'), fam: getComputedStyle(document.getElementById('stagename')).fontFamily }));
  ok(s1.on && s1.cls && s1.ls === '1' && !/^"?GlimmerFP/.test(s1.fam), '撳完：系統字開（' + s1.fam.slice(0, 24) + '）＋記低');
  await page.reload(); await page.waitForFunction(() => window.__qa && __qa.uiv2 && __qa.uiv2.st().ready, null, { timeout: 15000 }); await page.waitForTimeout(300);
  ok(await page.evaluate(() => document.getElementById('ui').classList.contains('sysf')), '重開仍然系統字');
  await page.evaluate(() => __qa.uiv2.sysFont(false)); await page.waitForTimeout(200);
  ok(await page.evaluate(() => /GlimmerFP12/.test(getComputedStyle(document.getElementById('stagename')).fontFamily) && localStorage.getItem('glimmer.sysf') === '0'), '關返 → FP12');
  ok(errs.length === 0, '冇 JS error ' + errs.slice(0, 2).join(' | '));
  await browser.close();
  console.log(`\n${pass}/${pass + fail} pass`); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
