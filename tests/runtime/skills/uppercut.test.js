const assert = require('node:assert/strict');
const test = require('node:test');
const { createUppercut } = require('../../../src/combat/skills/common/uppercut.js');

test('uppercut emits preparation, hit and recovery events without lifting the actor', () => {
  const events = [];
  const context = {
    emit: event => events.push(event),
    clock: { hitstop: 0 },
    status: { freeze: () => { throw new Error('hitstop must use the shared status clock'); } },
  };
  const action = createUppercut(context, { mp: 6, cooldown: 120 }, { startup: 3, active: 2, recovery: 4 });

  assert.deepEqual(action.phases.map(phase => phase.name), ['preparation', 'uppercut', 'recovery']);
  assert.equal(action.phases.some(phase => phase.move?.z || phase.move?.vz), false);
  action.update(3);
  action.update(2);
  assert.deepEqual(events.map(event => event.type), ['body', 'weapon', 'fxOnce', 'phase', 'phase', 'hitbox', 'hitstop', 'phase']);
  assert.equal(events.filter(event => event.type === 'fxOnce').length, 1);
  assert.equal(events.filter(event => event.type === 'fx').length, 0);
  assert.equal(action.cancel(), true);
});

test('uppercut spends resources at preparation and applies launch, hitstun and super armor at their phases', () => {
  const events = [];
  const context = {
    emit: event => events.push(event),
    resources: { mp: 20, cooldown: 0 },
    status: { setTimer: (name, value) => events.push({ type: 'status', name, value }) },
    clock: { hitstop: 0 },
    freeze: duration => { context.clock.hitstop = duration; },
  };
  const action = createUppercut(context, { mp: 6, cooldown: 120, launch: 13, hitstun: 18, superArmor: 8 }, { startup: 2, active: 1, recovery: 2 });

  action.update(1);
  assert.equal(context.resources.mp, 14);
  assert.equal(context.resources.cooldown, 120);
  assert.equal(events.some(event => event.type === 'status' && event.name === 'superArmor'), false);
  action.update(1);
  assert.ok(events.some(event => event.type === 'status' && event.name === 'superArmor'));
  action.update(1);
  assert.ok(events.some(event => event.type === 'hitbox' && event.launch === 13 && event.hitstun === 18));
  assert.equal(context.clock.hitstop, 3);
});
