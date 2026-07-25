"""Theater refine export: nest t2–t4 detail into deep-tile overlays."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import compute_climate
from deeptime.v2.grid import CubedSphere
from deeptime.v2.theater import build_theater_overlays, sample_overlays
from deeptime.v2.tiles import DeepWindow


def _mini_world():
    grid = CubedSphere.create(12)
    elev = np.full(grid.size, -2800.0)
    land = (np.abs(grid.lon_deg - 140.0) < 25.0) & (np.abs(grid.lat_deg - 30.0) < 20.0)
    elev[land] = 120.0 + 40.0 * grid.lat_deg[land]
    climate = compute_climate(grid, elev, 0.0)
    return grid, elev, climate


class TheaterOverlayTests(unittest.TestCase):
    def test_build_theater_overlays_at_t2(self) -> None:
        grid, elev, climate = _mini_world()
        windows = (DeepWindow("veldara", 132.0, 155.0, 18.0, 45.0),)
        overlays = build_theater_overlays(
            grid,
            elev,
            climate,
            sea_level_m=0.0,
            windows=windows,
            target_km=80.0,
            seed=7,
            iterations=4,
        )
        self.assertEqual(len(overlays), 1)
        ov = overlays[0]
        self.assertEqual(ov.name, "veldara")
        self.assertEqual(ov.rgb.ndim, 3)
        self.assertEqual(ov.rgb.shape[2], 3)
        self.assertGreater(ov.nx * ov.ny, 20)

    def test_sample_overlays_prefers_theater_detail(self) -> None:
        grid, elev, climate = _mini_world()
        windows = (DeepWindow("veldara", 132.0, 155.0, 18.0, 45.0),)
        overlays = build_theater_overlays(
            grid,
            elev,
            climate,
            sea_level_m=0.0,
            windows=windows,
            target_km=80.0,
            seed=7,
            iterations=4,
        )
        lon = np.array([144.0, -20.0])
        lat = np.array([31.0, 10.0])
        base = np.zeros((2, 3), dtype=np.float64)
        base[:] = (0.1, 0.2, 0.3)
        out = sample_overlays(overlays, lon, lat, base)
        # Inside theater window should differ from flat base.
        self.assertFalse(np.allclose(out[0], base[0]))
        # Outside stays base.
        self.assertTrue(np.allclose(out[1], base[1]))


if __name__ == "__main__":
    unittest.main()
