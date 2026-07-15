# DOF 70 Blade/Berserker audit matrix

Status: **READY**

| key | level 70 | derivation | SKL | ATK |
|---|---:|---|---|---|
| uppercut | 10 | `min(1+floor((70-1)/3), 50, 10) = 10` | `skill/swordman/upperslash.skl` | `["character/swordman/attackinfo/upperslash.atk","character/swordman/attackinfo/upperslashafter.atk"]` |
| tripleSlash | 30 | `min(1+floor((70-10)/2), 50, 30) = 30` | `skill/swordman/tripleslash.skl` | `["character/swordman/attackinfo/tripleslash1.atk","character/swordman/attackinfo/tripleslash2.atk","character/swordman/attackinfo/tripleslash3.atk","character/swordman/attackinfo/tripleslash3down.atk","character/swordman/attackinfo/tripleslash4.atk","character/swordman/attackinfo/tripleslash5.atk"]` |
| momentarySlash | 18 | `min(1+floor((70-35)/2), 50, 30) = 18` | `skill/swordman/momentaryslash.skl` | `["character/swordman/attackinfo/momentaryslash.atk","character/swordman/attackinfo/momentaryslashex.atk","passiveobject/character/swordman/attackinfo/momentaryslashexwave.atk","passiveobject/character/swordman/attackinfo/momentaryslashwave.atk"]` |
| chargeCrash | 21 | `min(1+floor((70-30)/2), 50, 30) = 21` | `skill/swordman/chargecrash.skl` | `["character/swordman/attackinfo/chargecrashdash.atk","character/swordman/attackinfo/chargecrashexpick.atk","character/swordman/attackinfo/chargecrashexshoulder.atk","character/swordman/attackinfo/chargecrashexupper.atk","character/swordman/attackinfo/chargecrashfinish.atk","character/swordman/attackinfo/chargecrashupper.atk","passiveobject/character/swordman/attackinfo/chargecrashsub.atk"]` |
| rapidMoveSlash | 16 | `min(1+floor((70-40)/2), 50, 30) = 16` | `skill/swordman/rapidmoveslash.skl` | `["character/swordman/attackinfo/rapidmoveslash1.atk","character/swordman/attackinfo/rapidmoveslash2.atk"]` |
| illusionSlash | 13 | `min(1+floor((70-45)/2), 50, 30) = 13` | `skill/swordman/illusionslash.skl` | `["character/swordman/attackinfo/illusionslashsmash.atk","character/swordman/attackinfo/illusionslashupper.atk","passiveobject/character/swordman/attackinfo/illusionslashmelee.atk","passiveobject/character/swordman/attackinfo/illusionslashsub.atk","passiveobject/character/swordman/attackinfo/illusionslashwave.atk","passiveobject/character/swordman/attackinfo/illusionslashwave2.atk","passiveobject/character/swordman/attackinfo/stateoflimitillusionslashwave.atk"]` |
| weaponCombo | 1 | `min(1+floor((70-20)/1), 1, 1) = 1` | `skill/swordman/weaponcombo.skl` | `["character/swordman/attackinfo/weaponcomboblade1.atk","character/swordman/attackinfo/weaponcomboblade2.atk","character/swordman/attackinfo/weaponcomboblade3.atk","character/swordman/attackinfo/weaponcomboblade4.atk","character/swordman/attackinfo/weaponcomboblunt1.atk","character/swordman/attackinfo/weaponcomboblunt2.atk","character/swordman/attackinfo/weaponcomboblunt3.atk","character/swordman/attackinfo/weaponcomboheavy1.atk","character/swordman/attackinfo/weaponcomboheavy2.atk","character/swordman/attackinfo/weaponcombolight1.atk","character/swordman/attackinfo/weaponcombolight2.atk","character/swordman/attackinfo/weaponcombolight3.atk","character/swordman/attackinfo/weaponcomboshort1.atk","character/swordman/attackinfo/weaponcomboshort2.atk","character/swordman/attackinfo/weaponcomboshort3.atk"]` |
| goreCross | 30 | `min(1+floor((70-10)/2), 50, 30) = 30` | `skill/swordman/gorecross.skl` | `["character/swordman/attackinfo/gorecross1.atk","character/swordman/attackinfo/gorecross2.atk","passiveobject/character/swordman/attackinfo/gorecross.atk","passiveobject/character/swordman/attackinfo/gorecrossadd.atk","passiveobject/common/attackinfo/gorecrossattack.atk"]` |
| hopSmash | 28 | `min(1+floor((70-15)/2), 50, 30) = 28` | `skill/swordman/hopsmash.skl` | `["character/swordman/attackinfo/hopsmash.atk","character/swordman/attackinfo/hopsmashfinal.atk","passiveobject/character/swordman/attackinfo/hopsmashsub.atk"]` |
| grabBlastBlood | 23 | `min(1+floor((70-25)/2), 50, 30) = 23` | `skill/swordman/grabblastblood.skl` | `["character/swordman/attackinfo/grabblastblood.atk","character/swordman/attackinfo/grabblastbloodex.atk","passiveobject/character/swordman/attackinfo/grabblastblood.atk","passiveobject/character/swordman/attackinfo/grabblastbloodbig.atk","passiveobject/character/swordman/attackinfo/grabblastbloodex.atk"]` |
| bloodBlast | 21 | `min(1+floor((70-30)/2), 50, 30) = 21` | `skill/swordman/bloodblast.skl` | `["character/swordman/attackinfo/frenzy1.atk","character/swordman/attackinfo/frenzy2.atk","character/swordman/attackinfo/frenzy3.atk","character/swordman/attackinfo/frenzy4.atk"]` |
| bloodyRave | 18 | `min(1+floor((70-35)/2), 50, 30) = 18` | `skill/swordman/bloodyrave.skl` | `["character/swordman/attackinfo/bloodyrave.atk","passiveobject/character/swordman/attackinfo/bloodyrave.atk"]` |
| outrageBreak | 13 | `min(1+floor((70-45)/2), 50, 30) = 13` | `skill/swordman/outragebreak.skl` | `["character/swordman/attackinfo/outragebreak.atk","passiveobject/character/swordman/attackinfo/outragebreakbloodexp.atk","passiveobject/character/swordman/attackinfo/outragebreakfloor.atk"]` |
| weaponMastery | 17 | `min(1+floor((70-20)/3), 50, 20) = 17` | `skill/swordman/weaponmasteryup.skl` | `"not applicable: passive/buff has no ATK"` |
| lightSwordMastery | 1 | `min(1+floor((70-20)/3), 50, 1) = 1` | `skill/swordman/lightswordmastery.skl` | `"not applicable: passive/buff has no ATK"` |
| katanaMastery | 1 | `min(1+floor((70-15)/3), 50, 1) = 1` | `skill/swordman/blademastery.skl` | `"not applicable: passive/buff has no ATK"` |
| greatSwordMastery | 1 | `min(1+floor((70-15)/3), 50, 1) = 1` | `skill/swordman/heavyswordmastery.skl` | `"not applicable: passive/buff has no ATK"` |
| bluntMastery | 1 | `min(1+floor((70-15)/3), 50, 1) = 1` | `skill/swordman/bluntmastery.skl` | `["passiveobject/character/swordman/attackinfo/bluntmasterysub.atk"]` |
| shortSwordMastery | 1 | `min(1+floor((70-15)/3), 50, 1) = 1` | `skill/swordman/shortswordmastery.skl` | `"not applicable: passive/buff has no ATK"` |
| bloodAwakening | 16 | `min(1+floor((70-25)/3), 50, 20) = 16` | `skill/swordman/pinchpowerup.skl` | `"not applicable: passive/buff has no ATK"` |
| bloodRage | 17 | `min(1+floor((70-20)/3), 50, 20) = 17` | `skill/swordman/frenzy.skl` | `["character/swordman/attackinfo/frenzy1.atk","character/swordman/attackinfo/frenzy2.atk","character/swordman/attackinfo/frenzy3.atk","character/swordman/attackinfo/frenzy4.atk"]` |
| reckless | 16 | `min(1+floor((70-25)/3), 50, 20) = 16` | `skill/swordman/reckless.skl` | `"not applicable: passive/buff has no ATK"` |

## Weapon mastery

Effective levels (direct level-17 table consumption, no base +1): `{"shortSword":19,"katana":19,"greatSword":19,"blunt":19,"lightSword":18}`.

## Damage pipeline

Order: `physicalPrimaryPercent -> randomVariance -> physicalDefense -> physicalAbsoluteAttack -> critical -> postDefenseAdjustment -> postMultipliers -> truncateTowardZero`.
Physical defense: `rate=max(D,0)/max(max(D,0)+200*L,1)`.

## Documented limitations
- `binaryFieldNames` (documented limitation): documentation naming only; current runtime interface and formula are fully defined; test: map +0x3f, +0x63, +0x5f and +0x9b to symbols or server protocol fields when available
