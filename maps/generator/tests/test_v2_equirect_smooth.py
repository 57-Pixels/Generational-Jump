"""Equirect sampling smoothness tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.grid import CubedSphere
from deeptime.v2.tiles import _sample_equirect


class EquirectSmoothTests(unittest.TestCase):
    def test_blend_softer_than_nearest_on_cell_boundary(self) -> None:
        grid = CubedSphere.create(12)
        field = np.zeros(grid.size, dtype=np.float64)
        field[grid.lon_deg > 0.0] = 1.0
        nearest = grid.to_equirect(field, 360, 180, blend=False)
        blended = grid.to_equirect(field, 360, 180, blend=True)
        # Nearest is almost binary; blend must create a soft band.
        near_frac = float(np.mean((nearest > 0.05) & (nearest < 0.95)))
        blend_frac = float(np.mean((blended > 0.05) & (blended < 0.95)))
        self.assertLess(near_frac, 0.02)
        self.assertGreater(blend_frac, near_frac + 0.01)
        self.assertLess(float(blended.min()), 0.05)
        self.assertGreater(float(blended.max()), 0.95)
        # Peak step should not exceed nearest's hard 0↔1 jump.
        peak_near = float(np.abs(np.diff(nearest, axis=1)).max())
        peak_blend = float(np.abs(np.diff(blended, axis=1)).max())
        self.assertLessEqual(peak_blend, peak_near + 1e-9)

    def test_bilinear_tile_sample_interpolates_horizontal(self) -> None:
        image = np.zeros((2, 2, 3), dtype=np.uint8)
        image[0, 0] = (0, 0, 0)
        image[0, 1] = (255, 0, 0)
        image[1, 0] = (0, 255, 0)
        image[1, 1] = (0, 0, 255)
        # Pixel center between the two top texels.
        lon = np.array([[0.0]])
        lat = np.array([[45.0]])
        # Force coordinates: sample at x=0.5, y=0.25 of the 2x2 image via lon/lat.
        # Equirect: x = (lon+180)/360*w → lon = x/w*360 - 180
        lon = np.array([[-180.0 + 0.5 / 2.0 * 360.0]])
        lat = np.array([[90.0 - 0.25 / 2.0 * 180.0]])
        pix = _sample_equirect(image, lon, lat)
        # Expect ~halfway between black and red on top row.
        self.assertGreater(int(pix[0, 0, 0]), 80)
        self.assertLess(int(pix[0, 0, 0]), 200)


if __name__ == "__main__":
    unittest.main()
