const assert = require('node:assert/strict');
const test = require('node:test');
const { createGrabBlastBlood } = require('../../../../src/combat/skills/berserk/grab-blast-blood.js');

function run(target, extra = {}) {
  const events = [], resources = { mp: 20, hp: 50, maxhp: 100 };
  const action = createGrabBlastBlood({ direction: 1, target, targetStatus: target?.status, resources, emit: e => events.push(e), ...extra }, { dmg: [60, 73], mp: 5 }, { startup: 1, grab: 1, blood: 1, recovery: 1 });
  for (let i = 0; i < 4; i++) action.update(1);
  return { action, events, resources };
}

test('grab blast blood binds a normal target, sprays blood and heals', () => {
  const target = { status: { timers: {}, held: null } };
  const { action, events, resources } = run(target, { status: { setTimer() {}, grab: () => true } });
  assert.equal(action.branch, 'normal');
  assert.equal(events.find(e => e.type === 'bind').target, target);
  assert.equal(events.find(e => e.type === 'blood').branch, 'normal');
  assert.ok(events.some(e => e.type === 'heal'));
  assert.ok(resources.hp > 50);
});

test('grab blast blood has ungrabbable and boss branches', () => {
  const blocked = run({ status: { timers: { ungrabbable: 1 } } });
  assert.equal(blocked.action.branch, 'ungrabbable');
  assert.equal(blocked.events.some(e => e.type === 'bind'), false);
  const boss = run({ boss: true, status: { timers: {} } }, { status: { setTimer() {}, grab: () => true } });
  assert.equal(boss.action.branch, 'boss');
  assert.equal(boss.events.find(e => e.type === 'blood').branch, 'boss');
});

test('grab blast blood cleans a successful bind when canceled', () => {
  const target = { status: { timers: {}, held: null } }, events = [];
  const action = createGrabBlastBlood({ target, targetStatus: target.status, status: { setTimer() {}, grab: () => true }, release: () => events.push('released'), emit: e => events.push(e) }, {}, { startup: 1, grab: 1, blood: 1, recovery: 5 });
  action.update(2);
  assert.equal(action.cancel(), false);
  action.update(1);
  assert.equal(action.cancel(), true);
  assert.ok(events.includes('released'));
});
