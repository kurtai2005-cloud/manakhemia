// 由 src/town-map.js 生成 art/town/*.json（Tiled JSON 子集）：node tools/gen-town-json.js
const fs = require('fs'), path = require('path');
const TM = require('../src/town-map.js');
const out = path.join(__dirname, '../art/town/');
const maps = TM.buildMaps('night');
Object.keys(maps).forEach(k => { fs.writeFileSync(out + k + '.json', JSON.stringify(maps[k])); console.log(k, fs.statSync(out + k + '.json').size, 'bytes'); });
