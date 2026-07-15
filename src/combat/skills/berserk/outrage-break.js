(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {}; root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {}; root.DOF70.combat.skills.outrageBreak = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  function createOutrageBreak(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), dir = context.direction < 0 ? -1 : 1, base = data.dmg || [30, 36], cost = data.hpCost ?? 64, eruptions = data.eruptions ?? 6;
    const phases = [{ name: 'leap', duration: timeline.leap ?? 5 }, { name: 'descent', duration: timeline.descent ?? 5 }, { name: 'impact', duration: timeline.impact ?? 2 }, ...Array.from({ length: eruptions }, (_, i) => ({ name: `eruption${i + 1}`, duration: timeline.eruption ?? 2 })), { name: 'recovery', duration: timeline.recovery ?? 7, cancelable: true }];
    const action = { skill: 'outrage-break', phases, phase: phases[0], time: 0, done: false, hits: [], failed: false, spent: false };
    const event = (type, value) => emit({ type, skill: action.skill, ...value });
    const hp = context.resources?.hp ?? context.hp;
    if (cost > 0 && hp !== undefined && hp <= cost) { action.failed = true; action.done = true; event('resource', { kind: 'insufficient-hp', required: cost, available: hp }); return action; }
    function restore() { if (context.status?.clearTimer) { context.status.clearTimer('superArmor'); context.status.clearTimer('invincible'); } else if (context.statusState?.timers) { context.statusState.timers.superArmor = 0; context.statusState.timers.invincible = 0; } event('land', { recover: true }); }
    function enter(phase) { action.phase = phase; event('phase', { name: phase.name }); if (phase.name === 'leap') { if (context.resources && cost) { context.resources.hp -= cost; action.spent = true; } event('body', { action: action.skill, airborne: true, direction: dir }); if (context.status?.setTimer) { context.status.setTimer('superArmor', data.superArmor ?? 20); context.status.setTimer('invincible', data.invincible ?? 8); } event('move', { distance: (data.leapDistance ?? 50) * dir, direction: dir, airborne: true }); } else if (phase.name === 'descent') event('move', { distance: (data.leapDistance ?? 50) * dir, direction: dir, airborne: true }); else if (phase.name === 'impact') { action.hits.push('impact'); event('hitbox', { stage: 'impact', shape: 'ground-slam', damage: base, radius: data.radius ?? 150, direction: dir }); event('hitstop', { duration: data.hitstop ?? 4 }); if (context.freeze) context.freeze(data.hitstop ?? 4); } else if (phase.name.startsWith('eruption')) { const index = Number(phase.name.slice(8)); action.hits.push(index); event('hitbox', { stage: 'eruption', index, shape: 'lava', damage: base, radius: data.eruptionRadius ?? 55, direction: dir, targetCooldown: data.hitInterval ?? 1 }); event('lava', { index }); } else if (phase.name === 'recovery') restore(); }
    enter(phases[0]); if (context.resources) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = action.spent || !!data.mp; }
    action.update = function (delta = 1) { if (action.done || action.failed || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i]); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = () => { if (action.done || !action.phase.cancelable) return false; action.done = true; restore(); return true; };
    return action;
  }
  return { createOutrageBreak };
});
