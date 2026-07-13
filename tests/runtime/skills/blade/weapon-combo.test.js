const assert = require('node:assert/strict');
const test = require('node:test');
const { createWeaponCombo } = require('../../../../src/combat/skills/blade/weapon-combo.js');

test('weapon combo exposes five complete weapon branches and five hits', () => {
  const weapons = ['lightsword', 'katana', 'greatsword', 'club', 'shortsword'];
  for (const weapon of weapons) {
    const events = [], resources = { mp: 99, cooldown: 0 };
    const action = createWeaponCombo({ weapon, emit: e => events.push(e), resources }, {}, { weapon1: 1, weapon2: 1, weapon3: 1, weapon4: 1, weapon5: 1 });
    for (let i = 0; i < 5; i++) action.update(1);
    assert.equal(events.filter(e => e.type === 'hitbox').length, 5);
    assert.equal(events.find(e => e.type === 'weapon').action, `weapon-combo-${weapon}`);
    assert.equal(resources.mp, 99);
    assert.equal(resources.cooldown, 0);
  }
});
