// 測試／工具共用：由磁碟載入 data/（Node）。瀏覽器版喺 src/adventure.js 用 fetch。
const fs = require('fs'), path = require('path'); const ROOT = path.join(__dirname, '..');
const rj = p => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
function loadData() {
  const D = { tuning: rj('data/tuning.json'), flags: rj('data/flags.json'), matches: {}, cups: {}, dialogues: {} };
  for (const f of fs.readdirSync(path.join(ROOT, 'data/matches'))) { const m = rj('data/matches/' + f); D.matches[m.id] = m; }
  for (const f of fs.readdirSync(path.join(ROOT, 'data/cups'))) { const m = rj('data/cups/' + f); D.cups[m.id] = m; }
  for (const f of fs.readdirSync(path.join(ROOT, 'data/dialogue'))) { const m = rj('data/dialogue/' + f); D.dialogues[m.id] = m; }
  return D;
}
module.exports = { loadData, rj, ROOT };
