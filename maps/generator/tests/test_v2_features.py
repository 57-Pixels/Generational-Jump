"""Feature extraction stability and enclosed-sea classification tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.features import (
    classify_sea_enclosure,
    extract_features,
    features_to_geojson,
)
from deeptime.v2.grid import CubedSphere
from deeptime.v2.model import WorldConfig, generate_world


class FeatureTests(unittest.TestCase):
    def test_ids_and_names_stable_across_runs(self) -> None:
        world = generate_world(
            WorldConfig(
                seed=12,
                grid_n=24,
                ticks=12,
                tier="dev",
                use_cache=False,
                validate=False,
            )
        )
        a = extract_features(world)
        b = extract_features(world)
        self.assertEqual(
            [(f.kind, f.feature_id, f.name) for f in a],
            [(f.kind, f.feature_id, f.name) for f in b],
        )
        geo = features_to_geojson(a, world)
        self.assertEqual(geo["type"], "FeatureCollection")
        self.assertGreater(len(geo["features"]), 0)

    def test_mediterranean_classifies_enclosed_open_bay_does_not(self) -> None:
        grid = CubedSphere.create(28)
        elevation = np.full(grid.size, 300.0)
        # Open ocean to the west.
        elevation[grid.lon_deg < -50.0] = -3000.0
        # Enclosed sea: nearly landlocked basin with a narrow strait.
        basin = (
            (grid.lon_deg > -10.0)
            & (grid.lon_deg < 25.0)
            & (grid.lat_deg > -8.0)
            & (grid.lat_deg < 12.0)
        )
        elevation[basin] = -800.0
        # Narrow western opening (strait).
        strait = (
            (grid.lon_deg >= -18.0)
            & (grid.lon_deg <= -8.0)
            & (np.abs(grid.lat_deg - 2.0) < 2.5)
        )
        elevation[strait] = -400.0
        enclosed = classify_sea_enclosure(grid, elevation, 0.0)
        self.assertTrue(np.any(enclosed.enclosed_sea_mask))
        self.assertFalse(np.any(enclosed.open_bay_mask & enclosed.enclosed_sea_mask))

        # Reset: open bay on a straight coast — should not be enclosed.
        elevation2 = np.full(grid.size, -3000.0)
        land = grid.lon_deg > 0.0
        elevation2[land] = 200.0
        bay = land & (grid.lon_deg < 15.0) & (np.abs(grid.lat_deg) < 10.0)
        elevation2[bay] = -200.0
        # Actually make bay ocean indentation into land.
        elevation2 = np.full(grid.size, -3000.0)
        land = (grid.lon_deg > 10.0) | (np.abs(grid.lat_deg) > 20.0)
        elevation2[land] = 250.0
        # Broad open embayment.
        open_bay = (
            (grid.lon_deg > -5.0)
            & (grid.lon_deg < 10.0)
            & (np.abs(grid.lat_deg) < 12.0)
        )
        elevation2[open_bay] = -500.0
        elevation2[land & open_bay] = 250.0
        classified = classify_sea_enclosure(grid, elevation2, 0.0)
        # Open bay water should not be tagged enclosed.
        water = elevation2 < 0.0
        self.assertFalse(np.any(classified.enclosed_sea_mask & water & open_bay))


if __name__ == "__main__":
    unittest.main()
