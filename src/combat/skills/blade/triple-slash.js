(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {};
  root.DOF70.combat.skills.tripleSlash = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const WEAPONS = {
    lightsword: { damage: 1, reach: 96, move: 30 }, katana: { damage: 1.05, reach: 102, move: 34 },
    greatsword: { damage: 1.2, reach: 112, move: 24 }, club: { damage: 1.15, reach: 90, move: 20 },
    shortsword: { damage: 0.92, reach: 88, move: 38 },
  };
  function createTripleSlash(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), weapon = WEAPONS[data.weapon || context.weapon] || WEAPONS.lightsword;
    const base = data.dmg || [16, 19], dir = context.direction < 0 ? -1 : 1;
    const phases = [{ name: 'slash1', duration: timeline.slash1 ?? 4, move: weapon.move }, { name: 'slash2', duration: timeline.slash2 ?? 4, move: weapon.move }, { name: 'slash3', duration: timeline.slash3 ?? 4, move: weapon.move }].map(p => ({ ...p, cancelable: false }));
    const action = { skill: 'triple-slash', weapon: data.weapon || context.weapon || 'lightsword', phases, phase: phases[0], time: 0, done: false, hits: [] };
    const event = (type, value) => emit({ type, skill: action.skill, weapon: action.weapon, ...value });
    function enter(phase, index) { action.phase = phase; event('phase', { name: phase.name }); action.hits.push(index); event('move', { distance: phase.move * dir, direction: dir, index }); event('hitbox', { index, damage: [Math.round(base[0] * weapon.damage), Math.round(base[1] * weapon.damage)], reach: data.reach || weapon.reach, direction: dir, hitstop: data.hitstop ?? 2 }); event('hitstop', { duration: data.hitstop ?? 2 }); if (context.freeze) context.freeze(data.hitstop ?? 2); else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 2); }
     event('body', { action: 'triple-slash', direction: dir }); event('weapon', { action: 'triple-slash' }); event('fxOnce', { fxId: action.skill }); enter(phases[0], 1);
    if (context.resources && !action.spent) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i], i + 1); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = () => false;
    return action;
  }
  return { createTripleSlash, WEAPONS };
});
