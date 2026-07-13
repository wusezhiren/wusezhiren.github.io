import struct
from pathlib import Path

from . import pvf
from .skl import MAGIC, StringTable


DEFAULT_SCHEMA = {
    "attack type": {"physic"},
    "weapon damage apply": set(),
    "attack enemy": set(),
    "elemental property": {"no element"},
    "damage reaction": {"damage", "down"},
    "push aside": set(),
    "lift up": set(),
    "attack direction": {"hit lift up", "hit down"},
    "knuck back": set(),
    "hit info": {"blow", "no blood"},
    "hit wav": set(),
}


def parse_raw_tokens(data, string_table):
    if data[:2] != MAGIC:
        raise ValueError("not a pvf script")
    tokens = []
    for offset in range(2, len(data) - 4, 5):
        raw_type = data[offset]
        raw_value = struct.unpack_from("<i", data, offset + 1)[0]
        if raw_type == 2:
            kind, value = "int", raw_value
        elif raw_type == 4:
            kind = "float"
            value = struct.unpack("<f", struct.pack("<i", raw_value))[0]
        elif raw_type in (5, 6, 8):
            kind, value = "str", string_table.get(raw_value)
        elif raw_type == 7:
            kind, value = "path", string_table.get(raw_value)
        elif raw_type == 9:
            kind, value = "strfile", raw_value
        elif raw_type == 10:
            kind, value = "strkey", string_table.get(raw_value)
        else:
            kind, value = "unk%d" % raw_type, raw_value
        tokens.append({
            "raw_type": raw_type,
            "raw_value": raw_value,
            "kind": kind,
            "value": value,
            "offset": offset,
        })
    return tokens


def _tag_name(token):
    value = token["value"]
    if token["kind"] == "str" and value.startswith("[") and value.endswith("]"):
        return value[1:-1]
    return None


def analyze_tokens(tokens, schema):
    sections = []
    ambiguous = []
    current = None
    run = None

    def ambiguity(token):
        nonlocal run
        if run is None:
            run = {
                "tokens": [],
                "candidate_boundaries": [],
                "reason": "bracketed token is not declared by the ATK schema",
            }
            ambiguous.append(run)
        run["tokens"].append(token)
        if _tag_name(token) is not None:
            run["candidate_boundaries"].append(token["offset"])

    for token in tokens:
        name = _tag_name(token)
        if name in schema:
            run = None
            current = {"name": name, "tokens": []}
            sections.append(current)
        elif current is not None and name in schema[current["name"]]:
            current["tokens"].append(token)
        elif name is not None:
            current = None
            ambiguity(token)
        elif run is not None:
            ambiguity(token)
        elif current is not None:
            current["tokens"].append(token)
        else:
            ambiguity(token)

    index = {}
    for section in sections:
        index.setdefault(section["name"], []).append(section["tokens"])
    return {
        "confirmed_sections": sections,
        "section_index": index,
        "ambiguous_runs": ambiguous,
    }


def _pairs(tokens):
    return [(token["kind"], token["value"]) for token in tokens]


class AttackReader:
    def __init__(self, pvf_path, schema=None):
        self.pvf_path = str(Path(pvf_path).resolve())
        self.pv = pvf.Pvf(self.pvf_path)
        self.st = StringTable(self.pv)
        self.schema = schema if schema is not None else DEFAULT_SCHEMA

    def read_attack(self, path):
        data = self.pv.read(path)
        if data is None:
            raise FileNotFoundError(path)
        tokens = parse_raw_tokens(data, self.st)
        analyzed = analyze_tokens(tokens, self.schema)
        section_index = {
            name: [_pairs(value) for value in values]
            for name, values in analyzed["section_index"].items()
        }

        def first(name):
            values = section_index.get(name, [])
            return values[0] if values else []

        confirmed = [
            {"name": section["name"], "tokens": _pairs(section["tokens"])}
            for section in analyzed["confirmed_sections"]
        ]
        return {
            "path": path,
            "tokens": tokens,
            "sections": confirmed,
            "raw_sections": confirmed,
            "confirmed_sections": confirmed,
            "section_index": section_index,
            "ambiguous_runs": analyzed["ambiguous_runs"],
            "attack_type": first("attack type"),
            "weapon_damage_apply": first("weapon damage apply"),
            "attack_enemy": first("attack enemy"),
            "elemental_property": first("elemental property"),
            "damage_reaction": first("damage reaction"),
            "attack_direction": first("attack direction"),
        }
