import json
import sys
from pathlib import Path

try:
    from .skillfx_config import TARGET_CLIPS
except ImportError:  # Allow running as `python3 tools/verify_skillfx.py`.
    from skillfx_config import TARGET_CLIPS


def validate_meta(meta, targets=TARGET_CLIPS, strict=False):
    """校验 v3 元数据: {"v":3,"clips":{name:{"dur",layers:[{loop,frames}]}}}.

    实帧 = [sx,sy,sw,sh,ox,oy,delay,rx,ry,a]; 空帧 = [delay]。
    """
    issues = []
    clips = meta.get("clips") or {}
    for target in targets:
        clip = clips.get(target)
        layers = clip.get("layers") if isinstance(clip, dict) else None
        if not layers:
            issues.append(f"missing clip {target}")
            continue
        if strict and not clip.get("source"):
            issues.append(f"{target} missing source")
        if not isinstance(clip.get("dur"), int) or clip["dur"] <= 0:
            issues.append(f"{target} invalid dur")
        for li, layer in enumerate(layers):
            frames = layer.get("frames") if isinstance(layer, dict) else None
            if not frames:
                issues.append(f"{target} layer {li} has no frames")
                continue
            tiny = 0
            real = 0
            for fi, frame in enumerate(frames):
                if not isinstance(frame, list) or len(frame) not in (1, 10):
                    issues.append(f"{target} layer {li} frame {fi} invalid frame")
                    continue
                if strict and len(frame) == 10 and not isinstance(frame[-1], int):
                    issues.append(f"{target} layer {li} frame {fi} invalid alpha")
                if len(frame) == 1:
                    continue
                real += 1
                if frame[2] <= 1 and frame[3] <= 1:
                    tiny += 1
                if frame[6] <= 0:
                    issues.append(f"{target} layer {li} frame {fi} non-positive delay")
            if real == 0:
                issues.append(f"{target} layer {li} all empty frames")
            elif tiny == real:
                issues.append(f"{target} layer {li} suspicious 1x1 frames")
    return issues


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path("assets/skillfx.json")
    meta = json.loads(path.read_text(encoding="utf-8"))
    issues = validate_meta(meta)
    if issues:
        for issue in issues:
            print("ISSUE", issue)
        return 1
    print(f"skillfx metadata OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
