const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const vm = require('node:vm');

function pageContext() {
  const html = fs.readFileSync('index.html', 'utf8');
  const scripts = [...html.matchAll(/<script(?: src="([^"]+)")?>([\s\S]*?)<\/script>/g)];
  const gradient = () => ({ addColorStop() {} });
  const context2d = new Proxy({}, { get: (_target, name) => name === 'createLinearGradient' || name === 'createRadialGradient' ? gradient : () => {} });
  const canvas = { width: 960, height: 540, getContext: () => context2d, addEventListener() {}, getBoundingClientRect: () => ({ left: 0, top: 0, width: 960, height: 540 }) };
  const context = { console, Math, Date, URLSearchParams, performance: { now: () => 0 }, setTimeout, clearTimeout, setInterval() {}, clearInterval() {}, localStorage: { getItem: () => null, setItem() {} }, location: { search: '' }, document: { getElementById: () => canvas, querySelector: () => null }, Image: function () {}, AudioContext: function () {}, requestAnimationFrame() {}, addEventListener() {} };
  context.window = context;
  vm.createContext(context);
  for (const [, src, inline] of scripts) vm.runInContext(src ? fs.readFileSync(src, 'utf8') : inline, context);
  return context;
}

test('new character starts in town and the dungeon gate opens map selection', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    Audio2.sfx = () => {};
    AUTH.token = 'test-token';
    startGame('blade');
    const startState = gameState;
    player.x = TOWN.gate.x;
    player.y = TOWN.gate.y;
    keys['enter'] = true;
    update();
    return { startState, gateState: gameState, enemies: enemies.length };
  })()`, page);
  assert.equal(result.startState, 'town');
  assert.equal(result.gateState, 'mapsel');
  assert.equal(result.enemies, 0);
});

test('anonymous players cannot create a character', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    AUTH.els = {
      modal: { classList: { add() {} } }, state: { textContent: '', classList: { toggle() {} } },
      open: { hidden: false }, logout: { hidden: true }, message: { textContent: '' },
    };
    AUTH.token = null;
    const started = startGame('blade');
    return { started, state: gameState, player: Boolean(player) };
  })()`, page);
  assert.equal(result.started, false);
  assert.equal(result.state, 'menu');
  assert.equal(result.player, false);
});

test('town NPC opens the shop and leaving it returns to town', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    Audio2.sfx = () => {};
    AUTH.token = 'test-token';
    startGame('blade');
    player.x = TOWN.npc.x;
    player.y = TOWN.npc.y;
    keys['enter'] = true;
    update();
    const shopState = gameState;
    keys['escape'] = true;
    update();
    return { shopState, returnState: gameState };
  })()`, page);
  assert.equal(result.shopState, 'shop');
  assert.equal(result.returnState, 'town');
});

test('town location and position survive run serialization', () => {
  const page = pageContext();
  const run = vm.runInContext(`(() => {
    AUTH.token = 'test-token';
    startGame('blade');
    player.x = 812;
    player.y = 466;
    serializeRun();
    return Save.data.run;
  })()`, page);
  assert.equal(run.location, 'town');
  assert.deepEqual(JSON.parse(JSON.stringify(run.townPosition)), { x: 812, y: 466 });
});

test('multiplayer stays optional and does not connect without a configured endpoint', () => {
  const page = pageContext();
  const result = vm.runInContext(`(() => {
    AUTH.token = 'test-token';
    startGame('blade');
    return { endpoint: MULTIPLAYER.endpoint(), socket: MULTIPLAYER.socket, state: gameState };
  })()`, page);
  assert.equal(result.endpoint, '');
  assert.equal(result.socket, null);
  assert.equal(result.state, 'town');
});
