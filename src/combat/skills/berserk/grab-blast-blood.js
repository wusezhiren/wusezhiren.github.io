(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.grabBlastBlood = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  function createGrabBlastBlood(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), dir = context.direction < 0 ? -1 : 1;
    const base = data.dmg || [60, 73], target = context.target || data.target;
    const targetStatus = context.targetStatus || target?.combatStatus || target?.status;
    const phases = [
      { name: 'startup', duration: timeline.startup ?? 3 },
      { name: 'grab', duration: timeline.grab ?? 2 },
      { name: 'blood', duration: timeline.blood ?? 4 },
      { name: 'recovery', duration: timeline.recovery ?? 7, cancelable: true },
    ];
    const action = { skill: 'grab-blast-blood', phases, phase: phases[0], time: 0, done: false, hits: [], grabbed: false, branch: null };
    const event = (type, value) => emit({ type, skill: action.skill, ...value });
    function statusUngrabbable() { return targetStatus?.isUngrabbable ? targetStatus.isUngrabbable(targetStatus) : !!targetStatus?.timers?.ungrabbable; }
    function cleanup() {
      if (context.release) context.release(target);
      if (targetStatus?.held === context.owner) targetStatus.held = null;
      if (targetStatus?.timers?.grab) targetStatus.timers.grab = 0;
      event('cleanup', { target });
    }
    function enter(phase) {
      action.phase = phase; event('phase', { name: phase.name });
      if (phase.name === 'startup') { event('body', { action: action.skill, direction: dir }); if (context.status?.setTimer) context.status.setTimer('superArmor', data.superArmor ?? 8); }
      if (phase.name === 'grab') {
        const boss = !!(target?.isBoss || target?.boss || target?.type === 'boss' || data.boss);
        const blocked = !target || statusUngrabbable();
        action.branch = blocked ? 'ungrabbable' : boss ? 'boss' : 'normal';
        event('control', { kind: blocked ? 'grab-failed' : 'grab', target, branch: action.branch });
        if (!blocked && context.status?.grab) { action.grabbed = context.status.grab(target, targetStatus, data.grabDuration ?? 8) !== false; }
        if (!blocked && action.grabbed) { event('bind', { target, duration: data.grabDuration ?? 8 }); action.hits.push('grab'); }
      }
      if (phase.name === 'blood') {
        const damage = action.branch === 'boss' || action.branch === 'ungrabbable' ? [Math.round(base[0] * (data.failMultiplier ?? .6)), Math.round(base[1] * (data.failMultiplier ?? .6))] : [Math.round(base[0]), Math.round(base[1])];
        action.hits.push('blood'); event('hitbox', { stage: 'blood', shape: 'blood-blast', damage, target, direction: dir, bound: action.grabbed });
        event('blood', { target, branch: action.branch });
        const heal = data.heal ?? Math.round((damage[0] + damage[1]) * .5 * (data.lifesteal ?? .3));
        if (context.resources && heal > 0) { context.resources.hp = Math.min(context.resources.maxhp ?? Infinity, (context.resources.hp ?? 0) + heal); event('heal', { amount: heal }); }
        event('hitstop', { duration: data.hitstop ?? 3 });
        if (context.freeze) context.freeze(data.hitstop ?? 3); else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 3);
      }
      if (phase.name === 'recovery') cleanup();
    }
    enter(phases[0]);
    if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i]); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) { action.done = true; cleanup(); } return action; };
    action.cancel = () => { if (action.done || !action.phase.cancelable) return false; action.done = true; cleanup(); return true; };
    return action;
  }
  return { createGrabBlastBlood };
});
