const assert = require('node:assert/strict');
const fs = require('node:fs');
const test = require('node:test');

const {
  classAvailability,
  canStartClass,
} = require('../../src/classes/availability.js');

const html = fs.readFileSync('index.html', 'utf8');

function functionBody(name) {
  const match = html.match(new RegExp(`function ${name}\\([^)]*\\)\\{(.*?)\\n\\}`, 's'));
  assert.ok(match, `missing function ${name}`);
  return match[1];
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

test('keyboard, save, and URL entries route through guarded starters', () => {
  const selection = html.match(/if\(gameState==='select'\)\{(.*?)\n\s*return;\n\s*\}/s)[1];
  assert.match(selection, /pressed\(''\+i\).*startGame\(CLASS_KEYS\[selIndex\]\)/s);
  assert.match(selection, /pressed\('enter'\).*startGame\(CLASS_KEYS\[selIndex\]\)/s);
  assert.match(html, /if\(a==='continue'\) continueGame\(\);/);

  const debug = html.slice(html.indexOf('// 调试: ?shot='));
  assert.match(debug, /q\.get\('state'\)==='mapsel'.*if\(!startGame\(q\.get\('shot'\)\|\|'blade'\)\) return;/s);
  assert.match(debug, /if\(!startGame\(cls\)\) return; beginDungeon/);
});
