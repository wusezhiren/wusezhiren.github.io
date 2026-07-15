const assert = require('node:assert/strict');
const test = require('node:test');
const monsters = require('../../src/monsters/dof70.js');

test('exports level 70 normal, elite and boss templates', () => {
  assert.deepEqual(Object.keys(monsters.MONSTERS_DOF70), ['normal', 'elite', 'boss']);
  for (const template of Object.values(monsters.MONSTERS_DOF70)) {
    assert.equal(template.level, 70);
    for (const field of ['hp', 'defense', 'staggerResistance', 'floatResistance', 'grabResistance']) {
      assert.equal(typeof template[field], 'number');
    }
  }
});

test('creates independent monster stats without difficulty scaling', () => {
  const a = monsters.createMonster('normal');
  const b = monsters.createMonster('normal');
  assert.deepEqual(a, b);
  assert.notEqual(a, b);
  assert.equal(monsters.createMonster('boss').hp, monsters.MONSTERS_DOF70.boss.hp);
});
