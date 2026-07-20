#!/usr/bin/env python3
"""Build browser assets for the Hendon Myre town scene from DOF70 NPKs."""
import json
from pathlib import Path

from PIL import Image

try:
    from .dnf_img import parse_img, read_npk, read_npk_names
except ImportError:
    from dnf_img import parse_img, read_npk, read_npk_names


ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "地下城与勇士" / "ImagePacks2"
OUT = ROOT / "assets"
MAP_NPK = PACKS / "sprite_map_hendonmyre.NPK"
NPC_NPK = PACKS / "sprite_map_npc.NPK"

MAP_SPRITES = {
    "far": (1, 0),
    "mid": (3, 0),
    "ground": (120, 0),
    "treeLarge": (122, 0),
    "treeSmall": (123, 0),
    "forestGate": (113, 0),
}
# 原版赫顿玛尔 NPC 名单(Script.pvf map/hendonmyre/*.map [NPC] 布置 + 各 .npc [field animation]),
# 通过 NPK 内部路径名 sprite/map/npc/<name>.img 定位, 不再硬编码索引。
NPC_SPRITES = {
    "danjin":   "npc_dj1",       # 火罐(西门)
    "poongjin": "npc_pj",        # 风振(西门)
    "rothon":   "npc_rt",        # 诺顿·马西莫格(西门)
    "kiri":     "npc_kr",        # 凯丽·德莱迪(西门)
    "veol":     "veol_caelow",   # 维尔·克鲁(中央大街)
    "glam":     "glam_rinwood",  # 格林·林德(中央大街)
    "grandis":  "npc_gd",        # 歌兰蒂斯·格拉西亚(中央大街)
    "birken":   "npc_bk",        # 博肯(中央大街)
    "albert":   "npc_al",        # 阿尔伯特·伯恩斯坦(中央大街)
    "gsd":      "npc_gsd",       # G.S.D(拍卖场)
    "minet":    "npc_minet",     # 米内特(后巷)
    "shylock":  "npc_gbn",       # 夏洛克·戈林德(后巷)
    "shusia":   "npc_su",        # 索西雅(酒馆)
    "seria":    "npc_se",        # 赛丽亚·克鲁敏(城镇入口)
}


def npc_index_by_name(npk_path):
    lookup = {}
    for index, name, _off, _size in read_npk_names(str(npk_path)):
        lookup[name.lower()] = index
    return {
        key: lookup[f"sprite/map/npc/{img}.img"]
        for key, img in NPC_SPRITES.items()
    }


def resolved_frame(frames, index):
    frame = frames[index]
    seen = set()
    while frame["image"] is None and 0 <= frame.get("link", -1) < len(frames):
        if frame["link"] in seen:
            raise ValueError("cyclic IMG frame link")
        seen.add(frame["link"])
        frame = frames[frame["link"]]
    return frame


def pack(cells, max_width=2048, padding=2):
    positions = {}
    x = y = row_height = 0
    for name, image in sorted(cells.items(), key=lambda item: -item[1].height):
        width = image.width + padding
        height = image.height + padding
        if x and x + width > max_width:
            x = 0
            y += row_height
            row_height = 0
        positions[name] = (x, y, image.width, image.height)
        x += width
        row_height = max(row_height, height)
    atlas = Image.new("RGBA", (max_width, y + row_height), (0, 0, 0, 0))
    for name, image in cells.items():
        px, py, _, _ = positions[name]
        atlas.alpha_composite(image, (px, py))
    return atlas, positions


def main():
    map_entries = dict(read_npk(str(MAP_NPK)))
    npc_entries = dict(read_npk(str(NPC_NPK)))
    cells = {}
    metadata = {"source": "DOF70", "sprites": {}, "npcs": {}}

    for name, (img_index, frame_index) in MAP_SPRITES.items():
        frames = parse_img(map_entries[img_index])["frames"]
        frame = resolved_frame(frames, frame_index)
        cells[name] = frame["image"]

    npc_indexes = npc_index_by_name(NPC_NPK)
    for npc_name, image_index in npc_indexes.items():
        frames = parse_img(npc_entries[image_index])["frames"]
        first = resolved_frame(frames, 0)
        foot_x = first["x"] + first["w"] / 2
        foot_y = first["y"] + first["h"]
        values = {"frameMs": 140, "frames": []}
        for index in range(len(frames)):
            frame = resolved_frame(frames, index)
            key = f"{npc_name}{index}"
            cells[key] = frame["image"]
            values["frames"].append([key, round(frame["x"] - foot_x, 1), round(frame["y"] - foot_y, 1)])
        metadata["npcs"][npc_name] = values

    atlas, positions = pack(cells)
    for name in MAP_SPRITES:
        metadata["sprites"][name] = list(positions[name])
    for npc in metadata["npcs"].values():
        npc["frames"] = [[*positions[key], ox, oy] for key, ox, oy in npc["frames"]]

    OUT.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT / "town_hendonmyre.png", optimize=True)
    payload = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    (OUT / "town_hendonmyre.json").write_text(payload, encoding="utf-8")
    (OUT / "town_hendonmyre.meta.js").write_text("window.TOWN_HENDONMYRE_META=" + payload + ";\n", encoding="utf-8")
    print(f"town_hendonmyre: {atlas.width}x{atlas.height}, {len(cells)} sprites")


if __name__ == "__main__":
    main()
