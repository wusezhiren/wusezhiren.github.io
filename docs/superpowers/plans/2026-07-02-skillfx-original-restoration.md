# SkillFX Original Restoration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the six already-integrated swordman skill effects from the DOF 70 source and tune their in-game character actions toward the original feel.

**Architecture:** Keep the existing static frontend and `assets/skillfx.*` contract, but split the skill-effect extraction rules into a small auditable module. Add metadata checks and montage generation so each regenerated clip can be verified before tuning per-skill action profiles in `index.html`.

**Tech Stack:** Python 3 standard library, existing `tools/pvf.py`, `tools/ani.py`, `tools/dnf_img.py`, Pillow, browser-native JavaScript in `index.html`.

---

## File Structure

- Create: `tools/skillfx_config.py` - constants and source specs for DOF 70 skill-effect extraction.
- Modify: `tools/build_skillfx.py` - consume `skillfx_config`, prefer DOF source paths, log resolved layers, preserve backwards-compatible metadata.
- Create: `tools/verify_skillfx.py` - validate generated `assets/skillfx.json` for the six target clips and report suspicious layers/frames.
- Modify: `tools/fx_montage.py` - optionally render target clips from generated `assets/skillfx.*` rather than raw NPK rows.
- Modify: `index.html` - introduce per-skill action/effect profile data and use it in `spawnSkillFX`, `SKILL_MOVE`, and body-frame selection.
- Create: `tests/test_skillfx_config.py` - regression tests for path selection, target spec coverage, and bad-frame filtering policy.
- Create: `tests/test_skillfx_verify.py` - regression tests for metadata validation behavior.
- Modify: `docs/superpowers/specs/2026-07-02-skillfx-original-restoration-design.md` only if implementation discovers a necessary design correction.

## Task 1: Extract SkillFX Configuration

**Files:**
- Create: `tools/skillfx_config.py`
- Create: `tests/test_skillfx_config.py`

- [ ] **Step 1: Write failing config coverage tests**

Create `tests/test_skillfx_config.py`:

```python
import unittest
from pathlib import Path

from tools import skillfx_config as cfg


class SkillFxConfigTests(unittest.TestCase):
    def test_target_specs_cover_integrated_first_pass_skills(self):
        self.assertEqual(set(cfg.TARGET_CLIPS), set(cfg.SKILL_SPECS))

    def test_dof_source_paths_are_preferred_when_present(self):
        root = Path.cwd()
        pvf, imagepacks = cfg.resolve_source_paths(root)
        self.assertIn("DOF", str(pvf))
        self.assertTrue(str(imagepacks).endswith("ImagePacks2"))

    def test_bad_variant_filter_keeps_timing_names_but_rejects_known_bad_assets(self):
        self.assertTrue(cfg.is_bad_variant("(18)slash.img"))
        self.assertTrue(cfg.is_bad_variant("(tn)slash.img"))
        self.assertTrue(cfg.is_bad_variant("abc18eye.img"))
        self.assertFalse(cfg.is_bad_variant("blank_timing_gap.img"))
```

- [ ] **Step 2: Run test to verify RED**

Run: `python3 -m unittest tests.test_skillfx_config -v`

Expected: FAIL or ERROR because `tools.skillfx_config` does not exist yet.

- [ ] **Step 3: Implement minimal config module**

Create `tools/skillfx_config.py` with:

