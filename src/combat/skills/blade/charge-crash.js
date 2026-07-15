(function (root, factory) {
  const api = factory(); root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {}; root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.chargeCrash = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const WEAPONS = { lightsword: { damage: 1, reach: 74, charge: 72 }, katana: { damage: 1.05, reach: 78, charge: 80 }, greatsword: { damage: 1.25, reach: 88, charge: 60 }, club: { damage: 1.18, reach: 70, charge: 55 }, shortsword: { damage: .9, reach: 68, charge: 88 } };
  function createChargeCrash(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), weapon = WEAPONS[data.weapon || context.weapon] || WEAPONS.lightsword, dir = context.direction < 0 ? -1 : 1, base = data.dmg || [40, 50];
    const phases = [{ name: 'charge', duration: timeline.charge ?? 8, move: data.chargeDistance || weapon.charge }, { name: 'impact', duration: timeline.impact ?? 2, move: 0 }, { name: 'uppercut', duration: timeline.uppercut ?? 3, move: data.uppercutDistance || 10 }, { name: 'recovery', duration: timeline.recovery ?? 6, move: 0 }];
    const action = { skill: 'charge-crash', weapon: data.weapon || context.weapon || 'lightsword', phases, phase: phases[0], time: 0, done: false, hits: [] };
    const event = (type, value) => emit({ type, skill: action.skill, weapon: action.weapon, ...value });
    function enter(phase, index) { action.phase = phase; event('phase', { name: phase.name }); if (phase.name === 'charge') event('move', { distance: phase.move * dir, direction: dir }); if (phase.name === 'impact') { action.hits.push('impact'); event('hitbox', { stage: 'impact', damage: data.impactDamage || Math.round(base[0] * weapon.damage * .55), reach: data.impactReach || weapon.reach, direction: dir }); } if (phase.name === 'uppercut') { action.hits.push('uppercut'); if (context.status?.setTimer) context.status.setTimer('superArmor', data.superArmor ?? 8); event('hitbox', { stage: 'uppercut', damage: data.uppercutDamage || Math.round(base[1] * weapon.damage), reach: data.uppercutReach || weapon.reach, launch: data.launch ?? 14, hitstun: data.hitstun ?? 18, direction: dir }); event('hitstop', { duration: data.hitstop ?? 3 }); if (context.freeze) context.freeze(data.hitstop ?? 3); else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 3); } }
    event('body', { action: 'charge-crash', direction: dir }); event('weapon', { action: 'charge-crash' }); event('fxOnce', { fxId: action.skill }); event('phase', { name: phases[0].name }); event('move', { distance: phases[0].move * dir, direction: dir });
    if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i], i); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = () => !action.done && action.phase.name === 'recovery' ? (action.done = true, true) : false;
    return action;
  }
  return { createChargeCrash, WEAPONS };
});
