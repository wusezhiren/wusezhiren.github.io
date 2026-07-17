(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.status = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const TIMER_NAMES = ['invincible', 'hitImmunity', 'superArmor', 'hitstun', 'knockdown', 'getup', 'grab', 'ungrabbable'];
  function createStatus() {
    const timers = Object.fromEntries(TIMER_NAMES.map(name => [name, 0]));
    return { state: 'idle', timers, held: null, suction: { target: null, time: 0 }, hits: new Map() };
  }
  function setTimer(s, name, value) { if (!(name in s.timers)) throw new Error(`Unknown status timer: ${name}`); s.timers[name] = Math.max(s.timers[name], value || 0); return s; }
  function clearTimer(s, name) { if (!(name in s.timers)) throw new Error(`Unknown status timer: ${name}`); s.timers[name] = 0; return s; }
  function tick(s, amount = 1) {
    amount = Math.max(0, amount);
    for (const name of TIMER_NAMES) s.timers[name] = Math.max(0, s.timers[name] - amount);
    if (s.suction.time > 0) { s.suction.time = Math.max(0, s.suction.time - amount); if (!s.suction.time) s.suction.target = null; }
    tickHits(s, amount);
    if (s.timers.grab <= 0) s.held = null;
    if (s.state === 'hitstun' && !s.timers.hitstun) s.state = 'idle';
    if (s.state === 'launched' && !s.timers.hitstun) s.state = 'idle';
    if (s.state === 'knockdown' && !s.timers.knockdown) s.state = 'getup', setTimer(s, 'getup', 1);
    else if (s.state === 'getup' && !s.timers.getup) s.state = 'idle';
    return s;
  }
  function canHit(s) { return !s.timers.invincible && !s.timers.hitImmunity; }
  function hasSuperArmor(s) { return !!s.timers.superArmor; }
  function applyHitstun(s, duration) { if (!hasSuperArmor(s)) { s.state = 'hitstun'; setTimer(s, 'hitstun', duration); } return s; }
  function launch(s, duration = 1) { s.state = 'launched'; setTimer(s, 'hitstun', duration); return s; }
  function land(s) { if (s.state === 'launched' || s.state === 'float') s.state = 'knockdown', setTimer(s, 'knockdown', 24); return s; }
  function grab(s, target, duration = 1) { if (s.timers.ungrabbable) return false; s.held = target; setTimer(s, 'grab', duration); return true; }
  function isHolding(s, target) { return s.held === target && !!s.timers.grab; }
  function isUngrabbable(s) { return !!s.timers.ungrabbable; }
  function suction(s, target, duration = 1) { s.suction = { target, time: duration }; return s; }
  function canHitTarget(s, target) { return !s.hits.has(target) || s.hits.get(target) <= 0; }
  function recordHit(s, target, interval) { s.hits.set(target, Math.max(0, interval || 0)); return s; }
  function tickHits(s, amount = 1) { for (const [target, time] of s.hits) s.hits.set(target, Math.max(0, time - amount)); return s; }
  function createClock() { return { hitstop: 0 }; }
  function freeze(clock, duration) { clock.hitstop = Math.max(clock.hitstop || 0, Math.max(0, duration || 0)); return clock; }
  function tickClock(clock, amount = 1) { clock.hitstop = Math.max(0, (clock.hitstop || 0) - amount); return clock; }
  function advanceClock(clock, amount) { return clock.hitstop > 0 ? 0 : amount; }
  return { createStatus, setTimer, clearTimer, tick, canHit, hasSuperArmor, applyHitstun, launch, land, grab, isHolding, isUngrabbable, suction, canHitTarget, recordHit, tickHits, createClock, freeze, tickClock, advanceClock };
});
