const assert = require('node:assert/strict');
const test = require('node:test');
const { BASIC_ACTIONS, resolveAction } = require('../../src/combat/action-player.js');

test('defines the complete basic action set with five weapon variants', () => {
  for (const name of ['stand','walk','run','jump_start','airborne','landing','hit_front','hit_back','float','down','get_up']) assert.ok(BASIC_ACTIONS[name]);
  assert.deepEqual(Object.keys(BASIC_ACTIONS.weapons), ['lightsword','katana','greatsword','club','shortsword']);
  for (const weapon of Object.values(BASIC_ACTIONS.weapons)) assert.ok(weapon.body && weapon.shadow && weapon.anchors);
});

test('resolves DOF timeline metadata and explicit target failures', () => {
  const timeline = { basic_actions: { stand: { status: 'verified', body: { frames: [], total: 1 } } } };
  assert.equal(resolveAction('stand', timeline).source, 'dof70');
  assert.throws(() => resolveAction('stand', { basic_actions: { stand: { status: 'failed' } } }), /DOF.*stand/);
  assert.equal(resolveAction('other', timeline).source, 'fallback');
});

test('resolves weapon-specific basic attacks without entering the skill fallback path', () => {
  for (const weapon of Object.keys(BASIC_ACTIONS.weapons)) {
    const action = resolveAction(`basic_${weapon}`, {});
    assert.equal(action.source, 'basic_weapon');
    assert.equal(action.weapon, true);
  }
});
