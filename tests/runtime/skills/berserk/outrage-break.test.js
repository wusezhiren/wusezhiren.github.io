const assert = require('node:assert/strict');
const test = require('node:test');
const { createOutrageBreak } = require('../../../../src/combat/skills/berserk/outrage-break.js');

test('outrage break spends hp on leap, slams and emits every lava eruption', () => {
  const events = [], resources = { hp: 100, mp: 10, maxhp: 100 };
  const action = createOutrageBreak({ direction: -1, resources, emit: e => events.push(e) }, { hpCost: 64, eruptions: 3 }, { leap: 1, descent: 1, impact: 1, eruption: 1, recovery: 1 });
  assert.equal(resources.hp, 36);
  for (let i = 0; i < 9; i++) action.update(1);
  assert.deepEqual(action.hits, ['impact', 1, 2, 3]);
  assert.equal(events.filter(e => e.type === 'lava').length, 3);
  assert.ok(events.some(e => e.type === 'hitstop'));
  assert.ok(events.some(e => e.type === 'land' && e.recover));
});

test('outrage break refuses to spend the last available health', () => {
  const events = [], resources = { hp: 64, mp: 10 };
  const action = createOutrageBreak({ resources, emit: e => events.push(e) }, { hpCost: 64 });
  assert.equal(action.failed, true);
  assert.equal(resources.hp, 64);
  assert.equal(events[0].kind, 'insufficient-hp');
});

test('outrage break restores landing protection after interruption', () => {
  const events = [], timers = {};
  const action = createOutrageBreak({ resources: { hp: 100 }, status: { setTimer: (n, v) => { timers[n] = v; } }, emit: e => events.push(e) }, {}, { leap: 1, descent: 1, impact: 1, eruption: 1, recovery: 3 });
  action.update(9);
  assert.equal(action.cancel(), true);
  assert.ok(events.some(e => e.type === 'land'));
});
