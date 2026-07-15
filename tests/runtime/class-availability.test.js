const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const {
  classAvailability,
  canStartClass,
} = require('../../src/classes/availability.js');

const root = path.resolve(__dirname, '../..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

function functionSource(name) {
  const start = html.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `missing function ${name}`);
  const bodyStart = html.indexOf('{', start);
  let depth = 0;
  for (let i = bodyStart; i < html.length; i++) {
    if (html[i] === '{') depth++;
    if (html[i] === '}' && --depth === 0) return html.slice(start, i + 1);
  }
  assert.fail(`unterminated function ${name}`);
}

function functionBody(name) {
  const source = functionSource(name);
  return source.slice(source.indexOf('{') + 1, -1);
}

function runtimeContext(overrides = {}) {
  let playerConstructions = 0;
  const context = {
    classAvailability,
    canStartClass,
    Player: class {
      constructor(clsKey) {
        playerConstructions++;
        this.clsKey = clsKey;
      }
    },
    player: undefined,
    enemies: [],
    resetPools() {},
    dungeonId: 0,
    dungeon: 1,
    room: 1,
    score: 0,
    shake: 0,
    hitstop: 0,
    combo: {},
    door: null,
    transition: 0,
    mapIndex: 0,
    gameState: 'menu',
    classSelectMessage: '',
    Save: { data: { unlocked: 0 } },
    DUNGEONS: [{}],
    Audio2: { ensure() {}, stopBgm() {}, startBgm() {}, sfx() {} },
    Math,
    ...overrides,
  };
  context.playerConstructions = () => playerConstructions;
  return vm.createContext(context);
}

function install(context, ...names) {
  vm.runInContext(names.map(functionSource).join('\n'), context);
}

test('only finished swordman classes can start', () => {
  assert.equal(canStartClass('blade'), true);
  assert.equal(canStartClass('berserk'), true);
  assert.equal(canStartClass('spectre'), false);
  assert.equal(canStartClass('asura'), false);
  assert.equal(canStartClass('unknown'), false);
});

test('coming-soon classes expose the disabled label', () => {
  assert.equal(classAvailability('spectre').label, '暂未开放');
  assert.equal(classAvailability('asura').status, 'coming-soon');
  assert.equal(classAvailability('unknown'), undefined);
});

test('callers cannot mutate class availability policy', () => {
  const spectre = classAvailability('spectre');
  spectre.status = 'available';
  spectre.label = '已开放';

  assert.equal(canStartClass('spectre'), false);
  assert.equal(classAvailability('spectre').status, 'coming-soon');
  assert.equal(classAvailability('spectre').label, '暂未开放');
});

test('exports the same API for browser use', () => {
  assert.equal(globalThis.DOF70.classes.canStartClass, canStartClass);
});

test('loads availability after metadata and before the inline runtime', () => {
  const metadata = html.indexOf('<script src="assets/skill_actions.meta.js"></script>');
  const availability = html.indexOf('<script src="src/classes/availability.js"></script>');
  const runtime = html.indexOf('<script>\n"use strict";');
  assert.ok(metadata < availability);
  assert.ok(availability < runtime);
});

test('preserves four class cards and marks coming-soon cards disabled', () => {
  assert.match(html, /const CLASS_KEYS = \['blade','berserk','spectre','asura'\];/);
  const select = functionBody('drawSelect');
  assert.match(select, /classAvailability\(ck\)/);
  assert.match(select, /availability\.label/);
  assert.match(select, /ctx\.globalAlpha=0\.45/);
});

test('guards every Player construction before it happens', () => {
  const start = functionBody('startGame');
  const resume = functionBody('continueGame');
  assert.ok(start.indexOf('canStartClass(clsKey)') < start.indexOf('new Player'));
  assert.ok(resume.indexOf('canStartClass(r.clsKey)') < resume.indexOf('new Player'));
  assert.match(start, /gameState='select'.*classSelectMessage/s);
  assert.match(resume, /gameState='select'.*classSelectMessage/s);
});

test('startGame executes the gate before constructing Player', () => {
  for (const clsKey of ['spectre', 'unknown']) {
    const context = runtimeContext();
    install(context, 'startGame');
    assert.equal(context.startGame(clsKey), false);
    assert.equal(context.playerConstructions(), 0);
    assert.equal(context.gameState, 'select');
    assert.ok(context.classSelectMessage);
  }

  const context = runtimeContext();
  install(context, 'startGame');
  assert.equal(context.startGame('blade'), true);
  assert.equal(context.playerConstructions(), 1);
  assert.equal(context.player.clsKey, 'blade');
});

