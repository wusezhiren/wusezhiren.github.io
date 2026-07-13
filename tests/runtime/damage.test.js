const assert = require('node:assert/strict');
const test = require('node:test');
const damage = require('../../src/combat/damage.js');

test('applies level fluctuation, primary stat and physical defense to percent damage', () => {
  assert.equal(damage.resolveDamage({
    channel: 'percent', base: 100, level: 70, physicalPrimaryStat: 250,
    defense: 200, random: () => 1, critical: false,
  }), 241);
});

test('fixed and absolute damage bypass ordinary physical defense', () => {
  const input = { level: 70, physicalPrimaryStat: 999, defense: 99999, random: () => -1 };
  assert.equal(damage.resolveDamage({ ...input, channel: 'fixed', base: 100 }), 100);
  assert.equal(damage.resolveDamage({ ...input, channel: 'absolute', base: 100 }), 100);
});

test('uses 1.5 critical damage and truncates toward zero after later multipliers', () => {
  assert.equal(damage.resolveDamage({
    channel: 'fixed', base: 7, critical: true, multiplier: 1.1,
  }), 11);
  assert.equal(damage.resolveDamage({
    channel: 'fixed', base: -7, multiplier: 1.1,
  }), -7);
});
