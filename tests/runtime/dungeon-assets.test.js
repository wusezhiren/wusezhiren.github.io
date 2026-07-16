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
  assert.deepEqual(Object.keys(themes), ['light', 'ice', 'red', 'dark']);
  for (const theme of Object.values(themes)) {
    for (const name of ['far', 'mid', 'floor', 'tree', 'crystal', 'door', 'bossDoor']) {
      assert.ok(theme[name]?.frame, `missing ${name}`);
    }
  }
  assert.match(html, /const DUNGEON_SPR=/);
  assert.match(html, /dungeonSceneProps\(\)/);
  assert.match(html, /door\.boss\?'bossDoor':'door'/);
});

test('uses a larger unified character scale and visible stand weapon fallback', () => {
  assert.match(html, /let SPR_SCALE=0\.88/);
  assert.match(html, /wf\[2\]\*wf\[3\]>=400\?wkey/);
  assert.match(html, /anchorX=224\.5,anchorY=338/);
});
