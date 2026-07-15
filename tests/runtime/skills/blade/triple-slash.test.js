const assert = require('node:assert/strict');
const test = require('node:test');
const { createTripleSlash } = require('../../../../src/combat/skills/blade/triple-slash.js');

test('triple slash has three independent directional movement and hit stages', () => {
  const events = [], clock = { hitstop: 0 };
  const action = createTripleSlash({ direction: -1, clock, emit: e => events.push(e), resources: { mp: 20, cooldown: 0 } }, { weapon: 'katana', mp: 4, cooldown: 360 }, { slash1: 1, slash2: 1, slash3: 1 });
  action.update(1); action.update(1); action.update(1);
  assert.deepEqual(action.hits, [1, 2, 3]);
  assert.deepEqual(events.filter(e => e.type === 'move').map(e => e.direction), [-1, -1, -1]);
  assert.equal(events.filter(e => e.type === 'hitbox').length, 3);
  assert.equal(events.filter(e => e.type === 'hitstop').length, 3);
});

test('triple slash uses distinct parameters for all five weapons', () => {
  const weapons = ['lightsword', 'katana', 'greatsword', 'club', 'shortsword'];
  const reaches = weapons.map(weapon => { const events = []; createTripleSlash({ weapon, emit: e => events.push(e) }, {}).update(4); return events.find(e => e.type === 'hitbox').reach; });
  assert.equal(new Set(reaches).size, 5);
});
