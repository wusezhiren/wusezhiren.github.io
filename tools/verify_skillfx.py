import json
import sys
from pathlib import Path

try:
    from .skillfx_config import TARGET_CLIPS
except ImportError:  # Allow running as `python3 tools/verify_skillfx.py`.
    from skillfx_config import TARGET_CLIPS


def validate_meta(meta, targets=TARGET_CLIPS):
    issues = []
    clips = meta.get("clips") or {}
    for target in targets:
        layers = clips.get(target)
        if not layers:
            issues.append(f"missing clip {target}")
            continue
        for li, layer in enumerate(layers):
            frames = layer.get("frames") if isinstance(layer, dict) else None
            if not frames:
                issues.append(f"{target} layer {li} has no frames")
                continue
            tiny = 0
            for fi, frame in enumerate(frames):
                if not isinstance(frame, list) or len(frame) < 6:
                    issues.append(f"{target} layer {li} frame {fi} invalid frame")
                    continue
                if frame[2] <= 1 and frame[3] <= 1:
                    tiny += 1
            if tiny == len(frames):
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
