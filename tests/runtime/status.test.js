const assert = require('node:assert/strict');
const test = require('node:test');
const status = require('../../src/combat/status.js');

test('tracks invincibility, hit immunity and super armor independently', () => {
  const s = status.createStatus();
  status.setTimer(s, 'invincible', 100);
  status.setTimer(s, 'hitImmunity', 50);
  status.setTimer(s, 'superArmor', 80);
  assert.equal(status.canHit(s), false);
  assert.equal(status.hasSuperArmor(s), true);
  status.tick(s, 50);
  assert.equal(status.canHit(s), false);
  assert.equal(status.hasSuperArmor(s), true);
  status.tick(s, 50);
  assert.equal(status.canHit(s), true);
  assert.equal(status.hasSuperArmor(s), false);
});

test('transitions hitstun, launch, landing, knockdown and getup without protection', () => {
  const s = status.createStatus();
  status.applyHitstun(s, 20);
  assert.equal(s.state, 'hitstun');
  status.launch(s, 12);
  assert.equal(s.state, 'launched');
  status.land(s);
  assert.equal(s.state, 'knockdown');
  status.tick(s, s.timers.knockdown);
  assert.equal(s.state, 'getup');
  status.tick(s, s.timers.getup);
  assert.equal(s.state, 'idle');
  assert.equal(status.canHit(s), true);
});

test('supports grab, held target, suction and per-target hit intervals', () => {
  const s = status.createStatus();
  const target = {};
  status.grab(s, target, 30);
  assert.equal(status.isHolding(s, target), true);
  assert.equal(status.isUngrabbable(s), false);
  status.suction(s, target, 12);
  assert.equal(s.suction.target, target);
  assert.equal(status.canHitTarget(s, target, 10), true);
  status.recordHit(s, target, 10);
  assert.equal(status.canHitTarget(s, target, 10), false);
  status.tick(s, 10);
  assert.equal(status.canHitTarget(s, target, 10), true);
});

test('hitstop freezes the shared combat clock', () => {
  const clock = status.createClock();
  status.freeze(clock, 40);
  assert.equal(status.advanceClock(clock, 16), 0);
  assert.equal(clock.hitstop, 40);
  status.tickClock(clock, 16);
  assert.equal(clock.hitstop, 24);
  assert.equal(status.advanceClock(clock, 16), 0);
  status.tickClock(clock, 24);
  assert.equal(status.advanceClock(clock, 16), 16);
});

test('clears held targets when grab expires and keeps hit intervals target-local', () => {
  const s = status.createStatus();
  const first = {};
  const second = {};
  status.grab(s, first, 2);
  status.recordHit(s, first, 5);
  status.recordHit(s, second, 3);
  status.tick(s, 2);
  assert.equal(status.isHolding(s, first), false);
  assert.equal(status.canHitTarget(s, first), false);
  assert.equal(status.canHitTarget(s, second), false);
  status.tick(s, 3);
  assert.equal(status.canHitTarget(s, first), true);
  assert.equal(status.canHitTarget(s, second), true);
});