test('continueGame rejects a disabled save without constructing Player', () => {
  const context = runtimeContext({
    Save: { data: { unlocked: 0, run: { clsKey: 'spectre' } } },
    classSelectMessage: '旧提示',
  });
  install(context, 'continueGame');

  assert.equal(context.continueGame(), false);
  assert.equal(context.playerConstructions(), 0);
  assert.equal(context.gameState, 'select');
  assert.equal(context.classSelectMessage, '暂未开放');
});

test('URL debug entry stops after a disabled class fails its gate', () => {
  let dungeonStarts = 0;
  const context = runtimeContext({
    SPR: { ready: true },
    location: { search: '?shot=spectre' },
    URLSearchParams,
    beginDungeon() { dungeonStarts++; },
    updateCam() {},
  });
  install(context, 'startGame');
  const debug = html.slice(html.indexOf('(function(){const q='), html.indexOf('})();', html.indexOf('(function(){const q=')) + 5);

  assert.doesNotThrow(() => vm.runInContext(debug, context));
  assert.equal(context.playerConstructions(), 0);
  assert.equal(dungeonStarts, 0);
  assert.equal(context.player, null);
});

test('number and Enter selection execute the same startGame gate', () => {
  for (const key of ['3', 'enter']) {
    const keys = { [key]: true };
    const context = runtimeContext({
      gameState: 'select',
      CLASS_KEYS: ['blade', 'berserk', 'spectre', 'asura'],
      selIndex: 2,
      keys,
      pressed(name) {
        if (!keys[name]) return false;
        keys[name] = false;
        return true;
      },
    });
    install(context, 'startGame', 'update');

    context.update();
    assert.equal(context.playerConstructions(), 0, `${key} constructed Player`);
    assert.equal(context.gameState, 'select');
    assert.equal(context.classSelectMessage, '暂未开放');
  }
});

test('drawSelect treats missing availability as disabled instead of crashing', () => {
  const labels = [];
  const context = runtimeContext({
    CLASS_KEYS: ['missing'],
    CLASSES: { missing: { color: '#fff', name: '漏配职业', desc: '', hp: 1, mp: 1 } },
    classAvailability() { return undefined; },
    canStartClass() { return false; },
    ctx: {
      save() {}, restore() {}, fillRect() {}, strokeRect() {},
      fillText(text) { labels.push(text); },
    },
    W: 960,
    H: 540,
    selIndex: 0,
    drawBackground() {}, drawShadow() {}, drawClassPortrait() {}, wrapText() {},
  });
  install(context, 'drawSelect');

  assert.doesNotThrow(() => context.drawSelect());
  assert.ok(labels.includes('暂未开放'));
});

test('leaving class selection clears stale messages', () => {
  const keys = { escape: true };
  const context = runtimeContext({
    gameState: 'select',
    classSelectMessage: '暂未开放',
    CLASS_KEYS: ['blade', 'berserk', 'spectre', 'asura'],
    selIndex: 2,
    keys,
    pressed(name) {
      if (!keys[name]) return false;
      keys[name] = false;
      return true;
    },
  });
  install(context, 'update');

  context.update();
  assert.equal(context.gameState, 'menu');
  assert.equal(context.classSelectMessage, '');
});

test('global 0 key clears stale class messages when returning to menu', () => {
  let keydown;
  const context = runtimeContext({
    gameState: 'select',
    classSelectMessage: '暂未开放',
    menuIndex: 2,
    window: {
      addEventListener(type, handler) {
        if (type === 'keydown') keydown = handler;
      },
    },
  });
  const start = html.indexOf("window.addEventListener('keydown',e=>{", html.indexOf('/* ===================== 全局按键'));
  const end = html.indexOf('\n});', start) + 4;
  vm.runInContext(html.slice(start, end), context);

  keydown({ key: '0' });
  assert.equal(context.gameState, 'menu');
  assert.equal(context.menuIndex, 0);
  assert.equal(context.classSelectMessage, '');
});

test('keyboard, save, and URL entries route through guarded starters', () => {
  const selection = html.match(/if\(gameState==='select'\)\{(.*?)\n\s*return;\n\s*\}/s)[1];
  assert.match(selection, /pressed\(''\+i\).*startGame\(CLASS_KEYS\[selIndex\]\)/s);
  assert.match(selection, /pressed\('enter'\).*startGame\(CLASS_KEYS\[selIndex\]\)/s);
  assert.match(html, /if\(a==='continue'\) continueGame\(\);/);

  const debug = html.slice(html.indexOf('// 调试: ?shot='));
  assert.match(debug, /q\.get\('state'\)==='mapsel'.*if\(!startGame\(q\.get\('shot'\)\|\|'blade'\)\) return;/s);
  assert.match(debug, /if\(!startGame\(cls\)\) return; beginDungeon/);
});
