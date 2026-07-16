#!/usr/bin/env python3
"""Build four browser-ready original dungeon environment sets from DOF70 NPKs."""
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
THEMES = {
    "light": "lightcrystal_forest",
    "ice": "icecrystal_forest",
    "red": "redcrystal_forest",
    "dark": "darkrex_darkforest",
}


def frame(pack, image_index, frame_index=0):
    entries = dict(read_npk(str(PACKS / pack)))
    frames = parse_img(entries[image_index])["frames"]
    value = frames[frame_index]
    seen = set()
    while value["image"] is None and 0 <= value.get("link", -1) < len(frames):
        if value["link"] in seen:
            raise ValueError(f"cyclic frame link in {pack}")
        seen.add(value["link"])
        value = frames[value["link"]]
    if value["image"] is None:
        raise ValueError(f"empty frame {pack}[{image_index}:{frame_index}]")
    return value


def pack(cells, max_width=2048, padding=2):
    positions, x, y, row_height = {}, 0, 0, 0
    for key, value in sorted(cells.items(), key=lambda item: -item[1]["image"].height):
        image = value["image"]
        if x and x + image.width + padding > max_width:
            x, y, row_height = 0, y + row_height, 0
        positions[key] = (x, y, image.width, image.height)
        x += image.width + padding
        row_height = max(row_height, image.height + padding)
    atlas = Image.new("RGBA", (max_width, y + row_height), (0, 0, 0, 0))
    for key, value in cells.items():
        atlas.alpha_composite(value["image"], positions[key][:2])
    return atlas, positions


def main():
    cells = {}
    metadata = {"source": "DOF70", "themes": {}}
    for theme, source in THEMES.items():
        base = f"sprite_map_season4_metastasis_abnoba_{source}.NPK"
        tile = f"sprite_map_season4_metastasis_abnoba_{source}_tile.NPK"
        obj = f"sprite_map_season4_metastasis_abnoba_{source}_obj.NPK"
        gate = f"sprite_map_pathgate_season4_abnoba_{source}.NPK"
        specs = {
            "far": (base, 0, 0), "mid": (base, 2, 0), "floor": (tile, 0, 0),
            "tree": (obj, 13, 0), "treeSmall": (obj, 14, 0), "crystal": (obj, 1, 0),
            "statue": (obj, 11, 0), "door": (gate, 12, 0), "doorLight": (gate, 13, 0),
            "bossDoor": (gate, 4, 0), "bossDoorLight": (gate, 5, 0),
        }
        metadata["themes"][theme] = {}
        for name, (pack_name, image_index, frame_index) in specs.items():
            key = f"{theme}_{name}"
            value = frame(pack_name, image_index, frame_index)
            cells[key] = value
            metadata["themes"][theme][name] = {"key": key, "x": value["x"], "y": value["y"], "fw": value["fw"], "fh": value["fh"]}

    atlas, positions = pack(cells)
    for sprites in metadata["themes"].values():
        for sprite in sprites.values():
            sprite["frame"] = list(positions[sprite.pop("key")])
    OUT.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT / "dungeons_original.png", optimize=True)
    payload = json.dumps(metadata, ensure_ascii=False, separators=(",", ":"))
    (OUT / "dungeons_original.json").write_text(payload, encoding="utf-8")
    (OUT / "dungeons_original.meta.js").write_text("window.DUNGEONS_ORIGINAL_META=" + payload + ";\n", encoding="utf-8")
    print(f"dungeons_original: {atlas.width}x{atlas.height}, {len(cells)} sprites")


if __name__ == "__main__":
    main()
