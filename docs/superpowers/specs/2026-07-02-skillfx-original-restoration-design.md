# Skill Effects Original Restoration Design

## Goal

Restore the already-integrated swordman skill effects and character actions toward the DOF 70 source version. The first pass focuses on visual fidelity: effect layers, frame order, anchors, scale, timing, facing, spawn offsets, and character casting/movement actions. Hit timing and damage balance are not primary scope, except when a visual/action fix exposes an obviously wrong hit moment.

## Source Assets

Use the local DOF 70 source as the canonical reference:

- `DOF（重生70版本）/DOF_src/DOF重生/客户端/Script.pvf`
- `DOF（重生70版本）/DOF_src/DOF重生/客户端/ImagePacks2/`

The existing `地下城与勇士/` client resources remain a fallback only when a DOF resource is missing or unreadable.

## Target Skills

This phase covers the skills that are already integrated into gameplay and exposed through the current character skill lists:

- `tripleslash` - 三段斩
- `flashcut` - 拔刀斩
- `gorecross` - 十字斩
- `frenzy` - 怒气爆发
- `ghoststep` - 鬼影闪
- `wavespin` - 波动爆发

`uppercut` may be adjusted only where shared action logic affects the target skills.

## Approach

### 1. Resource Extraction Pipeline

Keep `tools/build_skillfx.py` as the main atlas generator, but make it source-aware:

- Prefer DOF 70 `Script.pvf` and `ImagePacks2` paths.
- Build a global `.img` lookup across swordman effect NPKs.
- For layered skills, read `.ani` files from the original animation folders and preserve each layer's anchor and frame delay.
- For single-image skills, select the original main visual `.img` files only when no reliable `.ani` layer exists.
- Avoid placeholder and bad variants such as `(18)`, `(tn)`, or empty 1x1 frames unless the original animation intentionally uses them as timing gaps.

The generated outputs remain compatible with the current frontend:

- `assets/skillfx.png`
- `assets/skillfx.json`
- `assets/skillfx.meta.js`

If needed, the metadata can be extended with optional per-layer fields such as `delay`, `loop`, `blend`, or `offset`, while preserving old consumers.

### 2. Per-Skill Effect Specs

Replace ad-hoc clip declarations with explicit per-skill source specs. Each spec should describe:

- Original PVF animation folder.
- Preferred NPK stem.
- Ordered effect layers.
- Whether each layer is one-shot, delayed, or looping.
- Frame sampling policy: no downsampling for short action effects; conservative caps only for very large looping effects.

This makes the extraction auditable and lets future skills be added without guessing.

### 3. Character Action Playback

In `index.html`, move from broad action buckets toward per-skill action profiles. Each profile can define:

- Character frame sequence.
- Action duration.
- Cast movement window and velocity.
- Effect start progress.
- Effect offset from character feet.
- Whether the skill uses dash, slash, burst, or cast posture.

The first pass should tune profiles for the six target skills only. Existing generic profiles should remain as fallbacks for other attacks.

### 4. Visual Verification

Add or reuse a lightweight preview path for checking generated effects before gameplay tuning:

- Generate a montage/contact sheet per target skill from `assets/skillfx.*`.
- Flag missing clips, empty layers, many 1x1 frames, and unusually large/small anchors.
- Launch the static page and manually cast each skill in-game to verify character action and effect alignment.

## Implementation Boundaries

In scope:

- Source path updates for DOF 70 resources.
- Atlas and metadata regeneration.
- Skill effect layer/frame/anchor corrections.
- Per-skill character action and effect offset tuning.
- Basic visual verification artifacts or scripts.

Out of scope for this pass:

- Adding new non-integrated skills from `SKILLS_SELECT.md`.
- Redesigning combat balance.
- Full original DNF hitbox replication.
- Large renderer rewrites unrelated to skill effects.

## Risks

- DOF client and existing local client may contain different file names or NPK layouts. The generator should log the resolved file for each layer.
- Some original animations use timing-only empty frames. The pipeline must distinguish intentional timing gaps from bad placeholder extraction.
- Skill action frames in the current player atlas may not exactly match original DNF body frames. Tuning should prefer believable original-like timing over forcing unavailable poses.
- Existing worktree has unrelated modifications. Implementation should avoid reverting or overwriting user changes.

## Acceptance Criteria

- `tools/build_skillfx.py` can rebuild the six target clips from the DOF 70 source path.
- `assets/skillfx.json` contains all target clips with non-empty layers and meaningful frame dimensions.
- Target skill effects appear in-game without obvious wrong facing, severe vertical drift, missing layers, or all-frames-at-once timing.
- Character actions for the six target skills use distinct per-skill profiles rather than only generic cast/dash buckets.
- A verification command or documented manual checklist exists for reviewing the six skills after regeneration.
