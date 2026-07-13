(function (root, factory) {
  const api = factory(root.DOF70?.combat?.skills?.uppercut);
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function (uppercut) {
  'use strict';
  return { uppercut };
});
