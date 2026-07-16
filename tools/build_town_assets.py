#!/usr/bin/env python3
"""Build browser assets for the Hendon Myre town scene from DOF70 NPKs."""
import json
from pathlib import Path

from PIL import Image

try:
    from .dnf_img import parse_img, read_npk
except ImportError:
    from dnf_img import parse_img, read_npk


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
    metadata = {"source": "DOF70", "sprites": {}, "linus": {"frameMs": 140, "frames": []}}

    for name, (img_index, frame_index) in MAP_SPRITES.items():
        frames = parse_img(map_entries[img_index])["frames"]
        frame = resolved_frame(frames, frame_index)
        cells[name] = frame["image"]

    linus_frames = parse_img(npc_entries[267])["frames"]
    first = resolved_frame(linus_frames, 0)
    foot_x = first["x"] + first["w"] / 2
    foot_y = first["y"] + first["h"]
    linus_offsets = []
    for index in range(len(linus_frames)):
        frame = resolved_frame(linus_frames, index)
        key = f"linus{index}"
        cells[key] = frame["image"]
        linus_offsets.append((key, round(frame["x"] - foot_x, 1), round(frame["y"] - foot_y, 1)))

    atlas, positions = pack(cells)
    for name in MAP_SPRITES:
        metadata["sprites"][name] = list(positions[name])
    for key, ox, oy in linus_offsets:
        metadata["linus"]["frames"].append([*positions[key], ox, oy])

    OUT.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT / "town_hendonmyre.png", optimize=True)
    payload = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    (OUT / "town_hendonmyre.json").write_text(payload, encoding="utf-8")
    (OUT / "town_hendonmyre.meta.js").write_text("window.TOWN_HENDONMYRE_META=" + payload + ";\n", encoding="utf-8")
    print(f"town_hendonmyre: {atlas.width}x{atlas.height}, {len(cells)} sprites")


if __name__ == "__main__":
    main()
