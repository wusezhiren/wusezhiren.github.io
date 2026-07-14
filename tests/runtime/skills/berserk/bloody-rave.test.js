const assert = require('node:assert/strict');
const test = require('node:test');
const { createBloodyRave } = require('../../../../src/combat/skills/berserk/bloody-rave.js');

test('bloody rave continuously suctions, opens release window and performs final slash', () => {
  const events = [], status = { suction: () => {} };
  const action = createBloodyRave({ target: { status: { timers: {} } }, targetStatus: { timers: {} }, status, emit: e => events.push(e) }, { hits: 3 }, { startup: 1, suction: 2, release: 1, final: 1, recovery: 1 });
  for (let i = 0; i < 6; i++) action.update(1);
  assert.equal(events.filter(e => e.type === 'suction').length, 1);
  assert.equal(events.filter(e => e.type === 'hitbox' && e.stage === 'suction').length, 3);
  assert.ok(events.some(e => e.type === 'control' && e.kind === 'release-window'));
  assert.deepEqual(action.hits, ['suction1', 'suction2', 'suction3', 'final']);
});

test('bloody rave skips suction for ungrabbable targets and clears on cancel', () => {
  const events = [], target = { status: { timers: { ungrabbable: 1 } } };
  const action = createBloodyRave({ target, targetStatus: target.status, emit: e => events.push(e) }, {}, { startup: 1, suction: 2, release: 1, final: 1, recovery: 4 });
  action.update(3);
  assert.equal(events.some(e => e.type === 'suction'), false);
  action.update(2);
  assert.equal(action.cancel(), true);
  assert.ok(events.some(e => e.type === 'cleanup'));
});
