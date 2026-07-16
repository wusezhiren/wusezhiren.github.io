import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools import build_player_atlas as atlas


class WeaponAtlasTests(unittest.TestCase):
    def test_dof70_weapon_mapping_has_five_canonical_types(self):
        self.assertEqual(set(atlas.WEAPON_NPKS), {
            "lightsword", "katana", "greatsword", "club", "shortsword"
        })
        self.assertEqual(atlas.WEAPON_ALIASES, {"lswd": "katana", "beamswd": "lightsword"})
        self.assertTrue(all("ImagePacks2" in str(path) for path in atlas.WEAPON_NPKS.values()))

    def test_build_outputs_png_json_and_meta_for_all_weapons(self):
        frame = {"image": Image.new("RGBA", (2, 2), (255, 0, 0, 255)),
                 "x": 0, "y": 0, "w": 2, "h": 2, "link": -1, "form": 0x10}
        with tempfile.TemporaryDirectory() as tmp, patch.object(atlas, "load", return_value=[frame]):
            meta = atlas.build_weapons(Path(tmp), ["lightsword", "katana", "greatsword", "club", "shortsword"])
            canonical = {"lightsword", "katana", "greatsword", "club", "shortsword"}
            self.assertTrue(canonical <= set(meta))
            for name in canonical:
                self.assertTrue((Path(tmp) / f"weapon_{name}.png").is_file())
                self.assertTrue((Path(tmp) / f"weapon_{name}.json").is_file())
            parsed = json.loads((Path(tmp) / "weapons.meta.js").read_text().split("=", 1)[1][:-1])
            self.assertTrue(canonical <= set(parsed))

    def test_invalid_inputs_fail_loudly(self):
        with self.assertRaises(FileNotFoundError):
            atlas.load(Path("/does/not/exist.npk"))
        with self.assertRaises(ValueError):
            atlas.resolve([{"image": None, "link": 4}], 0)
        with self.assertRaises(ValueError):
            atlas.validate_frames([{"image": None, "link": -1, "form": 0x10}])

    def test_composes_weapon_base_and_glow_layers_on_shared_canvas(self):
        base = {"image": Image.new("RGBA", (2, 3), (255, 0, 0, 255)),
                "x": 4, "y": 5, "w": 2, "h": 3, "fw": 20, "fh": 20, "link": -1, "form": 0x10}
        glow = {"image": Image.new("RGBA", (3, 2), (0, 0, 255, 255)),
                "x": 7, "y": 3, "w": 3, "h": 2, "fw": 20, "fh": 20, "link": -1, "form": 0x10}
        merged = atlas.compose_layers([base], [glow])[0]
        self.assertEqual((merged["x"], merged["y"], merged["w"], merged["h"]), (4, 3, 6, 5))
        self.assertEqual(merged["image"].getpixel((0, 2)), (255, 0, 0, 255))
        self.assertEqual(merged["image"].getpixel((3, 0)), (0, 0, 255, 255))


if __name__ == "__main__":
    unittest.main()
