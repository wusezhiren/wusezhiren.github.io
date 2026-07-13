(function (root, factory) {
  const api = factory();
  root.DOF70 = root.DOF70 || {};
  root.DOF70.equipment = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(globalThis, function () {
  'use strict';

  const WEAPON_TYPES = Object.freeze({
    lightsword: Object.freeze({ weaponType: 'lightsword', name: '光剑', level: 70, physicalAttack: 612, attackSpeed: 1.15, classRestrictions: Object.freeze(['blade']) }),
    katana: Object.freeze({ weaponType: 'katana', name: '太刀', level: 70, physicalAttack: 645, attackSpeed: 1.1, classRestrictions: Object.freeze(['blade', 'berserk']) }),
    greatsword: Object.freeze({ weaponType: 'greatsword', name: '巨剑', level: 70, physicalAttack: 790, attackSpeed: 0.85, classRestrictions: Object.freeze(['blade', 'berserk']) }),
    club: Object.freeze({ weaponType: 'club', name: '钝器', level: 70, physicalAttack: 735, attackSpeed: 0.92, classRestrictions: Object.freeze(['blade', 'berserk']) }),
    shortsword: Object.freeze({ weaponType: 'shortsword', name: '短剑', level: 70, physicalAttack: 680, attackSpeed: 1.02, classRestrictions: Object.freeze(['blade', 'berserk']) }),
  });
  const DEFAULT_WEAPON = Object.freeze({ blade: 'lightsword', berserk: 'katana' });

  function canUseWeapon(clsKey, weaponType) {
    return !!WEAPON_TYPES[weaponType]?.classRestrictions.includes(clsKey);
  }

  function normalizeWeapon(input, clsKey, notice) {
    const item = input && typeof input === 'object' ? { ...input } : {};
    const requested = item.weaponType || (item.type === 'weapon' ? DEFAULT_WEAPON[clsKey] : null);
    const weaponType = WEAPON_TYPES[requested] ? requested : (DEFAULT_WEAPON[clsKey] || 'katana');
    if (requested && requested !== weaponType && notice) notice(`未知武器类型 ${requested}，已回退为${WEAPON_TYPES[weaponType].name}`);
    const base = WEAPON_TYPES[weaponType];
    return { ...item, kind: 'equip', type: 'weapon', weaponType, level: base.level,
      physicalAttack: base.physicalAttack, attackSpeed: base.attackSpeed,
      classRestrictions: [...base.classRestrictions], name: item.name || base.name,
      stats: { ...(item.stats || {}), atk: item.stats?.atk ?? base.physicalAttack } };
  }

  return { WEAPON_TYPES, DEFAULT_WEAPON, canUseWeapon, normalizeWeapon };
});
