(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.classes = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';

  const availability = {
    blade: { status: 'available' },
    berserk: { status: 'available' },
    spectre: { status: 'coming-soon', label: '暂未开放' },
    asura: { status: 'coming-soon', label: '暂未开放' },
  };

  function classAvailability(key) {
    return availability[key];
  }

  function canStartClass(key) {
    return classAvailability(key)?.status === 'available';
  }

  return { classAvailability, canStartClass };
});
