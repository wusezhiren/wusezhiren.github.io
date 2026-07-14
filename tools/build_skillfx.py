"""Build the skill effect atlas from the local DOF 70 client."""
import argparse
import collections
import glob
import json
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from ani70 import parse_ani70
from dnf_img import parse_img, read_npk, read_npk_names
from pvf import Pvf
from skillfx_config import BUILD_SKILL_SPECS, OUT_DIR, PFX, TARGET_CLIPS, is_bad_variant, resolve_source_paths


def build(root=None, output_dir=None, strict_targets=True):
    root = Path(root or Path(__file__).resolve().parents[1]).resolve()
    pvf_path, imagepacks = resolve_source_paths(root)
    if "DOF（重生70版本）" not in str(pvf_path):
        raise FileNotFoundError(f"DOF70 source missing: Script.pvf at {pvf_path}")
    out = Path(output_dir) if output_dir else root / OUT_DIR
    pv = Pvf(str(pvf_path))
    base2loc, path2loc, pack_dirs = collections.defaultdict(list), collections.defaultdict(list), {}
    base_pack = PFX.rstrip("_")

    def index_packs(directory, tag):
        for filename in glob.glob(str(Path(directory) / f"{base_pack}*.NPK")):
            stem = os.path.basename(filename)[len(base_pack):-4].lstrip("_")
            pack_dirs[(tag, stem)] = filename
            for i, name, _, _ in read_npk_names(filename):
                base = name.rsplit("/", 1)[-1].lower()
                if not is_bad_variant(base):
                    base2loc[base].append(((tag, stem), i, name))
                    path2loc[name.lower()].append(((tag, stem), i, name))

    index_packs(imagepacks, "dof")
    # Only non-target legacy clips may use this compatibility index.
    old = root / "地下城与勇士" / "ImagePacks2"
    if old.exists() and old != imagepacks and not strict_targets:
        index_packs(old, "old")
    npk_cache, img_cache, cells = {}, {}, {}

    def load_img(name, prefer):
        base = name.rsplit("/", 1)[-1].lower()
        locs = path2loc.get(name.lower(), []) or base2loc.get(base, [])
        if not locs:
            raise FileNotFoundError(f"unknown IMG {name}")
        if len(locs) > 1:
            parts = name.replace("\\", "/").split("/")
            parent = parts[-2].lower() if len(parts) > 1 else ""
            preferred = [x for x in locs if x[0][0] == "dof" and x[0][1].lower() in (prefer.lower(), parent, "")]
            if len(preferred) != 1:
                raise ValueError(f"ambiguous IMG basename {name}: {len(locs)} candidates")
            locs = preferred
        pack, idx, source = locs[0]
        key = (pack, idx)
        if key not in img_cache:
            npk_cache.setdefault(pack, dict((i, d) for i, d in read_npk(pack_dirs[pack])))
            parsed = parse_img(npk_cache[pack][idx])
            frames = parsed["frames"]
            img_cache[key] = [frames[i] if f.get("image") is not None else frames[f.get("link", i)] for i, f in enumerate(frames)]
        return key, img_cache[key], {"img": source, "npk": pack_dirs[pack]}

    def cell(key, fi, frame):
        ck = (*key, fi)
        cells.setdefault(ck, {"image": frame["image"], "rect": None})
        return ck

    def ani_layer(rel, prefer):
        ani_source = f"character/swordman/effect/animation/{rel}.ani"
        raw = pv.read(ani_source)
        if raw is None:
            raise FileNotFoundError(f"missing ANI {ani_source}")
        # DOF70's effect files use the documented 4-byte kw23 extension.
        ani = parse_ani70(raw, strict=True, extra_kw={23: 4})
        imgs = [load_img(path, prefer) for path in ani["images"]]
        frames = []
        for f in ani["frames"]:
            if f["imgIdx"] < 0:
                frames.append([f["delay"]]); continue
            if f["imgIdx"] >= len(imgs) or f["imgFrame"] >= len(imgs[f["imgIdx"]][1]):
                raise ValueError(f"invalid frame reference in {ani_source}")
            key, image_frames, source = imgs[f["imgIdx"]]
            fr = image_frames[f["imgFrame"]]
            if fr["image"] is None:
                frames.append([f["delay"]]); continue
            rate = f["attrs"].get(7, [(1.0, 1.0)])[-1]
            rgba = f["attrs"].get(9, [-1])[-1]
            frames.append([cell(key, f["imgFrame"], fr), f["x"] + fr["x"], f["y"] + fr["y"], f["delay"], round(rate[0]*100), round(rate[1]*100), ((rgba >> 24) & 255) if rgba != -1 else 255])
        if not any(len(f) > 1 for f in frames):
            raise ValueError(f"empty ANI layer {ani_source}")
        source = {"ani": ani_source, "imgs": [x[2]["img"] for x in imgs], "npks": [x[2]["npk"] for x in imgs]}
        return {"loop": 1 if ani["gattrs"].get(0) else 0, "frames": frames, "source": source}

    def image_layer(name, spec):
        key, image_frames, source = load_img(name, spec.prefer_npk)
        frames = [[cell(key, i, fr), fr["x"], fr["y"], max(30, round(1000/spec.fps)), 100, 100, 255] for i, fr in enumerate(image_frames) if fr["image"] is not None]
        if not frames:
            raise ValueError(f"empty IMG layer {name}")
        return {"loop": 1 if spec.loop_images else 0, "frames": frames, "source": {"ani": None, "imgs": [source["img"]], "npks": [source["npk"]]}}

    clips = {}
    for name, spec in BUILD_SKILL_SPECS.items():
        target = name in TARGET_CLIPS
        layers = []
        for loader, value in [(ani_layer, a) for a in spec.anis] + [(image_layer, i) for i in spec.images]:
            try:
                layers.append(loader(value, spec.prefer_npk) if loader is ani_layer else loader(value, spec))
            except (FileNotFoundError, ValueError, KeyError):
                if target:
                    raise
        if not layers:
            if target:
                raise ValueError(f"missing all layers for target {name}")
            continue
        clips[name] = {"layers": layers, "source": {"client": "DOF70", "npk": spec.prefer_npk}, "dur": max(sum(f[0] if len(f) == 1 else f[3] for f in l["frames"]) for l in layers)}
    if not cells:
        raise ValueError("no skill effect frames loaded")
    pad, maxw, x, y, rowh = 1, 2048, 0, 0, 0
    for key in sorted(cells, key=lambda k: -cells[k]["image"].height):
        im = cells[key]["image"]
        if x + im.width + pad > maxw: x, y, rowh = 0, y + rowh, 0
        cells[key]["rect"] = (x, y, im.width, im.height); x += im.width + pad; rowh = max(rowh, im.height + pad)
    atlas = Image.new("RGBA", (maxw, y + rowh), (0, 0, 0, 0))
    for item in cells.values(): atlas.alpha_composite(item["image"], item["rect"][:2])
    data = {"v": 3, "clips": {}}
    for name, clip in clips.items():
        layers = []
        for layer in clip["layers"]:
            frames = []
            for frame in layer["frames"]:
                if len(frame) == 1: frames.append(frame); continue
                sx, sy, sw, sh = cells[frame[0]]["rect"]; frames.append([sx, sy, sw, sh, *frame[1:]])
            layers.append({"loop": layer["loop"], "frames": frames, "source": layer["source"]})
        data["clips"][name] = {"dur": clip["dur"], "layers": layers, "source": clip["source"]}
    out.mkdir(parents=True, exist_ok=True); atlas.save(out / "skillfx.png")
    text = json.dumps(data, separators=(",", ":")); (out / "skillfx.json").write_text(text, encoding="utf-8"); (out / "skillfx.meta.js").write_text("window.SKILLFX_META=" + text + ";", encoding="utf-8")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path); parser.add_argument("--allow-legacy", action="store_true")
    args = parser.parse_args()
    build(output_dir=args.output, strict_targets=not args.allow_legacy)
