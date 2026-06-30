#!/usr/bin/env python3
"""Static checks for the multi-dungeon map-select milestone."""
from __future__ import annotations

import re
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "index.html"
src = HTML.read_text(encoding="utf-8")

checks: list[tuple[str, bool]] = []

def check(name: str, ok: bool) -> None:
    checks.append((name, ok))

check("defines DUNGEONS data table", "const DUNGEONS" in src and "monsterPool" in src and "recommendedLv" in src)
check("defines current dungeon helper", "function currentDungeonDef" in src)
check("has map-select game state", "gameState='mapsel'" in src or 'gameState="mapsel"' in src or "gameState === 'mapsel'" in src)
check("draws map-select screen", "function drawMapSelect" in src)
check("updates map-select input", "if(gameState==='mapsel')" in src or "if(gameState === 'mapsel')" in src)
check("startGame enters map-select instead of direct play", re.search(r"function startGame\([^)]*\)[\s\S]*?gameState\s*=\s*'mapsel'", src) is not None)
check("enterRoom uses selected map monster pool", "monsterPool" in src and "pickMonsterKind(dun)" in src and re.search(r"new Enemy\([^\n]+kind", src) is not None)
check("boss uses selected map boss", re.search(r"new Enemy\([^\n]+\.boss", src) is not None)
check("background uses selected map tint", "currentDungeonDef().tint" in src or "dun.tint" in src)
check("clear unlocks next dungeon", "unlockNextDungeon" in src and "Save.data.unlocked" in src)
check("run save stores dungeon id", "dungeonId" in src and re.search(r"Save\.data\.run\s*=\{[\s\S]*dungeonId", src) is not None)
check("continue restores dungeon id", re.search(r"dungeonId\s*=\s*r\.dungeonId", src) is not None)
check("debug shot can open map select", "q.get('state')==='mapsel'" in src or 'q.get("state")==="mapsel"' in src)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(("PASS" if ok else "FAIL") + " - " + name)
if failed:
    raise SystemExit(f"\n{len(failed)} multi-dungeon checks failed")
print("\nAll multi-dungeon checks passed")
