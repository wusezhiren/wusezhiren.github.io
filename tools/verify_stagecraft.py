#!/usr/bin/env python3
"""Static checks for DNF-like dungeon stage presentation polish."""
from __future__ import annotations

import re
from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
checks: list[tuple[str, bool]] = []

def check(name: str, ok: bool) -> None:
    checks.append((name, ok))

check("has stage title banner helper", "function showStageTitle" in src and "stageTitle" in src)
check("enterRoom shows stage title cards", re.search(r"showStageTitle\([^\n]+room", src) is not None)
check("boss room uses warning presentation", "bossWarning" in src and "BOSS" in src)
check("openDoor emits door burst effect", "doorburst" in src and re.search(r"addEffect\(\{type:'doorburst'", src) is not None)
check("transition renders DNF-style cut card", "drawTransitionCard" in src and "NEXT ROOM" in src)
check("equipment pickups have light beam", "drawDropBeam" in src and "rarityBeam" in src)
check("equipment pickup triggers fly-in feedback", "spawnLootFly" in src and "lootFly" in src)
check("boss loot uses stronger equipment beams", "bossDrop" in src and "beamPower" in src)
check("render draws presentation overlays", "drawStageTitle" in src and "drawLootFly" in src)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(("PASS" if ok else "FAIL") + " - " + name)
if failed:
    raise SystemExit(f"\n{len(failed)} stagecraft checks failed")
print("\nAll stagecraft checks passed")