```python
from dataclasses import dataclass
from pathlib import Path

DOF_CLIENT = Path("DOF（重生70版本）/DOF_src/DOF重生/客户端")
FALLBACK_CLIENT = Path("地下城与勇士")
PFX = "sprite_character_swordman_effect_"
OUT_DIR = Path("assets")
TARGET_CLIPS = ("tripleslash", "flashcut", "gorecross", "frenzy", "ghoststep", "wavespin")


@dataclass(frozen=True)
class LayerSpec:
    folder: str
    name: str


@dataclass(frozen=True)
class SkillSpec:
    prefer_npk: str
    layers: tuple[LayerSpec, ...] = ()
    images: tuple[str, ...] = ()
    fps: int = 16
    max_frames: int | None = None


SKILL_SPECS = {
    "tripleslash": SkillSpec("tripleslash", layers=(LayerSpec("tripleslash", "slash1"), LayerSpec("tripleslash", "slash2"), LayerSpec("tripleslash", "slash3"))),
    "flashcut": SkillSpec("flashcut", images=("ld_sworda.img", "ld_swordb.img", "ld_finisheff_b.img")),
    "gorecross": SkillSpec("gorecross", layers=(LayerSpec("gorecross", "slash1"), LayerSpec("gorecross", "slash2"))),
    "frenzy": SkillSpec("atfrenzy", layers=(LayerSpec("frenzy", "cast"), LayerSpec("frenzy", "blast"), LayerSpec("frenzy", "sword1-1"), LayerSpec("frenzy", "sword1-3"), LayerSpec("frenzy", "sword1-4"), LayerSpec("frenzy", "ball"), LayerSpec("frenzy", "buff"))),
    "ghoststep": SkillSpec("ghoststep", layers=(LayerSpec("ghoststepslash", "slash1"), LayerSpec("ghoststepslash", "slash2"), LayerSpec("ghoststepslash", "skull"), LayerSpec("ghoststep", "appear1"), LayerSpec("ghoststep", "appear2"))),
    "wavespin": SkillSpec("wavespinarea", layers=(LayerSpec("wavespinarea", "createbeadnormal"), LayerSpec("wavespinarea", "circle"), LayerSpec("wavespinarea", "circlefront"), LayerSpec("wavespinarea", "hold"))),
}


def resolve_source_paths(root: Path):
    dof = root / DOF_CLIENT
    if (dof / "Script.pvf").exists() and (dof / "ImagePacks2").exists():
        return dof / "Script.pvf", dof / "ImagePacks2"
    fallback = root / FALLBACK_CLIENT
    return fallback / "Script.pvf", fallback / "ImagePacks2"


def is_bad_variant(name: str) -> bool:
    n = name.split("/")[-1].lower()
    return n.startswith("(18)") or n.startswith("(tn)") or "18eye" in n
```

- [ ] **Step 4: Run test to verify GREEN**

Run: `python3 -m unittest tests.test_skillfx_config -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tools/skillfx_config.py tests/test_skillfx_config.py
git commit -m "test: add skill effect extraction config"
```

## Task 2: Add Generated Metadata Verifier

**Files:**
- Create: `tools/verify_skillfx.py`
- Create: `tests/test_skillfx_verify.py`

- [ ] **Step 1: Write failing verifier tests**

Create `tests/test_skillfx_verify.py`:

```python
import unittest

from tools.verify_skillfx import validate_meta


class SkillFxVerifyTests(unittest.TestCase):
    def test_reports_missing_target_clip(self):
        issues = validate_meta({"clips": {}}, targets=("tripleslash",))
        self.assertTrue(any("missing clip tripleslash" in item for item in issues))

    def test_reports_all_empty_frames(self):
        meta = {"clips": {"tripleslash": [{"anchor": [0, 0], "fps": 16, "frames": [[0, 0, 1, 1, 0, 0]]}]}}
        issues = validate_meta(meta, targets=("tripleslash",))
        self.assertTrue(any("suspicious 1x1" in item for item in issues))

    def test_accepts_meaningful_layer(self):
        meta = {"clips": {"tripleslash": [{"anchor": [0, 0], "fps": 16, "frames": [[0, 0, 120, 80, 5, 6]]}]}}
        self.assertEqual(validate_meta(meta, targets=("tripleslash",)), [])
```

- [ ] **Step 2: Run test to verify RED**

Run: `python3 -m unittest tests.test_skillfx_verify -v`

Expected: FAIL or ERROR because `tools.verify_skillfx` does not exist yet.

- [ ] **Step 3: Implement verifier**

Create `tools/verify_skillfx.py` with a pure `validate_meta(meta, targets)` function and a CLI that loads `assets/skillfx.json`. The function should:

- Report `missing clip <name>` when a target is absent.
- Report empty layer/frame arrays.
- Report `suspicious 1x1` when a layer has only tiny frames.
- Report invalid frame arrays shorter than six values.
- Return an empty list for valid generated metadata.

- [ ] **Step 4: Run test to verify GREEN**

Run: `python3 -m unittest tests.test_skillfx_verify -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add tools/verify_skillfx.py tests/test_skillfx_verify.py
git commit -m "test: add skill effect metadata verifier"
```

## Task 3: Refactor `build_skillfx.py` to Use DOF Source Specs

**Files:**
- Modify: `tools/build_skillfx.py`
- Modify: `assets/skillfx.png`
- Modify: `assets/skillfx.json`
- Modify: `assets/skillfx.meta.js`

- [ ] **Step 1: Run current tests before editing**

Run: `python3 -m unittest tests.test_skillfx_config tests.test_skillfx_verify -v`

Expected: PASS.

- [ ] **Step 2: Update imports and paths**

Modify `tools/build_skillfx.py` to import `OUT_DIR`, `PFX`, `SKILL_SPECS`, `is_bad_variant`, and `resolve_source_paths` from `tools/skillfx_config.py`. Resolve source paths from repository root instead of hard-coding `地下城与勇士/`.

- [ ] **Step 3: Replace `LAYERED`/`SINGLE` with config-driven loop**

Loop over `SKILL_SPECS.items()`:

- For `spec.layers`, call `ani_layer(layer.folder, layer.name, spec.prefer_npk)`.
- For `spec.images`, call `single_layer(img, spec.prefer_npk, fps=spec.fps)`.
- Log each resolved clip/layer and missing layer with the original folder/name.

- [ ] **Step 4: Preserve frame quality**

Change frame sampling so target action clips are not reduced to 14 frames by default. Use `spec.max_frames` only when set; otherwise keep all valid frames.

- [ ] **Step 5: Rebuild assets**

Run: `python3 tools/build_skillfx.py`

Expected: command exits 0 and logs all six target clips.

- [ ] **Step 6: Verify generated metadata**

Run: `python3 tools/verify_skillfx.py assets/skillfx.json`

Expected: PASS/no issues for the six target clips.

- [ ] **Step 7: Commit**

Run:

```bash
git add tools/build_skillfx.py assets/skillfx.png assets/skillfx.json assets/skillfx.meta.js
git commit -m "feat: rebuild skill effects from DOF source"
```

## Task 4: Add Target Clip Montage Verification

**Files:**
- Modify: `tools/fx_montage.py`

- [ ] **Step 1: Write failing smoke check command**

Run: `python3 tools/fx_montage.py /tmp/skillfx-targets.png --from-meta assets/skillfx.json tripleslash flashcut gorecross frenzy ghoststep wavespin`

Expected: FAIL because `--from-meta` is not implemented yet.

- [ ] **Step 2: Implement `--from-meta` mode**

Extend `tools/fx_montage.py` so `--from-meta <json>` loads `assets/skillfx.png` and renders one row per named clip from generated metadata. Keep existing raw-NPK mode unchanged.

- [ ] **Step 3: Generate target montage**

Run: `python3 tools/fx_montage.py /tmp/skillfx-targets.png --from-meta assets/skillfx.json tripleslash flashcut gorecross frenzy ghoststep wavespin`

Expected: exits 0 and writes `/tmp/skillfx-targets.png`.

- [ ] **Step 4: Commit**

Run:

```bash
git add tools/fx_montage.py
git commit -m "chore: add generated skill effect montage"
```

## Task 5: Introduce Per-Skill Runtime Profiles

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Add a small browser-independent profile test by static inspection**

Before editing, run:

```bash
python3 - <<'PY'
from pathlib import Path
html = Path('index.html').read_text()
assert 'const SKILL_RUNTIME_PROFILE=' in html
PY
```

Expected: FAIL with `AssertionError` because the profile table is not implemented yet.

- [ ] **Step 2: Add `SKILL_RUNTIME_PROFILE` near `SKILL_MOVE`**

Add a table for the six target skills with values for `move`, `effect`, and `pose`. Example shape:

