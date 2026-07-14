(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.save = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';
  const SAVE_SCHEMA_VERSION = 2;
  const equipment = (typeof require === 'function') ? require('../equipment/weapons.js') : globalThis.DOF70.equipment;

  function migrateSave(input) {
    const save = JSON.parse(JSON.stringify(input || {}));
    const notices = [];
    const run = save.run;
    if (run) {
      const normalize = item => item ? equipment.normalizeWeapon(item, run.clsKey, text => notices.push(text)) : null;
      if (run.equipped) {
        run.equipped = { ...run.equipped, weapon: normalize(run.equipped.weapon) };
        if (run.equipped.weapon && !equipment.canUseWeapon(run.clsKey, run.equipped.weapon.weaponType)) {
          run.equipped.weapon = null;
          notices.push('武器不符合当前职业限制，已卸下');
        }
      }
      if (Array.isArray(run.inventory)) run.inventory = run.inventory.map(item => item?.type === 'weapon' ? normalize(item) : item)
        .filter(item => !item?.weaponType || equipment.canUseWeapon(run.clsKey, item.weaponType) || (notices.push('武器不符合当前职业限制，已移出背包'), false));
    }
    save.schemaVersion = Math.max(save.schemaVersion || 0, SAVE_SCHEMA_VERSION);
    return { save, notices };
  }
  return { SAVE_SCHEMA_VERSION, migrateSave };
});
