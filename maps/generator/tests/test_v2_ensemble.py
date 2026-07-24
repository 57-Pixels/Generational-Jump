import unittest
from collections import Counter

import numpy as np

from deeptime.v2.model import WorldConfig, generate_world
from deeptime.v2.resources import DEPOSIT_CATALOG


class EnsembleTests(unittest.TestCase):
    def test_reduced_seed_ensemble_meets_world_invariants(self) -> None:
        ensemble_mechanisms: set[str] = set()
        for seed in range(1, 4):
            with self.subTest(seed=seed):
                world = generate_world(
                    WorldConfig(seed=seed, grid_n=20, ticks=24, export_width=128, export_height=64)
                )
                self.assertGreaterEqual(world.land_fraction, 0.26)
                self.assertLessEqual(world.land_fraction, 0.32)
                world.plate_model.assert_connected(world.grid)
                landmasses = np.unique(world.geology.landmass_id[world.land])
                self.assertGreater(len(landmasses), 0)
                self.assertLess(len(landmasses), world.grid.size // 10)

                counts = Counter(deposit.deposit_class for deposit in world.deposits)
                self.assertEqual(set(counts), {spec.id for spec in DEPOSIT_CATALOG})
                self.assertGreater(len(set(counts.values())), 1)

                hot = world.land & (world.climate.hottest_wet_bulb_c > 25)
                if np.any(hot):
                    uplift = world.settlement.h_ac[hot] - world.settlement.h_ind[hot]
                    self.assertGreater(float(uplift.mean()), 0.08)
                mechanisms = set(world.settlement.mechanism_ac[world.land])
                ensemble_mechanisms.update(mechanisms)
        self.assertTrue(
            "incentive_driven" in ensemble_mechanisms
            or "combined" in ensemble_mechanisms
        )


if __name__ == "__main__":
    unittest.main()
