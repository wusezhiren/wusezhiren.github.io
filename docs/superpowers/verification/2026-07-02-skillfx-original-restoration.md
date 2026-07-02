# SkillFX Original Restoration Verification

Date: 2026-07-02
Worktree: `.worktrees/skillfx-original-restoration`

## Automated Checks

Commands used:

```bash
python3 -m unittest tests.test_skillfx_config tests.test_skillfx_verify -v
python3 tools/build_skillfx.py
python3 tools/verify_skillfx.py assets/skillfx.json
python3 tools/fx_montage.py /tmp/skillfx-targets.png --from-meta assets/skillfx.json tripleslash flashcut gorecross frenzy ghoststep wavespin
python3 - <<'PY'
from pathlib import Path
import re
html=Path('index.html').read_text()
parts=[m.group(1) for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S|re.I)]
Path('/tmp/index-inline.js').write_text('\n'.join(parts))
print(len(parts), 'inline scripts extracted')
PY
node --check /tmp/index-inline.js
```

Results observed:

- 8 unittest checks passed.
- `tools/build_skillfx.py` resolved DOF 70 resources from `DOF（重生70版本）/DOF_src/DOF重生/客户端`.
- `tools/verify_skillfx.py` reported `skillfx metadata OK` for the six target clips.
- `tools/fx_montage.py --from-meta` generated `/tmp/skillfx-targets.png` with six rows.
- `node --check /tmp/index-inline.js` exited 0.

## Montage Review

Reviewed `/tmp/skillfx-targets.png` visually:

- `tripleslash`: three orange slash layers are visible and progress across the row.
- `flashcut`: uses the DOF `momentaryslash` white dodge layers; the slash is visible on dark background.
- `gorecross`: red slash and cross layers appear in sequence.
- `frenzy`: red burst/sword/blood-stone layers render across the row without all-1x1 output.
- `ghoststep`: ghost body, light, skull, and slash layers render with 32-frame timing.
- `wavespin`: bead/circle/front/hold layers render; small white hold frames are visible.

## Manual Browser UAT

Manual in-browser casting is still recommended after merge from the main workspace:

- 三段斩: confirm the three slashes follow the advancing character.
- 拔刀斩: confirm the white draw-slash is forward-facing and not too high.
- 十字斩: confirm the red cross appears centered in front of the character.
- 怒气爆发: confirm burst stays around the cast point.
- 鬼影闪: confirm ghost/slash layers face the same direction as the player.
- 波动爆发: confirm the spin effect is centered and does not drift vertically.

## Body Action Timeline Extraction

Second-stage commands used after adding original body action parsing:

```bash
python3 -m unittest tests.test_skillfx_config tests.test_skillfx_verify tests.test_skill_actions -v
python3 tools/build_skill_actions.py
python3 tools/build_skillfx.py
python3 tools/verify_skillfx.py assets/skillfx.json
python3 tools/fx_montage.py /tmp/skillfx-targets.png --from-meta assets/skillfx.json tripleslash flashcut gorecross frenzy ghoststep wavespin
node --check /tmp/index-inline.js
```

Results observed:

- 11 unittest checks passed.
- `tools/build_skill_actions.py` generated `assets/skill_actions.json` and `assets/skill_actions.meta.js` from DOF 70 body `.ani` files.
- Extracted body action clips:
  - `tripleslash`: `tripleslash1`, `tripleslash2`, `tripleslash3`, 13 frames, 1140 ms.
  - `flashcut`: `momentaryslash`, 12 frames, 1055 ms.
  - `gorecross`: `gorecross`, 29 frames, 1330 ms.
  - `frenzy`: `frenzy1` to `frenzy4`, 22 frames, 2580 ms.
  - `ghoststep`: `ghoststepslashready`, `ghoststepslashmove`, 5 frames, 640 ms.
  - `wavespin`: `shockwaveareacast`, 2 frames, 510 ms.
- `index.html` now loads `assets/skill_actions.meta.js` and prefers original-delay action timelines before falling back to legacy pose arrays.

## Follow-up: Full Runtime Profile Coverage

Triggered by manual feedback that most skills still looked unrestored or misaligned after the six-skill first pass.

Root cause confirmed:

- `assets/skillfx.json` contains all current gameplay `fx` clips.
- `assets/skill_actions.json` contains all 25 current gameplay action clips.
- `index.html` only had six tuned `SKILL_RUNTIME_PROFILE` entries, so the other 19 gameplay skills used generic placement.
- Generic placement drew effects around the generated bounding-box center, which discarded original `.ani/.img` offsets and caused visible drift for source-offset-based clips.

Commands used:

```bash
python3 -m unittest tests.test_skillfx_config tests.test_skillfx_verify tests.test_skill_actions tests.test_skillfx_assets tests.test_skill_layer_timing tests.test_skill_runtime_profile -v
python3 tools/verify_skillfx.py assets/skillfx.json
python3 - <<'PY'
from pathlib import Path
import re
html=Path('index.html').read_text(encoding='utf-8')
parts=[m.group(1) for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S|re.I)]
Path('/tmp/index-inline.js').write_text('\n'.join(parts), encoding='utf-8')
print(len(parts), 'inline scripts extracted')
PY
node --check /tmp/index-inline.js
```

