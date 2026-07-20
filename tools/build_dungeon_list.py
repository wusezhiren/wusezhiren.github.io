#!/usr/bin/env python3
"""从 DOF70 Script.pvf 提取原版副本权威清单 → assets/dungeon_list.json。

dungeon/dungeon.lst 给出 副本id → .dgn 路径;每个 .dgn 里:
  [name]                    副本名(字符串表 Big5)
  [minimum required level]  进入等级
  [basis level]             标准(怪物)等级
  [maze info]/[size]        迷宫 宽×高(格子数≈房间数上限)
  [maze info]/[greed]       房间布局字母图(每格2字母, 去重后=实际房间数)
  [monster]                 出场怪物(路径引用, 需再解 .aic/.ani 才有名字, 这里只留路径)
本客户端字符串表为 Big5(繁体), StringTable 默认 cp949 会得到乱码, 这里强制 Big5。
"""
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pvf  # noqa: E402
import skl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PVF_PATH = ROOT / "DOF（重生70版本）/DOF_src/DOF重生/客户端/Script.pvf"
OUT = ROOT / "assets/dungeon_list.json"

try:
    from opencc import OpenCC  # type: ignore
    _cc = OpenCC("t2s")
except ImportError:
    _cc = None


class Big5StringTable(skl.StringTable):
    def get(self, i):
        if not (0 <= i < self.n):
            return "<bad:%d>" % i
        chunk = self.raw[4 + self.offs[i]: 4 + self.offs[i + 1]]
        for enc in ("big5", "gbk", "latin1"):
            try:
                return chunk.decode(enc)
            except UnicodeDecodeError:
                continue
        return chunk.decode("latin1", "replace")


def t2s(text):
    return _cc.convert(text) if (_cc and isinstance(text, str)) else text


def room_count(greed):
    """greed 是形如 'JJEE\r\n LLMM\r\n DDGG' 的布局图, 每格两个相同字母。"""
    letters = set(re.findall(r"[A-Za-z]", greed or ""))
    return len(letters) or None


def main():
    pv = pvf.Pvf(str(PVF_PATH))
    st = Big5StringTable(pv)
    lst = skl.parse_tokens(pv.read("dungeon/dungeon.lst"), st)
    pairs = []
    for i in range(0, len(lst) - 1, 2):
        a, b = lst[i], lst[i + 1]
        if a[0] == "int" and b[0] == "path":
            pairs.append((a[1], b[1]))

    dungeons = []
    for did, rel in pairs:
        path = ("dungeon/" + rel).lower()
        data = pv.read(path)
        if data is None:
            dungeons.append({"id": did, "path": rel, "missing": True})
            continue
        toks = skl.parse_tokens(data, st)

        def first(tag, kind="int"):
            for k, v in skl.section_body(toks, tag):
                if k == kind:
                    return v
            return None

        name = None
        for j, tok in enumerate(toks):
            if tok == ("str", "[name]") and j + 1 < len(toks):
                name = toks[j + 1][1]
                break
        size = skl.ints(skl.section_body(toks, "size"))
        greed = first("greed", "path")
        dungeons.append({
            "id": did,
            "path": rel,
            "act": rel.split("/")[0],
            "name": name,
            "name_sc": t2s(name),
            "minLevel": first("minimum required level"),
            "basisLevel": first("basis level"),
            "mazeSize": size[:2] if size else None,
            "rooms": room_count(greed),
        })

    OUT.write_text(json.dumps({"source": "DOF70 Script.pvf",
                               "count": len(dungeons),
                               "dungeons": dungeons},
                              ensure_ascii=False, indent=1), "utf-8")
    print("写出", OUT, "共", len(dungeons), "个副本")
    for d in dungeons:
        if d.get("missing"):
            print("  [缺失]", d["id"], d["path"])
            continue
        print("  %3d %-40s %-14s Lv%-3s 房%-3s %s" % (
            d["id"], d["path"], d["act"],
            d["minLevel"], d["rooms"], d["name_sc"] or d["name"]))


if __name__ == "__main__":
    main()
