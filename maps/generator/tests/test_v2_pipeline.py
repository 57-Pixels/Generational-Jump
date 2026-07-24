import unittest

import numpy as np

from deeptime.v2.model import WorldConfig, generate_world


class PipelineTests(unittest.TestCase):
    def test_reference_world_is_deterministic_and_finite(self) -> None:
        config = WorldConfig(seed=42, grid_n=12, ticks=12, export_width=128, export_height=64)
        first = generate_world(config)
        second = generate_world(config)
        np.testing.assert_array_equal(first.geology.plate_id, second.geology.plate_id)
        np.testing.assert_allclose(first.geology.elevation_m, second.geology.elevation_m)
        self.assertTrue(np.isfinite(first.climate.precipitation_mm_yr).all())
        self.assertTrue(np.isfinite(first.settlement.h_ac).all())

    def test_present_and_lgm_share_bedrock_and_emergent_land(self) -> None:
        present = generate_world(
            WorldConfig(seed=9, grid_n=12, ticks=10, era="present", export_width=128, export_height=64)
        )
        lgm = generate_world(
            WorldConfig(seed=9, grid_n=12, ticks=10, era="lgm", export_width=128, export_height=64)
        )
        np.testing.assert_allclose(present.geology.elevation_m, lgm.geology.elevation_m)
        self.assertAlmostEqual(present.sea_level_m - lgm.sea_level_m, 120.0, places=6)
        self.assertAlmostEqual(present.sea_level_m, 0.0, places=6)
        self.assertGreater(present.land_fraction, 0.01)
        self.assertLess(present.land_fraction, 0.995)
        self.assertGreaterEqual(lgm.land_fraction, present.land_fraction)

    def test_plate_and_landmass_topology_is_sane(self) -> None:
        world = generate_world(
            WorldConfig(seed=4, grid_n=14, ticks=14, export_width=128, export_height=64)
        )
        world.plate_model.assert_connected(world.grid)
        self.assertGreater(len(np.unique(world.geology.landmass_id[world.land])), 0)
        self.assertLess(len(np.unique(world.geology.landmass_id[world.land])), world.grid.size // 10)


if __name__ == "__main__":
    unittest.main()
