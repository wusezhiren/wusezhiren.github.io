(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = root.DOF70.combat.skills || {};
  root.DOF70.combat.skills.weaponCombo = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const BRANCHES = {
    lightsword: { reach: [78, 86, 94, 102, 112], move: [18, 22, 26, 30, 34] },
    katana: { reach: [84, 92, 100, 108, 116], move: [20, 24, 28, 32, 38] },
    greatsword: { reach: [92, 100, 108, 116, 124], move: [12, 16, 20, 24, 27] },
    club: { reach: [82, 90, 98, 106, 114], move: [14, 18, 22, 25, 25] },
    shortsword: { reach: [76, 84, 92, 100, 108], move: [22, 26, 30, 36, 42] },
  };
  function createWeaponCombo(context = {}, data = {}, timeline = {}) {
    const emit = context.emit || (() => {}), weapon = data.weapon || context.weapon || 'lightsword';
    const branch = BRANCHES[weapon] || BRANCHES.lightsword, base = data.dmg || [32, 40];
    const phases = Array.from({ length: 5 }, (_, i) => ({ name: `weapon${i + 1}`, duration: timeline[`weapon${i + 1}`] ?? 3, cancelable: i === 4 }));
    const action = { skill: 'weapon-combo', weapon, phases, phase: phases[0], time: 0, done: false, hits: [] };
    const event = (type, value) => emit({ type, skill: action.skill, weapon, ...value });
    function enter(phase, index) {
      action.phase = phase; action.hits.push(index); const direction = context.direction < 0 ? -1 : 1;
      event('phase', { name: phase.name, index }); event('turn', { direction, index });
      event('move', { distance: branch.move[index - 1] * direction, direction, index });
      event('hitbox', { index, damage: [Math.round(base[0] * (1 + index * .04)), Math.round(base[1] * (1 + index * .04))], reach: branch.reach[index - 1], direction, knock: index === 5 ? (data.knock ?? 16) : 2 });
      event('hitstop', { duration: data.hitstop ?? 2 });
      if (context.freeze) context.freeze(data.hitstop ?? 2);
      else if (context.clock) context.clock.hitstop = Math.max(context.clock.hitstop || 0, data.hitstop ?? 2);
    }
    event('body', { action: 'weapon-combo', direction: context.direction < 0 ? -1 : 1 }); event('weapon', { action: `weapon-combo-${weapon}` }); enter(phases[0], 1);
    action.update = function (delta = 1) { if (action.done || delta <= 0) return action; const before = action.time; action.time += delta; let boundary = phases[0].duration; for (let i = 1; i < phases.length; i++) { if (before < boundary && action.time >= boundary) enter(phases[i], i + 1); boundary += phases[i].duration; } if (action.time >= phases.reduce((n, p) => n + p.duration, 0)) action.done = true; return action; };
    action.cancel = () => action.phase.cancelable && (action.done = true);
    return action;
  }
  return { createWeaponCombo, BRANCHES };
});
