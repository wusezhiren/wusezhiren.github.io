const assert = require('node:assert/strict');
const test = require('node:test');
const { createMomentarySlash } = require('../../../../src/combat/skills/blade/momentary-slash.js');

test('momentary slash stages charge, instant area slash, and recovery', () => {
  const events = [], clock = { hitstop: 0 };
  const action = createMomentarySlash({ direction: -1, clock, emit: e => events.push(e) }, { weapon: 'lightsword' }, { charge: 2, slash: 1, recovery: 2 });
  assert.deepEqual(action.phases.map(p => p.name), ['charge', 'slash', 'recovery']);
  action.update(2); action.update(1);
  assert.equal(events.filter(e => e.type === 'hitbox').length, 1);
  assert.equal(events.find(e => e.type === 'hitbox').radius, 104);
  assert.equal(clock.hitstop, 4);
  assert.equal(action.cancel(), true);
});

test('momentary slash parameterizes area radius across five weapons', () => {
  const weapons = ['lightsword', 'katana', 'greatsword', 'club', 'shortsword'];
  const radii = weapons.map(weapon => { const events = []; const action = createMomentarySlash({ weapon, emit: e => events.push(e) }, {}); action.update(20); return events.find(e => e.type === 'hitbox').radius; });
  assert.equal(new Set(radii).size, 5);
});