```js
const SKILL_RUNTIME_PROFILE={
  tripleslash:{move:{vx:3.2,t:'dur'}, effect:{scale:0.62,yo:64,ahead:70,follow:true,maxMul:1.15}, pose:[2,3,4,5,6,189,190,191,192,193,195,196,197,198]},
  flashcut:{move:{vx:8.0,t:10}, effect:{scale:0.72,yo:62,ahead:96,follow:true,maxMul:1.0}, pose:[21,22,23,24,25,26,27,28,29,30,31,32]},
  gorecross:{move:{vx:2.2,t:'dur'}, effect:{scale:0.62,yo:66,ahead:72,follow:true,maxMul:1.0}, pose:[10,11,12,13,14,15,200,201,202,203]},
  frenzy:{move:null, effect:{scale:0.95,yo:58,ahead:0,follow:false,maxMul:1.25}, pose:[188,190,192,194,196,198,200,202,204,206,208,209]},
  ghoststep:{move:null, effect:{scale:0.72,yo:74,ahead:48,follow:true,maxMul:1.0}, pose:[194,195,196,197,198]},
  wavespin:{move:null, effect:{scale:0.9,yo:56,ahead:0,follow:false,maxMul:1.1}, pose:[66,196,70,200]},
};
```

Tune these values during manual verification, but keep the object shape stable.

- [ ] **Step 3: Wire `SKILL_MOVE` to profile moves**

Replace hard-coded target entries in `SKILL_MOVE` with values from `SKILL_RUNTIME_PROFILE[fx]?.move`, while keeping non-target skills unchanged.

- [ ] **Step 4: Wire body poses to profiles**

Change `pickSwordFrame` so `SKILL_RUNTIME_PROFILE[at.fx]?.pose` wins before `SKILL_POSE[at.fx]`.

- [ ] **Step 5: Wire `spawnSkillFX` to profile effects**

Change `spawnSkillFX` to use `SKILL_RUNTIME_PROFILE[sk.fx]?.effect` for `scale`, `yo`, `ahead`, `follow`, and `max` duration. Keep the generic calculation as fallback.

- [ ] **Step 6: Re-run static inspection**

Run the same static check from Step 1.

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add index.html
git commit -m "feat: add per-skill runtime effect profiles"
```

## Task 6: Full Verification and Manual Checklist

**Files:**
- Modify: `PLAN.md` or create a short verification note if no better doc exists.

- [ ] **Step 1: Run automated verification**

Run:

```bash
python3 -m unittest tests.test_skillfx_config tests.test_skillfx_verify -v
python3 tools/build_skillfx.py
python3 tools/verify_skillfx.py assets/skillfx.json
python3 tools/fx_montage.py /tmp/skillfx-targets.png --from-meta assets/skillfx.json tripleslash flashcut gorecross frenzy ghoststep wavespin
```

Expected: all commands exit 0.

- [ ] **Step 2: Serve the page locally**

Run: `python3 -m http.server 8000`

Expected: page is available at `http://localhost:8000/`.

- [ ] **Step 3: Manual visual UAT**

In browser, cast each target skill and check:

- 三段斩: three advancing slashes appear in sequence and follow the character.
- 拔刀斩: draw-slash effect appears forward and not behind/too high.
- 十字斩: cross blood slash is centered in front of the character.
- 怒气爆发: burst stays around the cast point and does not chase after dash movement.
- 鬼影闪: slash/ghost layers face the same direction as the player.
- 波动爆发: circular/spin effect is centered around the player and not vertically drifting.

- [ ] **Step 4: Record verification note**

Add a short checklist entry to `PLAN.md` or a dedicated docs note with the commands run and any manual observations.

- [ ] **Step 5: Final commit**

Run:

```bash
git add PLAN.md docs/superpowers/plans/2026-07-02-skillfx-original-restoration.md
git commit -m "docs: record skill effect verification checklist"
```

## Non-Subagent Execution Note

The original brainstorming/writing-plan workflow recommends a plan-review subagent. This session's active tool policy forbids spawning subagents unless the user explicitly requests delegation, so execute inline unless the user asks for subagents later.
