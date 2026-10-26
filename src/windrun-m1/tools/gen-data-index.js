// 產生 data/index.json（瀏覽器唔能列目錄；adventure.js 用佢載入 data/）。node tools/gen-data-index.js
const fs = require('fs'), path = require('path'); const R = path.join(__dirname, '..', 'data');
const ls = d => fs.readdirSync(path.join(R, d)).filter(f => f.endsWith('.json')).sort();
fs.writeFileSync(path.join(R, 'index.json'), JSON.stringify({ _doc: '由 tools/gen-data-index.js 產生', matches: ls('matches'), cups: ls('cups'), dialogue: ls('dialogue') }, null, 1) + '\n'); console.log('data/index.json 已寫');
