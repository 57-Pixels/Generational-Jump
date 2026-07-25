"""Canon anchor scoring tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

import numpy as np

from deeptime.v2.anchor import score_eastmarch, score_world
from deeptime.v2.climate import compute_climate
from deeptime.v2.grid import CubedSphere


class AnchorScoreTests(unittest.TestCase):
    def test_eastmarch_orogenic_wall_scores_zero(self) -> None:
        grid = CubedSphere.create(20)
        elevation = np.full(grid.size, -3000.0)
        land = (np.abs(grid.lon_deg) < 50.0) & (np.abs(grid.lat_deg) < 40.0)
        elevation[land] = 200.0
        # Orogenic wall bisecting the eastern plain on a plate boundary.
        wall = land & (np.abs(grid.lon_deg - 30.0) < 4.0)
        elevation[wall] = 2800.0
        plate = np.zeros(grid.size, dtype=np.int32)
        plate[land & (grid.lon_deg >= 30.0)] = 1
        region = land & (grid.lon_deg > 0.0)
        score = score_eastmarch(grid, elevation, plate, region)
        self.assertEqual(score, 0.0)

    def test_eastmarch_open_plain_scores_near_one(self) -> None:
        grid = CubedSphere.create(20)
        elevation = np.full(grid.size, -3000.0)
        land = (np.abs(grid.lon_deg) < 55.0) & (np.abs(grid.lat_deg) < 35.0)
        elevation[land] = 180.0 + 40.0 * (grid.lon_deg[land] / 55.0)
        plate = np.zeros(grid.size, dtype=np.int32)
        region = land & (grid.lon_deg > 5.0)
        score = score_eastmarch(grid, elevation, plate, region)
        self.assertGreater(score, 0.7)

    def test_scoring_is_deterministic(self) -> None:
        grid = CubedSphere.create(16)
        elevation = np.full(grid.size, -3000.0)
        land = grid.xyz[:, 0] > 0.1
        elevation[land] = 250.0 + 800.0 * np.clip(grid.xyz[land, 0], 0, 1)
        plate = np.zeros(grid.size, dtype=np.int32)
        climate = compute_climate(grid, elevation, 0.0)
        world = SimpleNamespace(
            grid=grid,
            sea_level_m=0.0,
            geology=SimpleNamespace(elevation_m=elevation, plate_id=plate),
            climate=climate,
        )
        a = score_world(world)  # type: ignore[arg-type]
        b = score_world(world)  # type: ignore[arg-type]
        self.assertEqual(a.as_dict(), b.as_dict())
        np.testing.assert_array_equal(a.region_cells, b.region_cells)


if __name__ == "__main__":
    unittest.main()
