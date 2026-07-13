(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.monsters = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';

  const MONSTERS_DOF70 = Object.freeze({
    normal: Object.freeze({ level: 70, hp: 1200, defense: 180, staggerResistance: 0.1, floatResistance: 0.1, grabResistance: 0.1 }),
    elite: Object.freeze({ level: 70, hp: 3000, defense: 300, staggerResistance: 0.35, floatResistance: 0.35, grabResistance: 0.3 }),
    boss: Object.freeze({ level: 70, hp: 12000, defense: 520, staggerResistance: 0.65, floatResistance: 0.7, grabResistance: 0.6 }),
  });

  function createMonster(kind = 'normal') {
    return { ...(MONSTERS_DOF70[kind] || MONSTERS_DOF70.normal) };
  }

  return { MONSTERS_DOF70, createMonster };
});
