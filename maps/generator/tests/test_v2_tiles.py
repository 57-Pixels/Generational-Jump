import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from deeptime.v2.tiles import MERCATOR_MAX_LAT, write_mercator_tiles


class MercatorTileTests(unittest.TestCase):
    def test_writes_expected_xyz_layout_and_samples_equirect(self) -> None:
        # Distinct colors by latitude band so we can check pole-edge sampling.
        height, width = 180, 360
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:20] = (240, 240, 240)  # near north
        image[80:100] = (20, 180, 40)  # equator band
        image[-20:] = (200, 200, 220)  # near south
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "color"
            meta = write_mercator_tiles(image, root, max_zoom=1, tile_size=64)
            self.assertEqual(meta["tile_count"], 1 + 4)
            self.assertTrue((root / "0" / "0" / "0.png").is_file())
            self.assertTrue((root / "1" / "0" / "0.png").is_file())
            z0 = np.array(Image.open(root / "0" / "0" / "0.png"))
            self.assertEqual(z0.shape, (64, 64, 3))
            # Top row of z0 is the north mercator edge (~85°), not empty.
            self.assertGreater(int(z0[0].mean()), 30)
            self.assertAlmostEqual(meta["mercator_max_lat"], MERCATOR_MAX_LAT)

    def test_mercator_max_lat_matches_epsg_3857(self) -> None:
        expected = math.degrees(2 * math.atan(math.exp(math.pi)) - math.pi / 2)
        self.assertAlmostEqual(MERCATOR_MAX_LAT, expected, places=10)


if __name__ == "__main__":
    unittest.main()
