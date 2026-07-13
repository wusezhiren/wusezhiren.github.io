(function (root, factory) {
  const api = factory(); root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {}; root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.momentarySlash = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const WEAPONS = { lightsword: { damage: 1, radius: 104, charge: 8 }, katana: { damage: 1.1, radius: 112, charge: 7 }, greatsword: { damage: 1.3, radius: 122, charge: 11 }, club: { damage: 1.2, radius: 108, charge: 10 }, shortsword: { damage: .94, radius: 96, charge: 5 } };
  function createMomentarySlash(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), weapon = WEAPONS[data.weapon || context.weapon] || WEAPONS.lightsword, dir = context.direction < 0 ? -1 : 1, base = data.dmg || [122, 148];
    const phases = [{ name: 'charge', duration: timeline.charge ?? weapon.charge, move: 0, cancelable: true }, { name: 'slash', duration: timeline.slash ?? 2, move: 0, cancelable: false }, { name: 'recovery', duration: timeline.recovery ?? 8, move: 0, cancelable: true }];
    const action = { skill: 'momentary-slash', weapon: data.weapon || context.weapon || 'lightsword', phases, phase: phases[0], time: 0, done: false, hit: false };
    const event = (type, value) => emit({ type, skill: action.skill, weapon: action.weapon, ...value });
    function enter(phase) { action.phase = phase; event('phase', { name: phase.name }); if (phase.name === 'slash') { action.hit = true; event('hitbox', { stage: 'slash', damage: [Math.round(base[0] * weapon.damage), Math.round(base[1] * weapon.damage)], radius: data.radius || weapon.radius, direction: dir, knock: data.knock ?? 18 }); event('hitstop', { duration: data.hitstop ?? 4 }); if (context.freeze) context.freeze(data.hitstop ?? 4); else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 4); } }
    event('body', { action: 'momentary-slash', direction: dir }); event('weapon', { action: 'momentary-slash' }); event('phase', { name: phases[0].name });
    if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i]); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = function () { if (!action.done && action.phase.cancelable) { action.done = true; return true; } return false; };
    return action;
  }
  return { createMomentarySlash, WEAPONS };
});
