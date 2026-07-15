const assert = require('node:assert/strict');
const test = require('node:test');
const { createRapidMoveSlash } = require('../../../../src/combat/skills/blade/rapid-move-slash.js');

test('rapid move slash has five independent dashes, hits, turns and short status windows', () => {
  const events = [], status = [], clock = { hitstop: 0 };
  const action = createRapidMoveSlash({ direction: -1, clock, emit: e => events.push(e), status: { setTimer: (n, v) => status.push([n, v]) } }, { weapon: 'katana' }, { dash1: 1, dash2: 1, dash3: 1, dash4: 1, dash5: 1 });
  for (let i = 0; i < 5; i++) action.update(1);
  assert.deepEqual(action.hits, [1, 2, 3, 4, 5]);
  assert.equal(events.filter(e => e.type === 'move').length, 5);
  assert.equal(events.filter(e => e.type === 'hitbox').length, 5);
  assert.equal(events.filter(e => e.type === 'turn').length, 5);
  assert.equal(status.filter(([name]) => name === 'invincible').length, 5);
  assert.ok(status.reduce((n, [name, value]) => n + (name === 'invincible' ? value : 0), 0) < 5 * 3);
});
