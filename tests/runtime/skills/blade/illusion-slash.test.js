const assert = require('node:assert/strict');
const test = require('node:test');
const { createIllusionSlash } = require('../../../../src/combat/skills/blade/illusion-slash.js');

test('illusion slash prepares, locks direction, performs ten slashes, then sword-wave and recovery', () => {
  const events = [];
  const action = createIllusionSlash({ direction: -1, emit: e => events.push(e) }, { weapon: 'greatsword' }, { preparation: 1, slashes: 1, swordWave: 1, recovery: 1 });
  action.update(1); action.update(1); action.update(1); action.update(1);
  assert.deepEqual(events.filter(e => e.type === 'phase').map(e => e.name), ['preparation', 'slashes', 'sword-wave', 'recovery']);
  assert.equal(events.filter(e => e.type === 'hitbox' && e.stage === 'slash').length, 10);
  assert.equal(events.filter(e => e.type === 'hitbox' && e.stage === 'sword-wave').length, 1);
  assert.ok(events.filter(e => e.type === 'turn').every(e => e.direction === -1));
});

test('illusion slash only scales allowed preparation and recovery phases', () => {
  const fast = createIllusionSlash({ emit: () => {} }, { speedMultiplier: 2 }, { preparation: 6, slashes: 20, recovery: 8 });
  assert.equal(fast.phases[0].duration, 3);
  assert.equal(fast.phases[1].duration, 20);
  assert.equal(fast.phases[3].duration, 4);
});
