(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.action = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const WEAPONS = ['lightsword', 'katana', 'greatsword', 'club', 'shortsword'];
  const BASIC_ACTIONS = { stand: {}, walk: {}, run: {}, jump_start: {}, airborne: {}, landing: {}, hit_front: {}, hit_back: {}, float: {}, down: {}, get_up: {}, weapons: Object.fromEntries(WEAPONS.map(w => [w, { body: true, weapon: true, shadow: true, anchors: { body: [0, 0], weapon: [1, 0], shadow: [0, 0], effect: [1, 0] } }])) };
  function mirrorAnchors(anchors, direction = 1) {
    const sign = direction < 0 ? -1 : 1;
    return Object.fromEntries(Object.entries(anchors || {}).map(([name, point]) => [name, [point[0] ? point[0] * sign : 0, point[1]]]));
  }
  function weaponAction(weapon = 'lightsword') {
    if (!WEAPONS.includes(weapon)) throw new Error(`Unknown weapon action: ${weapon}`);
    return { ...BASIC_ACTIONS.weapons[weapon], name: `basic_${weapon}`, anchors: mirrorAnchors(BASIC_ACTIONS.weapons[weapon].anchors) };
  }
  function resolveAction(name, timelines) {
    if (name.startsWith('basic_')) return { ...weaponAction(name.slice(6)), phases: [{ name, duration: 160, speedScalable: true }], source: 'basic_weapon' };
    const data = timelines?.basic_actions?.[name];
    if (data?.status === 'failed') throw new Error(`DOF basic action resource failed: ${name}`);
    if (data?.body) {
      const frames = data.body.frames || [];
      const phases = frames.length ? [{ name, duration: frames.reduce((sum, frame) => sum + (frame.delay || 0), 0), speedScalable: false }] : [{ name, duration: data.body.total || 0 }];
      return { ...data, phases, source: 'dof70' };
    }
    return { name, phases: [{ name: 'fallback', duration: 100 }], source: 'fallback' };
  }
  class ActionPlayer {
    constructor({ clock = { hitstop: 0 }, emit } = {}) { this.clock = clock; this.emit = emit || (() => {}); this.direction = 1; this.position = 0; this.inputs = []; this.done = true; this.time = 0; }
    play(action) { this.action = action; this.phases = action.phases || [{ name: 'default', duration: action.duration || 0 }]; this.events = (action.events || []).map((event, i) => ({ ...event, _i: i, fired: false })); this.time = 0; this.position = 0; this.phase = this.phases[0]; this.done = false; return this; }
    update(delta, speed = 1) {
      if (this.done || this.clock.hitstop > 0 || delta <= 0) return this;
      const end = this.phases.reduce((sum, phase) => sum + phase.duration, 0);
      let remaining = delta;
      while (remaining > 0 && !this.done) {
        let elapsed = 0;
        for (const phase of this.phases) {
          if (this.time < elapsed + phase.duration || phase === this.phases[this.phases.length - 1]) {
            if (phase !== this.phase) { this.phase = phase; this.emit({ type: 'phase', name: phase.name }); }
            const rate = phase.speedScalable ? Math.max(0, speed) : 1;
            if (!rate) break;
            const step = Math.min(remaining * rate, Math.max(0, elapsed + phase.duration - this.time));
            this.position += (phase.move || 0) * step * this.direction;
            this.time += step;
            remaining -= step / rate;
            break;
          }
          elapsed += phase.duration;
        }
        if (this.time >= end) this.done = true;
        if (remaining > 0 && this.time >= end) break;
      }
      if (!this.done) {
        let elapsed = 0;
        for (const phase of this.phases) {
          if (this.time < elapsed + phase.duration) {
            if (phase !== this.phase) { this.phase = phase; this.emit({ type: 'phase', name: phase.name }); }
            break;
          }
          elapsed += phase.duration;
        }
      }
      for (const event of this.events) if (!event.fired && event.at <= this.time) { event.fired = true; this.emit(event); }
      return this;
    }
    turn(direction) { if (direction) this.direction = direction < 0 ? -1 : 1; return this.direction; }
    cancel() { if (!this.done && (this.phase.cancelable || this.action.cancelable)) { this.done = true; return true; } return false; }
    buffer(input) { this.inputs.push(input); return this; }
    consumeBuffered() { return this.inputs.shift(); }
  }
  return { ActionPlayer, BASIC_ACTIONS, resolveAction, mirrorAnchors, weaponAction };
});
