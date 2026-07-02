import json
import unittest
from pathlib import Path

HTML = Path('index.html').read_text(encoding='utf-8')
META = json.loads(Path('assets/skillfx.json').read_text(encoding='utf-8'))


class SkillLayerTimingTests(unittest.TestCase):
    """v3: 图层错峰时序不再手调, 由原版 .ani 逐帧延迟/空帧数据驱动."""

    def test_metadata_is_v3_with_per_frame_delays(self):
        self.assertEqual(META.get('v'), 3)
        clip = META['clips']['tripleslash']
        self.assertGreater(clip['dur'], 0)
        delays = {f[6] for l in clip['layers'] for f in l['frames'] if len(f) > 1}
        self.assertGreater(len(delays), 0)

    def test_gorecross_keeps_original_delayed_cross_layer(self):
        # 原版血十字(slash3)开头是 ~910ms 空帧: 挥砍之后十字才出现
        layers = META['clips']['gorecross']['layers']
        lead_empty = [l['frames'][0][0] for l in layers if len(l['frames'][0]) == 1]
        self.assertTrue(any(d >= 500 for d in lead_empty))

    def test_renderer_walks_original_frame_delays(self):
        self.assertIn('const d=fr.length===1?fr[0]:fr[6];', HTML)
        self.assertIn("if(l.loop||loopAll) t=tMs%total;", HTML)
        self.assertIn('else if(t>=total) continue;', HTML)
        self.assertIn('if(!f||f.length===1) continue;', HTML)

    def test_runtime_uses_dof_action_duration_for_skill_animation(self):
        self.assertIn('function skillActionDurationTicks(fx,fallback)', HTML)
        self.assertIn('const actionDur=skillActionDurationTicks(sk.fx,sk.dur);', HTML)
        self.assertIn('this.attackTimer=Math.max(8,Math.round(actionDur*this.attackSpeedMul()));', HTML)

    def test_effect_lifetime_comes_from_original_clip_duration(self):
        self.assertIn('const durMs=fxClipInfo(sk.fx).dur;', HTML)
        self.assertIn('max:Math.max(12,Math.round(durMs/1000*LOGIC_HZ))', HTML)


if __name__ == '__main__':
    unittest.main()
