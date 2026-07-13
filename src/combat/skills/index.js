(function (root, factory) {
  const api = factory(root.DOF70?.combat?.skills?.uppercut, root.DOF70?.combat?.skills?.tripleSlash, root.DOF70?.combat?.skills?.chargeCrash, root.DOF70?.combat?.skills?.momentarySlash);
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function (uppercut, tripleSlash, chargeCrash, momentarySlash) {
  'use strict';
  return { uppercut, tripleSlash, chargeCrash, momentarySlash };
});
