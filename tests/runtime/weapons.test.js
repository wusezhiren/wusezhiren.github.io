const assert = require('node:assert/strict');
const test = require('node:test');
const weapons = require('../../src/equipment/weapons.js');

test('defines the five stable level 70 weapon types', () => {
  assert.deepEqual(Object.keys(weapons.WEAPON_TYPES), ['lightsword', 'katana', 'greatsword', 'club', 'shortsword']);
  for (const weapon of Object.values(weapons.WEAPON_TYPES)) {
    assert.equal(weapon.level, 70);
    assert.equal(typeof weapon.physicalAttack, 'number');
    assert.equal(typeof weapon.attackSpeed, 'number');
    assert.ok(Array.isArray(weapon.classRestrictions));
  }
});

test('enforces class restrictions without changing classes', () => {
  assert.equal(weapons.canUseWeapon('blade', 'lightsword'), true);
  assert.equal(weapons.canUseWeapon('blade', 'club'), true);
  assert.equal(weapons.canUseWeapon('berserk', 'katana'), true);
  assert.equal(weapons.canUseWeapon('berserk', 'lightsword'), false);
  assert.equal(weapons.canUseWeapon('berserk', 'unknown'), false);
});

test('normalizes typed weapons while preserving unknown fields', () => {
  const item = weapons.normalizeWeapon({ id: 'old-id', rarity: 'purple', type: 'weapon', custom: { tag: 1 } }, 'blade');
  assert.equal(item.id, 'old-id');
  assert.equal(item.rarity, 'purple');
  assert.deepEqual(item.custom, { tag: 1 });
  assert.equal(item.weaponType, 'lightsword');
  assert.equal(item.level, 70);
  assert.equal(item.kind, 'equip');
});
