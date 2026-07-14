const assert = require('node:assert/strict');
const test = require('node:test');
const { createGoreCross } = require('../../../../src/combat/skills/berserk/gore-cross.js');

test('gore cross emits horizontal, vertical and blood-cross hit stages independently', () => {
  const events = [], clock = { hitstop: 0 };
  const action = createGoreCross({ direction: -1, clock, emit: e => events.push(e) }, {}, { horizontal: 1, vertical: 1, bloodCross: 1, recovery: 1 });
  action.update(1); action.update(1); action.update(1);
  assert.deepEqual(action.hits, ['horizontal', 'vertical', 'bloodCross']);
  assert.deepEqual(events.filter(e => e.type === 'hitbox').map(e => e.shape), ['horizontal', 'vertical', 'cross']);
  assert.deepEqual(events.filter(e => e.type === 'hitbox').map(e => e.direction), [-1, -1, -1]);
  assert.equal(events.filter(e => e.type === 'hitstop').length, 3);
  assert.equal(events.find(e => e.stage === 'bloodCross').launch, 5);
});
