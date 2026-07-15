(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {};
  root.DOF70.combat.skills.illusionSlash = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const WEAPONS = { lightsword: 1, katana: 1.05, greatsword: 1.2, club: 1.15, shortsword: .92 };
  function createIllusionSlash(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), weapon = data.weapon || context.weapon || 'lightsword', mul = WEAPONS[weapon] || 1;
    const speed = Math.max(.1, data.speedMultiplier || 1), duration = (name, fallback, scalable) => Math.max(1, Math.round((timeline[name] ?? fallback) / (scalable ? speed : 1)));
    const phases = [{ name: 'preparation', duration: duration('preparation', 6, true), cancelable: false }, { name: 'slashes', duration: duration('slashes', 20, false), cancelable: false }, { name: 'sword-wave', duration: duration('swordWave', 3, false), cancelable: false }, { name: 'recovery', duration: duration('recovery', 8, true), cancelable: true }];
    const action = { skill: 'illusion-slash', weapon, phases, phase: phases[0], time: 0, done: false, hits: [], direction: context.direction < 0 ? -1 : 1 };
    if (context.resources && !action.spent) { context.resources.mp -= data.mp || 0; context.resources.cooldown = data.cooldown || 0; action.spent = true; }
    const event = (type, value) => emit({ type, skill: action.skill, weapon, ...value });
    function enter(phase) {
      action.phase = phase; event('phase', { name: phase.name }); event('turn', { direction: action.direction });
      if (phase.name === 'slashes') for (let i = 1; i <= 10; i++) { action.hits.push(i); event('hitbox', { index: i, stage: 'slash', damage: [Math.round((data.dmg || [32, 40])[0] * mul), Math.round((data.dmg || [32, 40])[1] * mul)], reach: data.reach || 104, direction: action.direction, knock: 2 }); event('hitstop', { duration: data.hitstop ?? 1 }); }
      if (phase.name === 'sword-wave') { action.hits.push('wave'); event('hitbox', { stage: 'sword-wave', index: 'wave', damage: data.waveDamage || [Math.round(80 * mul), Math.round(100 * mul)], reach: data.waveReach || 150, direction: action.direction, knock: data.knock ?? 18 }); event('hitstop', { duration: data.waveHitstop ?? 3 }); }
      if (phase.name === 'recovery') event('status', { invincible: 0, superArmor: 0 });
    }
     event('body', { action: 'illusion-slash', direction: action.direction }); event('weapon', { action: 'illusion-slash' }); event('fxOnce', { fxId: action.skill }); enter(phases[0]);
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = 0; for (const phase of phases) { if (before < boundary + phase.duration && action.time >= boundary + phase.duration && phase !== action.phase) enter(phase); boundary += phase.duration; } if (action.time >= boundary) action.done = true; return action; };
    action.cancel = () => false;
    return action;
  }
  return { createIllusionSlash, WEAPONS };
});
