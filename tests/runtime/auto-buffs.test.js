const assert = require('node:assert/strict');
const test = require('node:test');
const { ActionPlayer } = require('../../src/combat/action-player.js');
const { createAutoBuffController } = require('../../src/combat/passives.js');

function setup(overrides = {}) {
  const events = [];
  const resources = overrides.resources || { mp: 100, cooldown: {} };
  const player = new ActionPlayer({ clock: { hitstop: 0 } });
  const controller = createAutoBuffController({ actionPlayer: player, resources, emit: e => events.push(e), ...overrides });
  return { controller, player, resources, events };
}

test('auto buffs use real action duration and spend resources before applying', () => {
  const { controller, player, resources, events } = setup();
  controller.enterRoom();
  assert.equal(controller.active, 'bloodRage');
  assert.equal(resources.mp, 92);
  assert.equal(controller.buffs.bloodRage, undefined);
  for (let i = 0; i < 25; i++) { player.update(1); controller.update(1); }
  assert.equal(controller.buffs.bloodRage, true);
  assert.ok(events.some(e => e.type === 'auto-buff' && e.name === 'bloodRage'));
});

test('delays while hit, down, or another action is running and auto-renews after cooldown', () => {
  const { controller, player, events } = setup({ status: { state: 'hitstun' } });
  controller.enterRoom();
  assert.equal(controller.active, null);
  controller.status.state = 'idle';
  player.play({ phases: [{ name: 'skill', duration: 20 }] });
  controller.update(1);
  assert.equal(controller.active, null);
  for (let i = 0; i < 25; i++) { player.update(1); controller.update(1); }
  assert.equal(controller.active, 'bloodRage');
  for (let i = 0; i < 60; i++) { player.update(1); controller.update(1); }
  assert.ok(events.filter(e => e.type === 'auto-buff').length >= 2);
});

test('does not alias the old frenzy skill name and waits for resources', () => {
  const { controller, resources } = setup({ resources: { mp: 0 } });
  controller.enterRoom();
  assert.equal(controller.active, null);
  assert.equal(controller.buffs.frenzy, undefined);
  resources.mp = 100;
  controller.update(1);
  assert.equal(controller.active, 'bloodRage');
});
