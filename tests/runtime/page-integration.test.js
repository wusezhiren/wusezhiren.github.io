const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');

function pageContext() {
  const html = fs.readFileSync('index.html', 'utf8');
  const scripts = [...html.matchAll(/<script(?: src="([^"]+)")?>([\s\S]*?)<\/script>/g)];
  const canvas = { width: 960, height: 540, getContext: () => new Proxy({}, { get: (_target, name) => name.startsWith('create') ? () => ({ addColorStop() {} }) : () => {} }), addEventListener() {} };
  const context = { console, Math, Date, URLSearchParams, performance: { now: () => 0 }, setTimeout, clearTimeout, localStorage: { getItem: () => null, setItem() {} }, location: { search: '' }, document: { getElementById: () => canvas, querySelector: () => null }, Image: function () {}, AudioContext: function () {}, requestAnimationFrame() {}, addEventListener() {} };
  context.window = context;
  vm.createContext(context);
  for (const [, src, inline] of scripts) vm.runInContext(src ? fs.readFileSync(src, 'utf8') : inline, context);
  return context;
}

test('real page skill adapter supplies target context and consumes dedicated FX', () => {
  const page = pageContext();
  const source = vm.runInContext('Player.prototype.bladeSkillContext.toString()+Player.prototype.handleBladeEvent.toString()+Player.prototype.handleBerserkEvent.toString()', page);
  assert.match(source, /targetStatus/);
  assert.match(source, /release|clearSuction/);
  assert.match(source, /event\.damage/);
  assert.match(source, /spawnSkillFX/);
  assert.doesNotThrow(() => vm.runInContext("(() => { const p = new Player('blade'); p.attackType = { fx: 'tripleslash' }; p.handleBladeEvent({ type: 'phase', skill: 'triple-slash' }); p.handleBerserkEvent({ type: 'phase', skill: 'gore-cross' }); })()", page));
});
