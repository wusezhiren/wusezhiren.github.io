# 重建 DOF 70 剑士技能特效 → assets/skillfx.png + 元数据(v3)。
# v3: 用结构化 70ani 解析(tools/ani70.py)保留原版逐帧数据:
#   逐帧 img 引用(多 img/空帧)、逐帧坐标、逐帧延迟(ms)、缩放(IMAGE RATE)、透明度(RGBA)、循环标志。
# 元数据模型: {"v":3,"clips":{name:{"dur":ms,"layers":[{"loop":0|1,"frames":[...]}]}}}
#   实帧 = [sx,sy,sw,sh, ox,oy, delay, rx,ry, a]  (ox/oy=ani坐标+img帧偏移; rx/ry=缩放%; a=0..255)
#   空帧 = [delay]
import collections
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ani70 import parse_ani70
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

# basename -> [(npkstem, img_index, img_name)]; 含无后缀基础包(stem='')
BASE_PACK = PFX.rstrip("_")
print("建立全局img索引...")
base2loc = collections.defaultdict(list)
_pack_dirs = {}


def _index_packs(dir_path, tag):
    for f in glob.glob(str(dir_path / f"{BASE_PACK}*.NPK")):
        stem = os.path.basename(f)[len(BASE_PACK):-4].lstrip("_")
        _pack_dirs[(tag, stem)] = f
        try:
            for i, name, _, _ in read_npk_names(f):
                base = name.split("/")[-1].lower()
                if is_bad_variant(base):
                    continue
                base2loc[base].append(((tag, stem), i, name))
        except Exception as ex:
            print(f"  [索引失败] {f}: {ex}")


_index_packs(IMAGEPACKS, "dof")
# 个别素材(如鬼泣光环 descentsoul)不在 DOF 70 包里, 从旧客户端回退索引
_fallback_packs = ROOT / "地下城与勇士" / "ImagePacks2"
if _fallback_packs.exists() and _fallback_packs != IMAGEPACKS:
    _index_packs(_fallback_packs, "old")

_npk_cache = {}


def npk_data(pack):
    if pack not in _npk_cache:
        _npk_cache[pack] = dict((i, d) for i, d in read_npk(_pack_dirs[pack]))
    return _npk_cache[pack]


_img_cache = {}


def load_img(basename, prefer_npk=None):
    """按 basename 解析 .img, 返回 (key, frames列表) — frames 已做 link 解引用."""
    bn = basename.split("/")[-1].lower()
    locs = base2loc.get(bn, [])
    if not locs:
        return None, None
    locs = sorted(locs, key=lambda l: (l[0][0] != "dof", l[0][1] != prefer_npk, l[0][1] != "", l[0][1], l[1]))
    pack, idx, _name = locs[0]
    key = (pack, idx)
    if key not in _img_cache:
        parsed = parse_img(npk_data(pack)[idx])
        frames = parsed["frames"]

        def res(i):
            fr = frames[i]
            if fr["image"] is None and 0 <= fr.get("link", -1) < len(frames):
                return frames[fr["link"]]
            return fr

        _img_cache[key] = [res(i) for i in range(len(frames))]
    return key, _img_cache[key]


# ---- 收集图集单元(按 (npk,imgidx,frame) 去重) ----
cells = {}


def cell_of(key, fi, frame):
    ck = (key[0], key[1], fi)
    if ck not in cells:
        cells[ck] = {"image": frame["image"], "rect": None}
    return ck


def ani_layer(rel, prefer_npk):
    """把一个特效 .ani 转成 v3 图层(逐帧数据)."""
    pvf_name = f"character/swordman/effect/animation/{rel}.ani"
    raw = pv.read(pvf_name)
    if raw is None:
        return None
    ani = parse_ani70(raw)
    if not ani or not ani["frames"]:
        return None
    imgs = []
    for path in ani["images"]:
        key, frames = load_img(path, prefer_npk)
        imgs.append((key, frames))
    out = []
    for f in ani["frames"]:
        if f["imgIdx"] < 0:
            out.append([f["delay"]])
            continue
        key, frames = imgs[f["imgIdx"]] if f["imgIdx"] < len(imgs) else (None, None)
        fr = frames[f["imgFrame"]] if frames and f["imgFrame"] < len(frames) else None
        if not fr or fr["image"] is None:
            out.append([f["delay"]])
            continue
        rate = f["attrs"].get(7, [(1.0, 1.0)])[-1]
        rx, ry = round(rate[0] * 100), round(rate[1] * 100)
        rgba = f["attrs"].get(9, [-1])[-1]
        a = (rgba >> 24) & 0xFF if rgba != -1 else 255
        ck = cell_of(key, f["imgFrame"], fr)
        out.append([ck, f["x"] + fr["x"], f["y"] + fr["y"], f["delay"], rx, ry, a])
    if not any(len(f) > 1 for f in out):
        return None  # 全空层(原版空壳 ani), 跳过
    loop = 1 if ani["gattrs"].get(0) else 0
    return {"loop": loop, "frames": out, "src": pvf_name}


