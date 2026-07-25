"""Canon anchor scoring tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from deeptime.v2.anchor import (
    promote_best,
    score_eastmarch,
    score_world,
    sweep_seeds,
)
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
        a = score_world(world)
        b = score_world(world)
        self.assertEqual(a.as_dict(), b.as_dict())
        np.testing.assert_array_equal(a.region_cells, b.region_cells)

    def test_sweep_ranks_deterministically(self) -> None:
        results = sweep_seeds(
            [3, 1, 2],
            grid_n=16,
            ticks=6,
            tier="dev",
            use_cache=False,
        )
        self.assertEqual(len(results), 3)
        totals = [r.score.total for r in results]
        self.assertEqual(totals, sorted(totals, reverse=True))
        for i in range(len(results) - 1):
            if abs(results[i].score.total - results[i + 1].score.total) < 1e-12:
                self.assertLessEqual(results[i].seed, results[i + 1].seed)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "promoted-seed.json"
            payload = promote_best(results, path)
            self.assertTrue(path.exists())
            loaded = json.loads(path.read_text())
            self.assertEqual(loaded["status"], payload["status"])
            self.assertIn(loaded["status"], ("promoted", "unreachable"))


if __name__ == "__main__":
    unittest.main()
