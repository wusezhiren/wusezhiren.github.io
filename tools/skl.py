# DNF Script.pvf 技能脚本(.skl)解码器: 还原原版技能数值(MP/冷却/等级/伤害表)。
# 二进制脚本格式: 0xD0B0 魔数 + 5字节单元(1字节类型 + int32 值)。
#   类型 2=int 4=float 5/6/8=字符串表引用 7=文件路径引用
#   9=本地化字符串所在 .str 文件序号(n_string.lst) 10=.str 内键名
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pvf  # noqa: E402

MAGIC = b"\xb0\xd0"


class StringTable:
    def __init__(self, pv):
        raw = pv.read("stringtable.bin")
        self.n = struct.unpack_from("<I", raw, 0)[0]
        self.offs = struct.unpack_from("<%dI" % (self.n + 1), raw, 4)
        self.raw = raw

    def get(self, i):
        if not (0 <= i < self.n):
            return "<bad:%d>" % i
        chunk = self.raw[4 + self.offs[i]: 4 + self.offs[i + 1]]
        for enc in ("cp949", "gbk", "latin1"):
            try:
                return chunk.decode(enc)
            except UnicodeDecodeError:
                continue
        return chunk.decode("latin1", "replace")


def parse_tokens(data, st):
    """解出 (kind, value) 列表; kind∈{'int','float','str','path','strfile','strkey'}"""
    assert data[:2] == MAGIC, "not a pvf script"
    toks = []
    p = 2
    while p + 5 <= len(data):
        t = data[p]
        v = struct.unpack_from("<i", data, p + 1)[0]
        p += 5
        if t == 2:
            toks.append(("int", v))
        elif t == 4:
            toks.append(("float", struct.unpack("<f", struct.pack("<i", v))[0]))
        elif t in (5, 6, 8):
            toks.append(("str", st.get(v)))
        elif t == 7:
            toks.append(("path", st.get(v)))
        elif t == 9:
            toks.append(("strfile", v))
        elif t == 10:
            toks.append(("strkey", st.get(v)))
        else:
            toks.append(("unk%d" % t, v))
    return toks


def _is_tag(tok):
    kind, val = tok
    return kind == "str" and val.startswith("[") and val.endswith("]")


def section_body(toks, tag):
    """取 [tag] 之后的 token: 有 [/tag] 闭合则取到闭合, 否则取到下一个任意标签。"""
    open_tag, close_tag = "[%s]" % tag, "[/%s]" % tag
    for i, tok in enumerate(toks):
        if tok == ("str", open_tag):
            body = []
            for j in range(i + 1, len(toks)):
                if toks[j] == ("str", close_tag):
                    return body
                if _is_tag(toks[j]) and ("str", close_tag) not in toks[j:]:
                    return body
                body.append(toks[j])
            return body
    return []


def ints(toks):
    return [v for k, v in toks if k == "int"]


class SkillReader:
    def __init__(self, pvf_path):
        self.pv = pvf.Pvf(str(pvf_path))
        self.st = StringTable(self.pv)
        self._strfiles = self._load_strfile_index()
        self._strcache = {}

    def _load_strfile_index(self):
        toks = parse_tokens(self.pv.read("n_string.lst"), self.st)
        table = {}
        for i in range(0, len(toks) - 1, 2):
            a, b = toks[i], toks[i + 1]
            if a[0] == "path" and b[0] == "int":
                table[b[1]] = a[1]
            elif a[0] == "int" and b[0] == "path":
                table[a[1]] = b[1]
        return table

    def _strfile(self, idx):
        if idx not in self._strcache:
            path = self._strfiles.get(idx)
            table = {}
            if path:
                raw = self.pv.read(path.lower()) or b""
                for enc in ("big5", "gbk", "cp949"):
                    try:
                        text = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    text = raw.decode("big5", "replace")
                for line in text.splitlines():
                    if ">" in line and not line.startswith("//"):
                        k, _, v = line.partition(">")
                        table[k.strip()] = v.strip()
            self._strcache[idx] = table
        return self._strcache[idx]

    def localized(self, toks, tag):
        """取 [tag] 段里的 (strfile,strkey) 并查 .str 得到本地化文本。"""
        buf = section_body(toks, tag)
        fidx = None
        for kind, val in buf:
            if kind == "strfile":
                fidx = val
            elif kind == "strkey" and fidx is not None:
                return self._strfile(fidx).get(val, val)
        return None

    def read_skill(self, path):
        data = self.pv.read(path)
        if data is None:
            raise FileNotFoundError(path)
        toks = parse_tokens(data, self.st)
        dungeon = section_body(toks, "dungeon")

        def dungeon_first(tag):
            # 部分技能(冰刃/爆炎波动剑等)把 MP/冷却写在顶层而非 [dungeon] 段
            return ints(section_body(dungeon, tag)) or ints(section_body(toks, tag))

        info = {
            "path": path,
            "name": self.localized(toks, "name"),
            "name2": self.localized(toks, "name2"),
            "required_level": (ints(section_body(toks, "required level")) or [None])[0],
            "consume_mp": dungeon_first("consume MP"),
            "cool_time_ms": (dungeon_first("cool time") or [None])[0],
            "casting_time_ms": (dungeon_first("casting time") or [None])[0],
            "static_data": ints(section_body(dungeon, "static data")),
            "maximum_level": (ints(section_body(toks, "maximum level")) or [None])[0],
        }
        li = ints(section_body(dungeon, "level info"))
        if li:
            cols, rows = li[0], li[1:]
            info["level_info_cols"] = cols
            info["level_info"] = [rows[i:i + cols] for i in range(0, len(rows) - cols + 1, cols)]
        else:
            info["level_info_cols"] = 0
            info["level_info"] = []
        return info


if __name__ == "__main__":
    reader = SkillReader(sys.argv[1] if len(sys.argv) > 1 else "地下城与勇士/Script.pvf")
    for p in sys.argv[2:]:
        inf = reader.read_skill(p)
        print(inf["path"], "|", inf["name"], "|", inf["name2"],
              "| reqLv", inf["required_level"], "| MP", inf["consume_mp"],
              "| CD", inf["cool_time_ms"], "| lvcols", inf["level_info_cols"],
              "| lv1", inf["level_info"][0] if inf["level_info"] else None)