def image_layer(basename, prefer_npk, fps, loop):
    key, frames = load_img(basename, prefer_npk)
    if not frames:
        return None
    delay = max(30, round(1000.0 / fps))
    out = []
    for fi, fr in enumerate(frames):
        if fr["image"] is None:
            continue
        ck = cell_of(key, fi, fr)
        out.append([ck, fr["x"], fr["y"], delay, 100, 100, 255])
    if not out:
        return None
    return {"loop": 1 if loop else 0, "frames": out, "src": basename}


clips = {}
for clip, spec in BUILD_SKILL_SPECS.items():
    layers = []
    print(f"\n[clip] {clip} prefer={spec.prefer_npk}")
    for rel in spec.anis:
        loaded = ani_layer(rel, spec.prefer_npk)
        if loaded:
            n_real = sum(1 for x in loaded["frames"] if len(x) > 1)
            dur = sum((x[0] if len(x) == 1 else x[3]) for x in loaded["frames"])
            print(f"  [层] {rel} 帧{len(loaded['frames'])}({n_real}实) {dur}ms loop={loaded['loop']}")
            layers.append(loaded)
        else:
            print(f"  [层缺] {rel}")
    for img in spec.images:
        loaded = image_layer(img, spec.prefer_npk, spec.fps, spec.loop_images)
        if loaded:
            print(f"  [单图层] {img} 帧{len(loaded['frames'])}")
            layers.append(loaded)
        else:
            print(f"  [单图缺] {img}")
    if layers:
        clips[clip] = layers
        print(f"  [OK] {clip} {len(layers)}层")
    else:
        print(f"  [clip缺] {clip}")

# ---- 打包图集 ----
if not cells:
    raise SystemExit("no skill effect frames loaded")

pad = 1
maxw = 2048
order = sorted(cells.keys(), key=lambda k: -cells[k]["image"].height)
x = y = rowh = 0
for k in order:
    im = cells[k]["image"]
    w, h = im.width + pad, im.height + pad
    if x + w > maxw:
        x = 0
        y += rowh
        rowh = 0
    cells[k]["rect"] = (x, y, im.width, im.height)
    x += w
    rowh = max(rowh, h)
H = y + rowh
atlas = Image.new("RGBA", (maxw, H), (0, 0, 0, 0))
for k in order:
    atlas.alpha_composite(cells[k]["image"], cells[k]["rect"][:2])

data = {"v": 3, "clips": {}}
for clip, layers in clips.items():
    out_layers = []
    durs = []
    loop_durs = []
    for layer in layers:
        frames = []
        total = 0
        for f in layer["frames"]:
            if len(f) == 1:
                frames.append([f[0]])
                total += f[0]
            else:
                ck, ox, oy, delay, rx, ry, a = f
                sx, sy, sw, sh = cells[ck]["rect"]
                frames.append([sx, sy, sw, sh, ox, oy, delay, rx, ry, a])
                total += delay
        (loop_durs if layer["loop"] else durs).append(total)
        out_layers.append({"loop": layer["loop"], "frames": frames})
    # clip 时长 = 最长一次性图层; 全循环层则取最长循环
    dur = max(durs) if durs else (max(loop_durs) if loop_durs else 500)
    data["clips"][clip] = {"dur": dur, "layers": out_layers}

OUT.mkdir(parents=True, exist_ok=True)
atlas.save(OUT / "skillfx.png")
(OUT / "skillfx.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
(OUT / "skillfx.meta.js").write_text("window.SKILLFX_META=" + json.dumps(data, separators=(",", ":")) + ";", encoding="utf-8")
print("\nskillfx: atlas %dx%d, %d clips, %d帧, PNG %.0fKB" % (
    maxw, H, len(clips), len(cells), os.path.getsize(OUT / "skillfx.png") / 1024))
