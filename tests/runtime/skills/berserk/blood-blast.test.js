const assert = require('node:assert/strict');
const test = require('node:test');
const { createBloodBlast } = require('../../../../src/combat/skills/berserk/blood-blast.js');

test('blood blast has four independent sprays and a distinct final burst', () => {
  const events = [], clock = { hitstop: 0 };
  const action = createBloodBlast({ direction: -1, clock, emit: e => events.push(e) }, { hits: 4 }, { startup: 1, spray: 1, final: 1, recovery: 1 });
  for (let i = 0; i < 6; i++) action.update(1);
  assert.deepEqual(action.hits, [1, 2, 3, 4, 'final']);
  assert.equal(events.filter(e => e.type === 'hitbox' && e.stage === 'spray').length, 4);
  assert.equal(events.filter(e => e.type === 'hitbox' && e.stage === 'final').length, 1);
  assert.notDeepEqual(events.find(e => e.stage === 'spray').shape, events.find(e => e.stage === 'final').shape);
  assert.equal(events.filter(e => e.type === 'hitstop').length, 4);
});
