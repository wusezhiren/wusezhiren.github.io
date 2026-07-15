(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';

  function resolveDamage(input) {
    const options = input || {};
    const channel = options.channel || 'percent';
    let value = Number(options.base) || 0;
    if (channel === 'percent') {
      const level = Number(options.level) || 0;
      const random = typeof options.random === 'function' ? options.random() : Math.random() * 2 - 1;
      value = (value + random * (3 + level * 0.28)) * (1 + (Number(options.physicalPrimaryStat) || 0) / 250);
      const defense = Math.max(Number(options.defense) || 0, 0);
      const denominator = Math.max(defense + 200 * level, 1);
      value *= 1 - defense / denominator;
    }
    if (options.critical) value *= Number(options.criticalMultiplier) || 1.5;
    value *= Number(options.multiplier) || 1;
    const result = value < 0 ? Math.ceil(value) : Math.floor(value);
    return channel === 'percent' ? Math.max(1, result) : result;
  }

  return { resolveDamage };
});
