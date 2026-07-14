(function (root, factory) {
  const api = factory(root.DOF70?.combat?.action);
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.passives = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function (actionApi) {
  'use strict';

  const PASSIVE_AUDIT = Object.freeze([
    { id: 'weaponMastery', name: '武器奥义' },
    { id: 'lightSwordMastery', name: '光剑精通', weapon: 'lightsword' },
    { id: 'katanaMastery', name: '太刀精通', weapon: 'katana' },
    { id: 'greatSwordMastery', name: '巨剑精通', weapon: 'greatsword' },
    { id: 'bluntMastery', name: '钝器精通', weapon: 'club' },
    { id: 'shortSwordMastery', name: '短剑精通', weapon: 'shortsword' },
    { id: 'bloodAwakening', name: '血气唤醒' },
    { id: 'bloodRage', name: '血之狂暴' },
    { id: 'reckless', name: '暴走' },
  ]);
  const MASTERY_MAP = Object.freeze({ 0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10 });
  function effectiveMasteryLevel(level = 0, mapping = MASTERY_MAP) {
    const n = Math.max(0, Math.floor(Number(level) || 0));
    if (Array.isArray(mapping)) return mapping[Math.min(n, mapping.length - 1)] ?? 0;
    const keys = Object.keys(mapping).map(Number).filter(k => k <= n).sort((a, b) => a - b);
    return keys.length ? mapping[keys[keys.length - 1]] : 0;
  }
  function getPassiveEffects({ classKey = 'blade', weaponType = 'lightsword', level = 1, masteryLevel = level, hp = 1, maxhp = 1 } = {}) {
    const ml = effectiveMasteryLevel(masteryLevel);
    const masteryWeapon = PASSIVE_AUDIT.find(p => p.weapon === weaponType);
    const mastery = classKey === 'blade' && masteryWeapon ? { level: ml, attack: ml * 0.025, speed: ml * 0.008 } : { level: 0, attack: 0, speed: 0 };
    const ratio = maxhp > 0 ? Math.max(0, Math.min(1, hp / maxhp)) : 1;
    const bloodAwakening = classKey === 'berserk' ? { threshold: ratio, attack: Math.max(0, (0.7 - ratio) * 0.18), speed: Math.max(0, (0.7 - ratio) * 0.08) } : { threshold: ratio, attack: 0, speed: 0 };
    return { mastery: { weapon: weaponType, ...mastery }, bloodAwakening, bloodRage: classKey === 'berserk', berserk: classKey === 'berserk' };
  }

  const BUFFS = Object.freeze({ bloodRage: { cost: 8, duration: 600, cooldown: 30 }, berserk: { cost: 12, duration: 480, cooldown: 120 } });
  function createAutoBuffController({ actionPlayer, resources, status = { state: 'idle' }, emit = () => {}, buffs = {}, actionFactory, canAct = () => true, enabled = ['bloodRage', 'berserk'] } = {}) {
    if (!actionPlayer || !resources) throw new TypeError('auto buffs require actionPlayer and resources');
    const state = { active: null, buffs: { ...buffs }, durations: {}, cooldowns: {}, status };
    const makeAction = actionFactory || (name => ({ name, phases: [{ name: 'startup', duration: 8 }, { name: 'active', duration: 4 }, { name: 'recovery', duration: 12 }] }));
    function eligible(name) { return !state.active && canAct() && (!state.cooldowns[name] || state.cooldowns[name] <= 0) && resources.mp >= BUFFS[name].cost && !['hitstun', 'knockdown', 'launched', 'getup'].includes(status.state) && actionPlayer.done; }
    function tryCast() {
      for (const name of enabled) if (eligible(name)) {
        resources.mp -= BUFFS[name].cost; state.active = name; actionPlayer.play(makeAction(name)); emit({ type: 'auto-buff-start', name }); return name;
      }
      return null;
    }
    return { get active() { return state.active; }, get buffs() { return state.buffs; }, get cooldowns() { return state.cooldowns; }, status, enterRoom() { tryCast(); }, update(delta = 1) {
      for (const name of Object.keys(state.cooldowns)) state.cooldowns[name] = Math.max(0, state.cooldowns[name] - delta);
      if (state.active && actionPlayer.done) { const name = state.active; state.active = null; state.buffs[name] = true; state.durations[name] = BUFFS[name].duration; state.cooldowns[name] = BUFFS[name].cooldown; emit({ type: 'auto-buff', name }); }
      for (const name of Object.keys(state.durations)) if (state.durations[name] > 0 && (state.durations[name] -= delta) <= 0) { state.durations[name] = 0; state.buffs[name] = false; }
      if (!state.active) tryCast();
    }, tryCast, definitions: BUFFS };
  }
  return { PASSIVE_AUDIT, MASTERY_MAP, effectiveMasteryLevel, getPassiveEffects, createAutoBuffController };
});
