import re
import unittest
from pathlib import Path


HTML = Path("index.html").read_text(encoding="utf-8")


class SkillRuntimeProfileTests(unittest.TestCase):
    def test_every_gameplay_skill_fx_has_runtime_profile(self):
        expected = set(re.findall(r"fx:'([^']+)'", HTML))
        block = re.search(r"const SKILL_RUNTIME_PROFILE=\{(.*?)\n\};", HTML, re.S).group(1)
        profiled = set(re.findall(r"\n\s*([a-z0-9]+):\{", block))
        self.assertEqual(profiled & expected, expected)

    def test_effects_render_in_body_space_with_original_offsets(self):
        # v3: 特效默认与身体同缩放(SPR_SCALE)、以脚底为原点, 逐帧偏移用原版 .ani 数据
        self.assertIn("const scale=prof?.scale ?? SPR_SCALE;", HTML)
        self.assertIn("const aheadPx=prof?.ahead ?? 0, yo=prof?.yo ?? 0;", HTML)
        self.assertIn("drawFXClipLayers(e.clip, e.t*(1000/LOGIC_HZ)", HTML)

    def test_projectiles_prefer_dedicated_flight_clips(self):
        self.assertIn("fxHasClip(sk.fx+'_proj')", HTML)
        self.assertIn("sk.type!=='proj' || fxHasClip(sk.fx+'_proj')", HTML)

    def test_skill_move_uses_runtime_profile_for_profiled_movers(self):
        for fx in ("uppercut", "dragonup", "illusionslash", "souldrain", "bloodseal", "chargecrash", "darkslash", "liftslash"):
            self.assertIn(f"{fx}:SKILL_RUNTIME_PROFILE.{fx}.move", HTML)


if __name__ == "__main__":
    unittest.main()
