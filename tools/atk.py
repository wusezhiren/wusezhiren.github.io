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


def split_sections(tokens):
    sections = []
    current = None
    for token in tokens:
        name = _tag_name(token)
        current_has_plain_value = current is not None and any(
            _tag_name(value) is None for value in current["tokens"]
        )
        if name is not None and (
                name in SECTION_TAGS or current is None or current_has_plain_value):
            current = {"name": name, "tokens": []}
            sections.append(current)
        elif current is None:
            current = {"name": None, "tokens": [token]}
            sections.append(current)
        else:
            current["tokens"].append(token)
    return sections


def index_sections(sections):
    index = {}
    for section in sections:
        if section["name"] is not None:
            index.setdefault(section["name"], []).append(section["tokens"])
    return index


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
        sections = split_sections(tokens)
        raw_sections = [section for section in sections if section["name"] is not None]
        section_index = index_sections(raw_sections)

        def first(name):
            values = section_index.get(name, [])
            return values[0] if values else []

        return {
            "path": path,
            "sections": sections,
            "raw_sections": raw_sections,
            "section_index": section_index,
            "attack_type": first("attack type"),
            "weapon_damage_apply": first("weapon damage apply"),
            "attack_enemy": first("attack enemy"),
            "elemental_property": first("elemental property"),
            "damage_reaction": first("damage reaction"),
            "attack_direction": first("attack direction"),
        }
