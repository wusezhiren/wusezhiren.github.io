const assert = require('node:assert/strict');
const test = require('node:test');
const { migrateSave, SAVE_SCHEMA_VERSION } = require('../../src/save/migrations.js');

test('migrates legacy generic swords to the class default', () => {
  const old = { high: 4, run: { clsKey: 'berserk', equipped: { weapon: { id: 9, type: 'weapon', rarity: 'blue', stats: { atk: .2 } } } } };
  const result = migrateSave(old);
  assert.equal(result.save.schemaVersion, SAVE_SCHEMA_VERSION);
  assert.equal(result.save.run.equipped.weapon.weaponType, 'katana');
  assert.equal(result.save.high, 4);
});

test('unknown weapon types fall back with a notice and migration is idempotent', () => {
  const old = { schemaVersion: 1, run: { clsKey: 'blade', equipped: { weapon: { weaponType: 'laser', extra: true } } } };
  const once = migrateSave(old);
  const twice = migrateSave(once.save);
  assert.equal(once.save.run.equipped.weapon.weaponType, 'lightsword');
  assert.ok(once.notices.length);
  assert.deepEqual(twice.save, once.save);
  assert.deepEqual(twice.notices, []);
});

test('does not auto-change a class when an equipped weapon is forbidden', () => {
  const result = migrateSave({ run: { clsKey: 'berserk', equipped: { weapon: { weaponType: 'lightsword' } } } });
  assert.equal(result.save.run.clsKey, 'berserk');
  assert.equal(result.save.run.equipped.weapon, null);
  assert.ok(result.notices.some(n => /职业限制/.test(n)));
});
