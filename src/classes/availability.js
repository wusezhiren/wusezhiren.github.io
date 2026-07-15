(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.classes = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';

  const availability = {
    blade: Object.freeze({ status: 'available' }),
    berserk: Object.freeze({ status: 'available' }),
    spectre: Object.freeze({ status: 'coming-soon', label: '暂未开放' }),
    asura: Object.freeze({ status: 'coming-soon', label: '暂未开放' }),
  };

  function classAvailability(key) {
    return availability[key];
  }

  function canStartClass(key) {
    return classAvailability(key)?.status === 'available';
  }

  return { classAvailability, canStartClass };
});
