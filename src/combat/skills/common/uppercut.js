(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {};
  root.DOF70.combat.skills.uppercut = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';

  function createUppercut(context = {}, auditData = {}, timeline = {}) {
    const emit = context.emit || (() => {});
    const phases = [
      { name: 'preparation', duration: timeline.startup ?? 4, cancelable: false },
      { name: 'uppercut', duration: timeline.active ?? 2, cancelable: false },
      { name: 'recovery', duration: timeline.recovery ?? 6, cancelable: true },
    ];
    const action = { phases, phase: phases[0], time: 0, done: false, _spent: false, _hit: false };
    const status = context.status;
    const resources = context.resources;

    function event(type, data = {}) { emit({ type, skill: 'uppercut', ...data }); }
    function enter(phase) {
      action.phase = phase;
      event('phase', { name: phase.name });
      if (phase.name === 'preparation' && !action._spent) {
        action._spent = true;
        if (resources) {
          resources.mp -= auditData.mp || 0;
          resources.cooldown = auditData.cooldown || 0;
        }
      }
      if (phase.name === 'uppercut') {
        if (status?.setTimer) status.setTimer('superArmor', auditData.superArmor ?? 8);
        event('hitbox', { launch: auditData.launch ?? 13, hitstun: auditData.hitstun ?? 18, radius: auditData.radius ?? 80 });
        event('hitstop', { duration: auditData.hitstop ?? 3 });
        if (context.freeze) context.freeze(auditData.hitstop ?? 3);
        else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, auditData.hitstop ?? 3);
        action._hit = true;
      }
    }
    event('body', { action: 'uppercut', airborne: false });
    event('weapon', { action: 'uppercut' });
    event('fx', { effect: 'uppercut' });
    event('phase', { name: phases[0].name });
    if (resources) {
      resources.mp -= auditData.mp || 0;
      resources.cooldown = auditData.cooldown || 0;
      action._spent = true;
    }
    action.update = function (delta = 1) {
      if (action.done || delta <= 0) return action;
      let next = action.time + delta;
      let elapsed = 0;
      for (const phase of phases) {
        if (next < elapsed + phase.duration) {
          if (action.phase !== phase) enter(phase);
          break;
        }
        elapsed += phase.duration;
      }
      action.time = next;
      if (action.time >= phases.reduce((sum, phase) => sum + phase.duration, 0)) action.done = true;
      return action;
    };
    action.cancel = function () {
      if (!action.done && action.phase.cancelable) { action.done = true; return true; }
      return false;
    };
    return action;
  }
  return { createUppercut };
});
