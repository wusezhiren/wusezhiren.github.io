const assert = require('node:assert/strict');
const test = require('node:test');
const passives = require('../../src/combat/passives.js');

test('keeps the nine audited swordman passives stable', () => {
  assert.deepEqual(passives.PASSIVE_AUDIT.map(p => p.name), [
    '武器奥义', '光剑精通', '太刀精通', '巨剑精通', '钝器精通', '短剑精通',
    '血气唤醒', '血之狂暴', '暴走',
  ]);
});

test('uses effectiveMasteryLevel for weapon mastery mapping', () => {
  assert.equal(passives.effectiveMasteryLevel(7, { 1: 0, 5: 2, 10: 4 }), 2);
  const effects = passives.getPassiveEffects({ classKey: 'blade', weaponType: 'greatsword', level: 70, masteryLevel: 10 });
  assert.equal(effects.mastery.level, passives.effectiveMasteryLevel(10));
  assert.ok(effects.mastery.attack > 0);
});

test('blood awakening scales with current HP, not room-entry HP', () => {
  const high = passives.getPassiveEffects({ classKey: 'berserk', level: 70, hp: 350, maxhp: 380 }).bloodAwakening;
  const low = passives.getPassiveEffects({ classKey: 'berserk', level: 70, hp: 95, maxhp: 380 }).bloodAwakening;
  assert.ok(low.attack > high.attack);
  assert.equal(passives.getPassiveEffects({ classKey: 'blade', hp: 1, maxhp: 100 }).bloodAwakening.attack, 0);
});
