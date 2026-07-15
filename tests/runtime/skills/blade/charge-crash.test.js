const assert = require('node:assert/strict');
const test = require('node:test');
const { createChargeCrash } = require('../../../../src/combat/skills/blade/charge-crash.js');

test('charge crash separates collision and launching uppercut', () => {
  const events = [], status = [], clock = { hitstop: 0 };
  const action = createChargeCrash({ direction: 1, clock, emit: e => events.push(e), status: { setTimer: (name, value) => status.push([name, value]) } }, { weapon: 'greatsword' }, { charge: 1, impact: 1, uppercut: 1, recovery: 1 });
  action.update(1); action.update(1); action.update(1);
  assert.deepEqual(events.filter(e => e.type === 'hitbox').map(e => e.stage), ['impact', 'uppercut']);
  assert.equal(events.find(e => e.stage === 'uppercut').launch, 14);
  assert.deepEqual(status, [['superArmor', 8]]);
  assert.equal(clock.hitstop, 3);
});

test('charge crash mirrors its movement and hit direction', () => {
  const events = [];
  const action = createChargeCrash({ direction: -1, emit: e => events.push(e) }, { weapon: 'shortsword' }, { charge: 1 });
  action.update(1);
  assert.equal(events.find(e => e.type === 'move').direction, -1);
  action.update(2);
  assert.equal(events.find(e => e.stage === 'impact').direction, -1);
});
