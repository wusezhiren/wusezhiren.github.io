const assert = require('node:assert/strict');
const test = require('node:test');
const { createHopSmash } = require('../../../../src/combat/skills/berserk/hop-smash.js');

test('hop smash separates leap, forward movement, landing and shockwave judgment', () => {
  const events = [], status = [];
  const action = createHopSmash({ direction: 1, emit: e => events.push(e), status: { setTimer: (name, value) => status.push([name, value]) } }, {}, { leap: 1, forward: 1, downward: 1, landing: 1, shockwave: 1, recovery: 1 });
  for (let i = 0; i < 5; i++) action.update(1);
  assert.deepEqual(action.hits, ['shockwave']);
  assert.equal(events.filter(e => e.type === 'move').length, 2);
  assert.equal(events.filter(e => e.type === 'land').length, 1);
  assert.equal(events.find(e => e.type === 'hitbox').shape, 'ground-wave');
  assert.equal(events.filter(e => e.type === 'hitstop').length, 1);
  assert.deepEqual(status, [['superArmor', 12]]);
});
