from dataclasses import dataclass


@dataclass(frozen=True)
class AuditSpec:
    key: str
    skl_name: str
    growtype: int
    body: tuple = ()
    effect: tuple = ()


SKILL_SPECS = {
    "uppercut": AuditSpec("uppercut", "upperslash", 0, ("upperslashafter",), ("upperslash1", "upperslash2")),
    "tripleSlash": AuditSpec("tripleSlash", "tripleslash", 1, ("tripleslash1", "tripleslash2", "tripleslash3"), ("tripleslash/slash1", "tripleslash/slash2", "tripleslash/slash3", "tripleslash/slash4", "tripleslash/slash5", "tripleslash/move1", "tripleslash/move2")),
    "momentarySlash": AuditSpec("momentarySlash", "momentaryslash", 1, ("momentaryslash",), ("momentaryslash", "momentaryslash/charge1", "momentaryslash/charge2", "momentaryslash/momentaryslash_none_under", "momentaryslash/momentaryslash_none_upper")),
    "chargeCrash": AuditSpec("chargeCrash", "chargecrash", 1, ("chargecrashupper",), ("chargecrash/charge", "chargecrash/dash", "chargecrash/up-slash", "chargecrash/dustdash", "chargecrash/dustdashlast")),
    "rapidMoveSlash": AuditSpec("rapidMoveSlash", "rapidmoveslash", 1, ("rapidmoveslashready1", "rapidmoveslashmove1", "rapidmoveslashready2", "rapidmoveslashmove2"), ("rapidmoveslash/move1", "rapidmoveslash/move2", "rapidmoveslash/slash1", "rapidmoveslash/slash2", "rapidmoveslash/dust")),
    "illusionSlash": AuditSpec("illusionSlash", "illusionslash", 1, ("illusionslash1", "illusionslash2", "illusionslash3", "illusionslash4", "illusionslashfinal"), ("illusionslash/upper", "illusionslash/smash")),
    "weaponCombo": AuditSpec("weaponCombo", "weaponcombo", 1, ("weaponcomboblade1", "weaponcomboblade2", "weaponcomboblade3", "weaponcomboblade4"), ("weaponcombo/light", "weaponcombo/blade")),
    "goreCross": AuditSpec("goreCross", "gorecross", 3, ("gorecross",), ("gorecross/slash1", "gorecross/slash2", "gorecross/slash3", "gorecross/slash4")),
    "hopSmash": AuditSpec("hopSmash", "hopsmash", 3, ("hopsmashready", "hopsmash"), ("hopsmash/smash", "hopsmash/sword")),
    "grabBlastBlood": AuditSpec("grabBlastBlood", "grabblastblood", 3, ("grab",), ("grabblastblood",)),
    "bloodBlast": AuditSpec("bloodBlast", "bloodblast", 3, ("frenzy1", "frenzy2", "frenzy3", "frenzy4"), ("frenzy/cast", "frenzy/blast", "frenzy/buff", "frenzy/createball", "frenzy/ball", "frenzy/sword1-1", "frenzy/sword1-3", "frenzy/sword1-4")),
    "bloodyRave": AuditSpec("bloodyRave", "bloodyrave", 3, ("bloodyraveinhale", "bloodyraveslash"), ("bloodyrave/start1", "bloodyrave/start2", "bloodyrave/loop1", "bloodyrave/loop2", "bloodyrave/line1", "bloodyrave/line2", "bloodyrave/sword1", "bloodyrave/sword3", "bloodyrave/sword4", "bloodyrave/typhoon", "bloodyrave/end")),
    "outrageBreak": AuditSpec("outrageBreak", "outragebreak", 3, ("outragebreakready", "outragebreakslash"), ("outragebreak/sword_ready_none", "outragebreak/sword_slash_none", "outragebreak/sword_slash_impact_none", "outragebreak/sword_slash_stone")),
}

PASSIVE_SPECS = {
    "weaponMastery": AuditSpec("weaponMastery", "weaponmasteryup", 1),
    "lightSwordMastery": AuditSpec("lightSwordMastery", "lightswordmastery", 1),
    "katanaMastery": AuditSpec("katanaMastery", "blademastery", 1),
    "greatSwordMastery": AuditSpec("greatSwordMastery", "heavyswordmastery", 1),
    "bluntMastery": AuditSpec("bluntMastery", "bluntmastery", 1),
    "shortSwordMastery": AuditSpec("shortSwordMastery", "shortswordmastery", 1),
    "bloodAwakening": AuditSpec("bloodAwakening", "pinchpowerup", 3),
    "bloodRage": AuditSpec("bloodRage", "frenzy", 3),
    "reckless": AuditSpec("reckless", "reckless", 3),
}
