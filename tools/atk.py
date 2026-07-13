from pathlib import Path

from . import pvf
from .skl import StringTable, parse_tokens


SECTION_TAGS = {
    "attack type",
    "weapon damage apply",
    "attack enemy",
    "elemental property",
    "damage reaction",
    "push aside",
    "lift up",
    "attack direction",
    "knuck back",
    "hit info",
    "hit wav",
}


def _tag_name(token):
    kind, value = token
    if kind == "str" and value.startswith("[") and value.endswith("]"):
        return value[1:-1]
    return None


class AttackReader:
    def __init__(self, pvf_path):
        self.pvf_path = str(Path(pvf_path).resolve())
        self.pv = pvf.Pvf(self.pvf_path)
        self.st = StringTable(self.pv)

    def read_attack(self, path):
        data = self.pv.read(path)
        if data is None:
            raise FileNotFoundError(path)
        tokens = parse_tokens(data, self.st)
        sections = []
        current = None
        for token in tokens:
            name = _tag_name(token)
            if name in SECTION_TAGS:
                current = {"name": name, "tokens": []}
                sections.append(current)
            elif current is None:
                sections.append({"name": None, "tokens": [token]})
                current = sections[-1]
            else:
                current["tokens"].append(token)

        raw_sections = {
            section["name"]: section["tokens"]
            for section in sections if section["name"] is not None
        }
        return {
            "path": path,
            "sections": sections,
            "raw_sections": raw_sections,
            "attack_type": raw_sections.get("attack type", []),
            "weapon_damage_apply": raw_sections.get("weapon damage apply", []),
            "attack_enemy": raw_sections.get("attack enemy", []),
            "elemental_property": raw_sections.get("elemental property", []),
            "damage_reaction": raw_sections.get("damage reaction", []),
            "attack_direction": raw_sections.get("attack direction", []),
        }
