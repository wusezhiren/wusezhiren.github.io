const assert = require('node:assert/strict');
const test = require('node:test');
const { ActionPlayer, mirrorAnchors, weaponAction } = require('../../src/combat/action-player.js');

test('plays raw millisecond phases and emits each event once', () => {
  const events = [];
  const player = new ActionPlayer({ clock: { hitstop: 0 }, emit: e => events.push(e) });
  player.play({ name: 'slash', phases: [{ name: 'startup', duration: 100 }, { name: 'active', duration: 50, speedScalable: true }, { name: 'recovery', duration: 80 }], events: [{ at: 100, type: 'hit' }] });
  player.update(100, 2);
  assert.equal(player.phase.name, 'active');
  player.update(25, 2);
  assert.deepEqual(events.map(e => e.type), ['phase', 'hit', 'phase']);
  player.update(100, 2);
  assert.equal(events.filter(e => e.type === 'hit').length, 1);
  assert.equal(player.done, true);
});

test('hitstop pauses action, movement, events and buffered input', () => {
  const events = [];
  const clock = { hitstop: 20 };
  const player = new ActionPlayer({ clock, emit: e => events.push(e) });
  player.play({ phases: [{ name: 'active', duration: 100, move: 10 }], events: [{ at: 10, type: 'hit' }] });
  player.buffer('next');
  player.update(50, 1);
  assert.equal(player.time, 0);
  assert.equal(events.length, 0);
  assert.equal(player.position, 0);
  clock.hitstop = 0;
  player.update(10, 1);
  assert.equal(player.position, 100);
  assert.equal(events.filter(e => e.type === 'hit').length, 1);
  assert.equal(player.consumeBuffered(), 'next');
});

test('turning, cancellation and input buffering are deterministic', () => {
  const player = new ActionPlayer({ clock: { hitstop: 0 } });
  player.direction = 1;
  player.turn(-1);
  assert.equal(player.direction, -1);
  player.play({ phases: [{ name: 'recovery', duration: 100, cancelable: true }] });
  assert.equal(player.cancel(), true);
  assert.equal(player.done, true);
});

test('advances across multiple phases without losing movement or boundary events', () => {
  const events = [];
  const player = new ActionPlayer({ clock: { hitstop: 0 }, emit: e => events.push(e) });
  player.play({ phases: [
    { name: 'startup', duration: 10, move: 1 },
    { name: 'active', duration: 10, move: 2 },
    { name: 'recovery', duration: 10 },
  ] });
  player.update(25);
  assert.equal(player.time, 25);
  assert.equal(player.position, 30);
  assert.deepEqual(events.map(e => e.name), ['active', 'recovery']);
});

test('mirrors weapon anchors and exposes all five weapon actions', () => {
  assert.deepEqual(mirrorAnchors({ hand: [12, -4], origin: [0, 2] }, -1), { hand: [-12, -4], origin: [0, 2] });
  for (const weapon of ['lightsword', 'katana', 'greatsword', 'club', 'shortsword']) {
    assert.equal(weaponAction(weapon).name, `basic_${weapon}`);
  }
});
