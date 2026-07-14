(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.hopSmash = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  function createHopSmash(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), dir = context.direction < 0 ? -1 : 1, base = data.dmg || [23, 28];
    const phases = [
      { name: 'leap', duration: timeline.leap ?? 5 }, { name: 'forward', duration: timeline.forward ?? 5 },
      { name: 'downward', duration: timeline.downward ?? 2 }, { name: 'landing', duration: timeline.landing ?? 2 },
      { name: 'shockwave', duration: timeline.shockwave ?? 3 }, { name: 'recovery', duration: timeline.recovery ?? 7, cancelable: true },
    ];
    const action = { skill: 'hop-smash', phases, phase: phases[0], time: 0, done: false, hits: [] };
    const event = (type, value) => emit({ type, skill: action.skill, ...value });
    function enter(phase) {
      action.phase = phase; event('phase', { name: phase.name });
      if (phase.name === 'leap') { event('body', { action: action.skill, airborne: true, direction: dir }); if (context.status?.setTimer) context.status.setTimer('superArmor', data.superArmor ?? 12); event('move', { distance: (data.forwardDistance ?? 55) * dir, direction: dir, airborne: true }); }
      if (phase.name === 'forward') event('move', { distance: (data.forwardDistance ?? 55) * dir, direction: dir, airborne: true });
      if (phase.name === 'downward') event('body', { action: action.skill, airborne: true, direction: dir });
      if (phase.name === 'landing') event('land', { recover: true });
      if (phase.name === 'shockwave') { action.hits.push('shockwave'); event('hitbox', { stage: 'shockwave', shape: 'ground-wave', damage: [Math.round(base[0]), Math.round(base[1])], radius: data.radius ?? 105, direction: dir, knock: data.knock ?? 12 }); event('hitstop', { duration: data.hitstop ?? 3 }); if (context.freeze) context.freeze(data.hitstop ?? 3); else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 3); }
    }
    event('body', { action: action.skill, direction: dir }); enter(phases[0]);
    if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i]); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = () => !action.done && action.phase.cancelable ? (action.done = true, true) : false;
    return action;
  }
  return { createHopSmash };
});