Results observed:

- 21 unittest checks passed.
- `tools/verify_skillfx.py` reported `skillfx metadata OK`.
- `node --check /tmp/index-inline.js` exited 0.
- Headless Chrome generated 24 screenshots using `?shot=<class>&sk=<q|w|e|a|s|d>` and wrote montage `/tmp/dnf-skill-shots-all/montage.png`.
- Visual montage review confirmed all 24 current class skills trigger visible effects; no blank/missing-sprite regression was observed.

## v3: Original Per-Frame Timeline Restoration (2026-07-02 second pass)

Triggered by "对一下当前的技能和原版技能的差异，然后修复，包括动作特效".

Audit findings against DOF 70 PVF (authoritative sources: `skill/swordmanskill.lst` + `.skl` names,
`character/swordman/effect/animation/**.ani`, `character/swordman/animation/*.ani`):

1. Effect `.ani` files were parsed heuristically (first image / first pos / single delay), which
   discarded per-frame image refs, per-frame offsets, per-frame delays, leading empty frames,
   IMAGE RATE scaling, RGBA alpha, and loop flags. New structural parser `tools/ani70.py`
   (`parse_ani70`) fully decodes 675/675 swordman effect anis and 161/161 body anis
   (frame layout: boxes / i16 imgIdx / u16 imgFrame / posX / posY / attrs; attr widths solved
   per-keyword with backtracking + sanity validation).
2. Wrong skill-to-source mappings fixed:
   - 邪光斩 waveeye → `grandwave` (Evil Light Slash); old source was the awakening 波动之眼.
   - 波动爆发 wavespin → `releasewave1/2` (Release Wave); old source was 不动明王阵素材.
   - 不动明王阵 vajra → `wavespinarea/*` ani layers (Acalanatha Array) + body `wavespinareabomb`.
   - 崩山裂地斩 chargecrash → `outragebreak/*`; 破军升龙击 dragonup → `chargecrash/*` ani.
   - 崩山击 mountaincrash → `hopsmash/*`; 噬灵鬼斩 darkslash → root `hardattack1/2`.
   - 满月斩 liftslash → `moonlightslash1/2` + flying `moonlightslashfull` as `liftslash_proj`.
   - 上挑 uppercut → root `upperslash1/2`; 地裂波动剑 normalwave → `normalwaveslash` +
     flying `normalwave` as `normalwave_proj`; 里·鬼剑术 hiddenblade → `weaponcombo/light+blade`.
   - 拔刀斩 flashcut → root `momentaryslash` + charge loops + none_under/upper ani layers.
   - Missing layers added: gorecross slash3/slash4 (delayed blood cross, ~910ms empty lead),
     tripleslash slash4/5+move1/2, ghoststep dust/move, frenzy createball/ball/swords,
     bloodyrave full 11-layer set, rapidmoveslash/bloodyrave/grabblastblood ani layers.
3. `assets/skillfx.*` regenerated as v3: `{v:3,clips:{name:{dur,layers:[{loop,frames}]}}}` with
   real frame = `[sx,sy,sw,sh,ox,oy,delay,rx,ry,a]`, empty frame = `[delay]`; frames deduped by
   (npk,img,frame): 31 clips, 574 cells, PNG 4.8MB (was 7.2MB).
4. Runtime (`index.html`): `drawFXClipLayers` is now time-driven (ms), walks original per-frame
   delays, skips empty frames, loops loop-layers, applies per-frame scale/alpha, and renders in
   body space (feet origin, `SPR_SCALE`), so effects align with the body pixel-for-pixel like the
   original client. Hand-tuned `SKILL_LAYER_TIMING` / `SKILL_FX_REF` / bbox-centering / per-skill
   scale/yo/ahead fudges removed. Projectiles prefer `<fx>_proj` flight clips.
5. Body actions: `build_skill_actions.py` switched to `parse_ani70` (all 25 clips still build);
   vajra now uses the authoritative `wavespinareabomb` timeline.

Verification commands:

```bash
python3 -m unittest discover -s tests        # 28 tests OK
python3 tools/build_skillfx.py               # 31 clips, no missing layers
python3 tools/build_skill_actions.py         # 25 clips
python3 tools/verify_skillfx.py assets/skillfx.json   # metadata OK
python3 tools/fx_montage.py <out> --from-meta assets/skillfx.json <25 clips + _proj>
node --check /tmp/index-inline.js
# headless Chrome: 24 screenshots (4 classes x q/w/e/a/s/d), montage reviewed
```

Montage/screenshot review: all 24 skills show original multi-layer effects at the caster with
correct timing (delayed gorecross cross, flying full moon, grandwave blade, releasewave burst,
Acalanatha array circle). No blank-sprite regressions.
