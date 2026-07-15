# DOF70 Restoration Task16 Verification

## Scope

The read-only manifest gate covers 13 skills, 9 passives, five weapon branches, base actions, normal/elite/Boss encounters, hit/miss cases, disabled classes, legacy save migration, no-open-blocker policy, automated tests, and browser evidence paths.

## Commands

Run from the repository root:

```text
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/runtime/**/*.test.js
python3 tools/verify_skillfx.py assets/skillfx.json
python3 tools/dof70_skill_audit.py
python3 tools/dof70_action_audit.py
python3 tools/verify_dof70_restoration.py --structural
python3 tools/extract_inline_js.py index.html /tmp/index-inline.js
node --check /tmp/index-inline.js
python3 tools/capture_dof70_evidence.py
python3 tools/verify_dof70_restoration.py --evidence manifest
```

## Evidence status

The structural gate is reproducible and read-only. Browser evidence is **BLOCKED** when Chromium or ffmpeg is unavailable; `capture_dof70_evidence.py` exits non-zero and records the missing dependency in `assets/dof70/evidence/manifest.json`. No screenshot, frame, or MP4 is fabricated. When dependencies are installed, rerun capture and then the evidence gate; every artifact is recorded with a SHA-256 hash.

## Commit

Task16 commit: `test: verify DOF blade and berserker restoration`.
