"""Build the DOF70 swordman body and weapon sprite atlases."""

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

try:
    from .dnf_img import parse_img, read_npk
except ImportError:  # pragma: no cover - supports direct script execution
    from dnf_img import parse_img, read_npk


DOF70_IMAGEPACKS2 = (Path("DOF（重生70版本）") / "DOF_src" / "DOF重生" /
                     "客户端" / "ImagePacks2")
WEAPON_NPKS = {
    "lightsword": DOF70_IMAGEPACKS2 / "sprite_character_swordman_equipment_weapon_beamswd.NPK",
    "katana": DOF70_IMAGEPACKS2 / "sprite_character_swordman_equipment_weapon_katana.NPK",
    "greatsword": DOF70_IMAGEPACKS2 / "sprite_character_swordman_equipment_weapon_mswd.NPK",
    "club": DOF70_IMAGEPACKS2 / "sprite_character_swordman_equipment_weapon_club.NPK",
    "shortsword": DOF70_IMAGEPACKS2 / "sprite_character_swordman_equipment_weapon_gemswd.NPK",
}
# Historical names are accepted only as aliases; their canonical mapping is explicit.
WEAPON_ALIASES = {"lswd": "katana", "beamswd": "lightsword"}
SUPPORTED_FORMS = {0x0E, 0x0F, 0x10}


def load(npk, idx=0):
    path = Path(npk)
    if not path.is_file():
        raise FileNotFoundError(f"missing NPK: {path}")
    try:
        entries = read_npk(str(path))
        if not entries:
            raise ValueError(f"empty NPK: {path}")
        if not 0 <= idx < len(entries):
            raise ValueError(f"NPK index out of range: {path} [{idx}]")
        return parse_img(entries[idx][1])["frames"]
    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(f"failed to decompress/decode {path}") from exc


def resolve(frames, index):
    if not 0 <= index < len(frames):
        raise ValueError(f"frame link/index out of range: {index}")
    frame = frames[index]
    if frame["image"] is not None:
        return frame
    link = frame.get("link", -1)
    if not 0 <= link < len(frames):
        raise ValueError(f"frame {index} links out of range: {link}")
    if link == index:
        raise ValueError(f"frame {index} links to itself")
    return resolve(frames, link)


def validate_frames(frames):
    if not frames:
        raise ValueError("empty image atlas")
    visible = False
    for index, frame in enumerate(frames):
        form = frame.get("form")
        if frame["image"] is not None and form not in SUPPORTED_FORMS:
            raise ValueError(f"unknown IMG format at frame {index}: {form!r}")
        resolved = resolve(frames, index)
        if resolved["image"] is not None and resolved["image"].getbbox() is not None:
            visible = True
    if not visible:
        raise ValueError("image atlas contains no visible key frame")


def build_single(frames, output_dir, name, foot_x=0, foot_y=0, scale=1.0):
    validate_frames(frames)
    cells = []
    for index in range(len(frames)):
        frame = resolve(frames, index)
        image = frame["image"]
        if scale != 1.0:
            image = image.resize((max(1, round(frame["w"] * scale)), max(1, round(frame["h"] * scale))))
        if image.getbbox() is not None:
            cells.append((index, image, round((frame["x"] - foot_x) * scale, 1),
                          round((frame["y"] - foot_y) * scale, 1)))

    pad, max_width = 1, 2048
    order = sorted(cells, key=lambda cell: -cell[1].height)
    x = y = row_height = 0
    rects = {}
    for index, image, _, _ in order:
        if x + image.width + pad > max_width and x:
            x, y, row_height = 0, y + row_height, 0
        rects[index] = (x, y, image.width, image.height)
        x += image.width + pad
        row_height = max(row_height, image.height + pad)
    atlas = Image.new("RGBA", (max_width, y + row_height), (0, 0, 0, 0))
    metadata_frames = [None] * len(frames)
    for index, image, ox, oy in order:
        ax, ay, width, height = rects[index]
        atlas.alpha_composite(image, (ax, ay))
        metadata_frames[index] = [ax, ay, width, height, ox, oy]

    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {"count": len(frames), "scale": scale, "frames": metadata_frames}
    atlas.save(output_dir / f"weapon_{name}.png")
    (output_dir / f"weapon_{name}.json").write_text(json.dumps(metadata, separators=(",", ":")))
    return metadata


def build_weapons(output_dir, names=None, source_dir=None):
    source_dir = source_dir or Path(__file__).resolve().parents[3]
    names = list(names or WEAPON_NPKS)
    unknown = set(names) - set(WEAPON_NPKS)
    if unknown:
        raise ValueError(f"unknown weapon type: {sorted(unknown)}")
    result = {}
    for name in names:
        frames = load(source_dir / WEAPON_NPKS[name])
        result[name] = build_single(frames, output_dir, name)
    for alias, canonical in WEAPON_ALIASES.items():
        if canonical in result:
            shutil.copyfile(output_dir / f"weapon_{canonical}.png", output_dir / f"weapon_{alias}.png")
            shutil.copyfile(output_dir / f"weapon_{canonical}.json", output_dir / f"weapon_{alias}.json")
            result[alias] = result[canonical]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "weapons.meta.js").write_text(
        "window.WEAPON_META=" + json.dumps(result, separators=(",", ":")) + ";"
    )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="assets", type=Path)
    parser.add_argument("--source-dir", default=None, type=Path)
    args = parser.parse_args(argv)
    build_weapons(args.output_dir, source_dir=args.source_dir)


if __name__ == "__main__":
    main()
