import unittest
from pathlib import Path

HTML = Path('index.html').read_text(encoding='utf-8')


class SkillLayerTimingTests(unittest.TestCase):
    def test_tripleslash_and_frenzy_have_layer_timing_profiles(self):
        self.assertIn('const SKILL_LAYER_TIMING=', HTML)
        self.assertIn('tripleslash:[[0,0.45],[0.25,0.7],[0.55,1]]', HTML)
        self.assertIn('frenzy:[[0,0.25],[0.08,0.4],[0.2,0.75],[0.35,0.85],[0.5,1],[0,1],[0,1]]', HTML)

    def test_draw_fx_layers_uses_timing_profile(self):
        self.assertIn('const timing=SKILL_LAYER_TIMING[clip];', HTML)
        self.assertIn('if(prog<st||prog>ed) continue;', HTML)

    def test_frenzy_uses_original_burst_layers_as_visual_center(self):
        self.assertIn('const SKILL_FX_REF={frenzy:{cx:300,cy:-70}};', HTML)
        self.assertIn('const ref=SKILL_FX_REF[clip];', HTML)
        self.assertIn('if(ref) r={...r,...ref};', HTML)

    def test_runtime_uses_dof_action_duration_for_skill_animation_and_effects(self):
        self.assertIn('function skillActionDurationTicks(fx,fallback)', HTML)
        self.assertIn('const actionDur=skillActionDurationTicks(sk.fx,sk.dur);', HTML)
        self.assertIn('this.attackTimer=Math.max(8,Math.round(actionDur*this.attackSpeedMul()));', HTML)
        self.assertIn('const actionMax=skillActionDurationTicks(sk.fx,0);', HTML)
        self.assertIn('max:Math.max(20,prof?.max||actionMax||Math.round(n*maxMul))', HTML)


if __name__ == '__main__':
    unittest.main()
