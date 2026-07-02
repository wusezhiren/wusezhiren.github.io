# Rebuilds DNF/DOF swordman skill effects into assets/skillfx.png + metadata.
# Layered clips preserve .ani anchors/fps; image-only clips keep native .img offsets.
import collections
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ani import parse_ani
from dnf_img import parse_img, read_npk, read_npk_names
from pvf import Pvf
from skillfx_config import BUILD_SKILL_SPECS, OUT_DIR, PFX, is_bad_variant, resolve_source_paths
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PVF_PATH, IMAGEPACKS = resolve_source_paths(ROOT)
OUT = ROOT / OUT_DIR
pv = Pvf(str(PVF_PATH))

print(f"使用PVF: {PVF_PATH}")
print(f"使用ImagePacks2: {IMAGEPACKS}")

# basename -> [(npkstem, img_index, img_name)] across all swordman effect NPKs.
print("建立全局img索引...")
base2loc = collections.defaultdict(list)
for f in glob.glob(str(IMAGEPACKS / f"{PFX}*.NPK")):
    stem = os.path.basename(f)[len(PFX) : -4]
    try:
        for i, name, _, _ in read_npk_names(f):
            base = name.split("/")[-1].lower()
            if is_bad_variant(base):
                continue
            base2loc[base].append((stem, i, name))
    except Exception as ex:
        print(f"  [索引失败] {f}: {ex}")

_npk_cache = {}


def npk_data(stem):
    if stem not in _npk_cache:
        path = IMAGEPACKS / f"{PFX}{stem}.NPK"
        _npk_cache[stem] = dict((i, d) for i, d in read_npk(str(path)))
    return _npk_cache[stem]


def load_frames(basename, prefer_npk=None, maxf=None):
    """Return parsed image frames, preferring the requested NPK and preserving frames by default."""
    bn = basename.split("/")[-1].lower()
    locs = base2loc.get(bn, [])
    if not locs:
        return None
    locs = sorted(locs, key=lambda l: (l[0] != prefer_npk, l[0], l[1]))
    stem, idx, resolved_name = locs[0]
    data = npk_data(stem)[idx]
    parsed = parse_img(data)
    frames = parsed["frames"]

    def res(i):
        frame = frames[i]
        if frame["image"] is None and 0 <= frame.get("link", -1) < len(frames):
            return frames[frame["link"]]
        return frame

    valid = [i for i in range(len(frames)) if res(i)["image"] is not None]
    if maxf and len(valid) > maxf:
        step = len(valid) / maxf
        valid = [valid[int(k * step)] for k in range(maxf)]
    picked = [res(i) for i in valid]
    print(f"    [img] {basename} -> {stem}:{idx} {resolved_name} frames={len(picked)}")
    return picked


def ani_layer(folder, name, prefer_npk, maxf=None):
    pvf_name = f"character/swordman/effect/animation/{folder}/{name}.ani"
    raw = pv.read(pvf_name)
    if raw is None:
        return None
    ani = parse_ani(raw)
    if not ani or not ani["images"]:
        return None
    img = ani["images"][0].split("/")[-1]
    frames = load_frames(img, prefer_npk, maxf=maxf)
    if not frames:
        return None
    fps = max(8, round(1000.0 / max(20, ani["delay"])))
    return {"frames": frames, "ax": ani["posX"], "ay": ani["posY"], "fps": fps, "src": pvf_name}


def single_layer(basename, prefer_npk, fps=16, maxf=None):
    frames = load_frames(basename, prefer_npk, maxf=maxf)
    if not frames:
        return None
    return {"frames": frames, "ax": 0, "ay": 0, "fps": fps, "src": basename}


clips = {}
for clip, spec in BUILD_SKILL_SPECS.items():
    layers = []
    print(f"\n[clip] {clip} prefer={spec.prefer_npk}")
    if spec.layers:
        for layer in spec.layers:
            loaded = ani_layer(layer.folder, layer.name, spec.prefer_npk, maxf=spec.max_frames)
            if loaded:
                layers.append(loaded)
                print(f"  [层] {layer.folder}/{layer.name} fps={loaded['fps']} frames={len(loaded['frames'])}")
            else:
                print(f"  [层缺] {layer.folder}/{layer.name}")
    for img in spec.images:
        loaded = single_layer(img, spec.prefer_npk, fps=spec.fps, maxf=spec.max_frames)
        if loaded:
            layers.append(loaded)
        else:
            print(f"  [单图缺] {img}")
    if layers:
        clips[clip] = layers
        print(f"  [OK] {clip} {len(layers)}层")
    else:
        print(f"  [clip缺] {clip}")

# ---- Pack atlas ----
cells = []
for layers in clips.values():
    for layer in layers:
        cells.extend(layer["frames"])

if not cells:
    raise SystemExit("no skill effect frames loaded")

pad = 1
maxw = 2048
order = sorted(range(len(cells)), key=lambda k: -cells[k]["image"].height)
x = y = rowh = 0
rects = {}
for k in order:
    im = cells[k]["image"]
    w, h = im.width + pad, im.height + pad
    if x + w > maxw:
        x = 0
        y += rowh
        rowh = 0
    rects[k] = (x, y, im.width, im.height)
    x += w
    rowh = max(rowh, h)
H = y + rowh
atlas = Image.new("RGBA", (maxw, H), (0, 0, 0, 0))
for k in order:
    atlas.alpha_composite(cells[k]["image"], (rects[k][0], rects[k][1]))
idmap = {id(cells[k]): rects[k] for k in range(len(cells))}

data = {"clips": {}}
for clip, layers in clips.items():
    out_layers = []
    for layer in layers:
        frames = []
        for frame in layer["frames"]:
            ax, ay, w, h = idmap[id(frame)]
            frames.append([ax, ay, w, h, frame["x"], frame["y"]])
        out_layers.append({"anchor": [layer["ax"], layer["ay"]], "fps": layer["fps"], "frames": frames})
    data["clips"][clip] = out_layers

OUT.mkdir(parents=True, exist_ok=True)
atlas.save(OUT / "skillfx.png")
(OUT / "skillfx.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
(OUT / "skillfx.meta.js").write_text("window.SKILLFX_META=" + json.dumps(data, separators=(",", ":")) + ";", encoding="utf-8")
print("\nskillfx: atlas %dx%d, %d clips, %d帧, PNG %.0fKB" % (maxw, H, len(clips), len(cells), os.path.getsize(OUT / "skillfx.png") / 1024))
