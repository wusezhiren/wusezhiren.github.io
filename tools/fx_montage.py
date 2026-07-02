# Render skill-effect contact sheets.
# Default mode: one raw effect NPK per row. --from-meta mode: generated assets/skillfx clip rows.
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from dnf_img import parse_img, read_npk
from PIL import Image, ImageDraw

BASE = "地下城与勇士/ImagePacks2/sprite_character_swordman_effect_"


def _safe_text(draw, xy, text, fill):
    draw.text(xy, str(text).encode("ascii", "replace").decode("ascii"), fill=fill)


def _resolve_frame(frames, i):
    frame = frames[i]
    if frame["image"] is None and 0 <= frame.get("link", -1) < len(frames):
        return frames[frame["link"]]
    return frame


def render_raw(out, names):
    cw, ch = 130, 120
    cols = 8
    rowh = ch + 4
    labelw = 170
    sheet = Image.new("RGBA", (labelw + cw * cols, rowh * len(names)), (18, 18, 26, 255))
    draw = ImageDraw.Draw(sheet)
    for r, name in enumerate(names):
        y0 = r * rowh
        _safe_text(draw, (4, y0 + 4), name, (255, 230, 80, 255))
        try:
            entries = read_npk(BASE + name + ".NPK")
            best = 0
            bestn = 0
            for i, (_, data) in enumerate(entries):
                try:
                    frames = parse_img(data)["frames"]
                    cnt = sum(1 for k in range(len(frames)) if _resolve_frame(frames, k)["image"] is not None)
                    if cnt > bestn:
                        bestn = cnt
                        best = i
                except Exception:
                    pass
            frames = parse_img(entries[best][1])["frames"]
            valid = [i for i in range(len(frames)) if _resolve_frame(frames, i)["image"] is not None]
            _safe_text(draw, (4, y0 + 22), "img%d/%d f%d" % (best, len(entries), len(valid)), (150, 150, 160, 255))
            step = max(1, len(valid) // cols)
            for c, i in enumerate(valid[::step][:cols]):
                frame = _resolve_frame(frames, i)
                im = frame["image"]
                s = min(cw / max(1, im.width), (ch - 2) / max(1, im.height), 1.0)
                im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
                sheet.alpha_composite(im2, (labelw + c * cw + (cw - im2.width) // 2, y0 + (ch - im2.height) // 2))
        except Exception as ex:
            _safe_text(draw, (labelw + 4, y0 + 40), "ERR " + str(ex)[:70], (255, 80, 80, 255))
    sheet.save(out)
    print("saved", out, "rows", len(names))


def _clip_bounds(layers):
    """v3 图层集合的包围盒(只统计实帧)."""
    minx = miny = 10**9
    maxx = maxy = -10**9
    for layer in layers:
        for frame in layer.get("frames", []):
            if len(frame) == 1:
                continue
            x, y = frame[4], frame[5]
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x + frame[2])
            maxy = max(maxy, y + frame[3])
    if maxx < minx or maxy < miny:
        return (0, 0, 1, 1)
    return (minx, miny, maxx, maxy)


def _layer_total(layer):
    return sum(f[0] if len(f) == 1 else f[6] for f in layer.get("frames", []))


def _frame_at(layer, t_ms, total):
    if total <= 0:
        return None
    if layer.get("loop"):
        t_ms = t_ms % total
    elif t_ms >= total:
        return None
    acc = 0
    for frame in layer.get("frames", []):
        d = frame[0] if len(frame) == 1 else frame[6]
        if t_ms < acc + d:
            return None if len(frame) == 1 else frame
        acc += d
    return None


def _compose_clip_time(atlas, layers, t_ms, box):
    minx, miny, maxx, maxy = box
    canvas = Image.new("RGBA", (max(1, int(maxx - minx)), max(1, int(maxy - miny))), (0, 0, 0, 0))
    for layer in layers:
        frame = _frame_at(layer, t_ms, _layer_total(layer))
        if frame is None:
            continue
        sx, sy, sw, sh, ox, oy = frame[:6]
        tile = atlas.crop((sx, sy, sx + sw, sy + sh))
        canvas.alpha_composite(tile, (int(ox - minx), int(oy - miny)))
    return canvas


def render_from_meta(out, meta_path, clips):
    meta_path = Path(meta_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    atlas = Image.open(meta_path.with_name("skillfx.png")).convert("RGBA")
    cw, ch = 160, 130
    cols = 8
    rowh = ch + 22
    labelw = 150
    sheet = Image.new("RGBA", (labelw + cw * cols, max(1, rowh * len(clips))), (18, 18, 26, 255))
    draw = ImageDraw.Draw(sheet)
    all_clips = meta.get("clips", {})
    for r, clip in enumerate(clips):
        y0 = r * rowh
        entry = all_clips.get(clip) or {}
        layers = entry.get("layers")
        _safe_text(draw, (4, y0 + 4), clip, (255, 230, 80, 255))
        if not layers:
            _safe_text(draw, (labelw + 4, y0 + 45), "missing clip", (255, 80, 80, 255))
            continue
        dur = max(1, entry.get("dur", 500))
        box = _clip_bounds(layers)
        _safe_text(draw, (4, y0 + 22), f"layers {len(layers)} dur {dur}ms", (150, 150, 160, 255))
        for c in range(cols):
            t_ms = round(c * (dur - 1) / max(1, cols - 1))
            im = _compose_clip_time(atlas, layers, t_ms, box)
            s = min(cw / max(1, im.width), (ch - 18) / max(1, im.height), 1.0)
            im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
            sheet.alpha_composite(im2, (labelw + c * cw + (cw - im2.width) // 2, y0 + 18 + (ch - 18 - im2.height) // 2))
            _safe_text(draw, (labelw + c * cw + 4, y0 + 2), f"{t_ms}ms", (120, 130, 150, 255))
    sheet.save(out)
    print("saved", out, "rows", len(clips))


def main(argv):
    if len(argv) < 3:
        print("usage: fx_montage.py OUT [--from-meta META_JSON] CLIP_OR_NPK...")
        return 2
    out = argv[1]
    if argv[2] == "--from-meta":
        if len(argv) < 5:
            print("usage: fx_montage.py OUT --from-meta META_JSON CLIP...")
            return 2
        render_from_meta(out, argv[3], argv[4:])
    else:
        render_raw(out, argv[2:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
