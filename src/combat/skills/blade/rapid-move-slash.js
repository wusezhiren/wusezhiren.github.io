(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {};
  root.DOF70.combat.skills.rapidMoveSlash = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const WEAPONS = {
    lightsword: { damage: 1, reach: 92, move: 34 }, katana: { damage: 1.05, reach: 100, move: 38 },
    greatsword: { damage: 1.2, reach: 110, move: 27 }, club: { damage: 1.15, reach: 96, move: 25 },
    shortsword: { damage: 0.92, reach: 88, move: 42 },
  };
  function createRapidMoveSlash(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), name = data.weapon || context.weapon || 'lightsword';
    const weapon = WEAPONS[name] || WEAPONS.lightsword, base = data.dmg || [22, 26];
    const phases = Array.from({ length: 5 }, (_, i) => ({ name: `dash${i + 1}`, duration: timeline[`dash${i + 1}`] ?? 3, move: weapon.move, cancelable: false }));
    const action = { skill: 'rapid-move-slash', weapon: name, phases, phase: phases[0], time: 0, done: false, hits: [] };
    if (context.resources && !action.spent) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    const event = (type, value) => emit({ type, skill: action.skill, weapon: name, ...value });
    function enter(phase, index) {
      action.phase = phase; action.hits.push(index);
      const direction = context.direction < 0 ? -1 : 1;
      event('phase', { name: phase.name, index });
      event('turn', { direction, index });
      event('move', { distance: phase.move * direction, direction, index });
      if (context.status?.setTimer) {
        context.status.setTimer('superArmor', data.superArmor ?? 3);
        context.status.setTimer('invincible', data.invincible ?? 1);
      }
      event('status', { superArmor: data.superArmor ?? 3, invincible: data.invincible ?? 1, index });
      event('hitbox', { index, damage: [Math.round(base[0] * weapon.damage), Math.round(base[1] * weapon.damage)], reach: data.reach || weapon.reach, direction, knock: index === 5 ? (data.knock ?? 14) : 2 });
      event('hitstop', { duration: data.hitstop ?? 2 });
      if (context.freeze) context.freeze(data.hitstop ?? 2);
      else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 2);
    }
    event('body', { action: 'rapid-move-slash', direction: context.direction < 0 ? -1 : 1 });
    event('weapon', { action: 'rapid-move-slash' });
    enter(phases[0], 1);
    action.update = function (delta = 1) {
      if (action.done || delta <= 0) return action;
      const before = action.time; action.time += delta; let boundary = phases[0].duration;
      for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i], i + 1); boundary += phases[i].duration; }
      if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true;
      return action;
    };
    action.cancel = () => false;
    return action;
  }
  return { createRapidMoveSlash, WEAPONS };
});
