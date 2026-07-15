(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.bloodyRave = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  function createBloodyRave(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), target = context.target || data.target, base = data.dmg || [115, 140];
    const targetStatus = context.targetStatus || target?.combatStatus || target?.status;
    const count = data.hits ?? 6, phases = [{ name: 'startup', duration: timeline.startup ?? 3 }, { name: 'suction', duration: timeline.suction ?? 12 }, { name: 'release', duration: timeline.release ?? 3 }, { name: 'final', duration: timeline.final ?? 3 }, { name: 'recovery', duration: timeline.recovery ?? 7, cancelable: true }];
    const action = { skill: 'bloody-rave', phases, phase: phases[0], time: 0, done: false, hits: [], released: false };
    const event = (type, value) => emit({ type, skill: action.skill, ...value });
    function canGrab() { return target && !(targetStatus?.timers?.ungrabbable || target?.ungrabbable) && !(target?.dead); }
    function cleanup() { if (context.clearSuction) context.clearSuction(target); if (targetStatus?.suction?.target === context.owner || targetStatus?.suction?.target === target) targetStatus.suction = { target: null, time: 0 }; event('cleanup', { target }); }
    function enter(phase) { action.phase = phase; event('phase', { name: phase.name }); if (phase.name === 'startup') { event('body', { action: action.skill }); if (context.status?.setTimer) context.status.setTimer('superArmor', data.superArmor ?? 18); } if (phase.name === 'suction') { if (canGrab()) { if (context.status?.suction) context.status.suction(target, data.suctionDuration ?? phase.duration); event('suction', { target, duration: phase.duration }); for (let i = 1; i <= count; i++) { action.hits.push(`suction${i}`); event('hitbox', { stage: 'suction', index: i, target, shape: 'blood-seal', damage: base, targetCooldown: data.hitInterval ?? 2 }); } } } if (phase.name === 'release') { action.released = true; event('control', { kind: 'release-window', target }); } if (phase.name === 'final') { action.hits.push('final'); event('hitbox', { stage: 'final', target, shape: 'rave-slash', damage: [Math.round(base[0] * 2), Math.round(base[1] * 2)], launch: data.launch ?? 8 }); event('hitstop', { duration: data.hitstop ?? 4 }); if (context.freeze) context.freeze(data.hitstop ?? 4); } if (phase.name === 'recovery') cleanup(); }
    enter(phases[0]); if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i]); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) { action.done = true; cleanup(); } return action; };
    action.cancel = () => { if (action.done || !action.phase.cancelable) return false; action.done = true; cleanup(); return true; };
    return action;
  }
  return { createBloodyRave };
});
