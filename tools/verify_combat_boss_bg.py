#!/usr/bin/env python3
"""Static checks for combat feel, boss staging, and background depth polish."""
from __future__ import annotations

from pathlib import Path

src = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
checks: list[tuple[str, bool]] = []

def check(name: str, ok: bool) -> None:
    checks.append((name, ok))

check("launched enemies can be juggled before knockdown", "juggle" in src and "launched" in src and "airCombo" in src)
check("downed enemies do not gain get-up immunity", "getupProtect" not in src and "起身保护" not in src)
check("player attack speed stat affects timers", "attackSpeedMul" in src and "speedStat" in src)
check("equipment can roll attack speed", "stats.speed" in src or "speed:" in src and "攻速" in src)
check("boss intro lock state exists", "bossIntro" in src and "bossGate" in src)
check("boss room starts boss music", "startBossBgm" in src and "bossBgm" in src)
check("leaving boss room restores normal bgm", "startBgm('normal')" in src or "startBgm()" in src and "bossBgm" in src)
check("background has parallax props", "drawParallaxProps" in src and "bgProps" in src)
check("dungeon data includes scene props", "props:" in src and "parallax" in src)

failed = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(("PASS" if ok else "FAIL") + " - " + name)
if failed:
    raise SystemExit(f"\n{len(failed)} combat/boss/background checks failed")
print("\nAll combat/boss/background checks passed")
