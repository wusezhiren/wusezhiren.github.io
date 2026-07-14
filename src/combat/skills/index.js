(function (root, factory) {
  const api = factory(root.DOF70?.combat?.skills?.uppercut, root.DOF70?.combat?.skills?.tripleSlash, root.DOF70?.combat?.skills?.chargeCrash, root.DOF70?.combat?.skills?.momentarySlash, root.DOF70?.combat?.skills?.rapidMoveSlash, root.DOF70?.combat?.skills?.weaponCombo, root.DOF70?.combat?.skills?.illusionSlash, root.DOF70?.combat?.skills?.goreCross, root.DOF70?.combat?.skills?.hopSmash, root.DOF70?.combat?.skills?.bloodBlast);
  root.DOF70 = root.DOF70 || {};
  root.DOF70.combat = root.DOF70.combat || {};
  root.DOF70.combat.skills = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function (uppercut, tripleSlash, chargeCrash, momentarySlash, rapidMoveSlash, weaponCombo, illusionSlash, goreCross, hopSmash, bloodBlast) {
  'use strict';
  return { uppercut, tripleSlash, chargeCrash, momentarySlash, rapidMoveSlash, weaponCombo, illusionSlash, goreCross, hopSmash, bloodBlast };
});
