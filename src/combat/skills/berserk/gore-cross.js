(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.goreCross = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  function createGoreCross(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), dir = context.direction < 0 ? -1 : 1;
    const base = data.dmg || [11, 13];
    const phases = [
      { name: 'horizontal', duration: timeline.horizontal ?? 3 },
      { name: 'vertical', duration: timeline.vertical ?? 3 },
      { name: 'bloodCross', duration: timeline.bloodCross ?? 5 },
      { name: 'recovery', duration: timeline.recovery ?? 8, cancelable: true },
    ];
    const action = { skill: 'gore-cross', phases, phase: phases[0], time: 0, done: false, hits: [] };
    const event = (type, value) => emit({ type, skill: action.skill, ...value });
    const damage = [Math.round(base[0]), Math.round(base[1])];
    function enter(phase, index) {
      action.phase = phase; event('phase', { name: phase.name });
      if (phase.name === 'horizontal' || phase.name === 'vertical' || phase.name === 'bloodCross') {
        action.hits.push(phase.name);
        const shape = phase.name === 'horizontal' ? 'horizontal' : phase.name === 'vertical' ? 'vertical' : 'cross';
        event('hitbox', { stage: phase.name, shape, damage, reach: data.reach ?? 86, radius: data.radius, direction: dir, hitId: phase.name, targetCooldown: phase.name === 'bloodCross' ? (data.hitInterval ?? 8) : 0, launch: phase.name === 'bloodCross' ? (data.launch ?? 5) : 0 });
        event('hitstop', { duration: data.hitstop ?? 2 });
        if (context.freeze) context.freeze(data.hitstop ?? 2);
        else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 2);
      }
    }
    event('body', { action: action.skill, direction: dir }); event('weapon', { action: action.skill }); event('fxOnce', { fxId: action.skill }); enter(phases[0], 0);
    if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) {
      if (action.done || delta <= 0) return action;
      const before = action.time; action.time += delta; let boundary = phases[0].duration;
      for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i], i); boundary += phases[i].duration; }
      if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action;
    };
    action.cancel = () => !action.done && action.phase.cancelable ? (action.done = true, true) : false;
    return action;
  }
  return { createGoreCross };
});
