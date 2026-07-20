const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('index.html', 'utf8');

test('loads four original dungeon themes and renders their layered environments', () => {
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('assets/dungeons_original.meta.js', 'utf8'), context);
  const themes = context.window.DUNGEONS_ORIGINAL_META.themes;
  assert.deepEqual(Object.keys(themes), ['light', 'ice', 'red', 'dark', 'mushroom']);
  for (const theme of Object.values(themes)) {
    for (const name of ['far', 'mid', 'floor', 'tree', 'crystal', 'door', 'bossDoor']) {
      assert.ok(theme[name]?.frame, `missing ${name}`);
    }
  }
  assert.match(html, /const DUNGEON_SPR=/);
  assert.match(html, /dungeonSceneProps\(\)/);
  assert.match(html, /door\.boss\?'bossDoor':'door'/);
});

test('town atlas includes original NPC animation sets', () => {
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('assets/town_hendonmyre.meta.js', 'utf8'), context);
  const npcs = context.window.TOWN_HENDONMYRE_META.npcs;
  // 原版赫顿玛尔名单(Script.pvf map/hendonmyre [NPC] 布置): 西门/中央大街/拍卖场/后巷/酒馆/入口
  const roster = ['danjin', 'poongjin', 'rothon', 'kiri', 'veol', 'glam', 'grandis',
    'birken', 'albert', 'gsd', 'minet', 'shylock', 'shusia', 'seria'];
  for (const name of roster) {
    assert.ok(npcs[name]?.frames?.length > 0, `missing ${name}`);
  }
  for (const name of roster) {
    assert.ok(html.includes(`sprite:'${name}'`), `TOWN.npcs missing sprite ${name}`);
  }
  assert.match(html, /const nearbyNpc=nearestTownNpc\(\)/);
});

test('uses a larger unified character scale and visible stand weapon fallback', () => {
  assert.match(html, /let SPR_SCALE=0\.88/);
  assert.match(html, /wf\[2\]\*wf\[3\]>=400\?wkey/);
  assert.match(html, /anchorX=224\.5,anchorY=338/);
});
