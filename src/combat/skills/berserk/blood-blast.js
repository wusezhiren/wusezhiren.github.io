(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.bloodBlast = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  function createBloodBlast(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), base = data.dmg || [11, 13], count = data.hits ?? 4;
    const phases = [{ name: 'startup', duration: timeline.startup ?? 4 }, ...Array.from({ length: count }, (_, i) => ({ name: `spray${i + 1}`, duration: timeline.spray ?? (data.interval ?? 3) })), { name: 'final', duration: timeline.final ?? 3 }, { name: 'recovery', duration: timeline.recovery ?? 7, cancelable: true }];
    const action = { skill: 'blood-blast', phases, phase: phases[0], time: 0, done: false, hits: [] };
    const event = (type, value) => emit({ type, skill: action.skill, ...value });
    function enter(phase) { action.phase = phase; event('phase', { name: phase.name }); if (phase.name === 'startup') { event('body', { action: action.skill }); if (context.status?.setTimer) context.status.setTimer('superArmor', data.superArmor ?? 10); event('control', { kind: 'startup' }); } else if (phase.name.startsWith('spray')) { const index = Number(phase.name.slice(5)); action.hits.push(index); event('hitbox', { stage: 'spray', index, shape: 'blood-spray', damage: [Math.round(base[0]), Math.round(base[1])], radius: data.radius ?? 120, targetCooldown: data.hitInterval ?? 3, direction: context.direction < 0 ? -1 : 1 }); event('hitstop', { duration: data.hitstop ?? 2 }); if (context.freeze) context.freeze(data.hitstop ?? 2); else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 2); } else if (phase.name === 'final') { action.hits.push('final'); event('hitbox', { stage: 'final', shape: 'blood-burst', damage: [Math.round(base[0] * 2), Math.round(base[1] * 2)], radius: (data.radius ?? 120) + 20, launch: data.launch ?? 8, knock: data.knock ?? 16, direction: context.direction < 0 ? -1 : 1 }); } }
    enter(phases[0]); if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i]); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = () => !action.done && action.phase.cancelable ? (action.done = true, true) : false;
    return action;
  }
  return { createBloodBlast };
});
