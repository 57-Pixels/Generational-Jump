"""Seafloor age–depth, trenches, and variable shelves."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.geology import GeologyConfig, simulate_geology
from deeptime.v2.grid import CubedSphere
from deeptime.v2.seafloor import (
    age_depth_m,
    build_seafloor_elevation,
    shelf_mask,
)


class SeafloorFormulaTests(unittest.TestCase):
    def test_depth_monotonic_below_80_ma(self) -> None:
        ages = np.linspace(0.0, 79.0, 40)
        depth = age_depth_m(ages)
        self.assertTrue(np.all(np.diff(depth) > 0.0))

    def test_abyssal_depth_at_150_ma(self) -> None:
        depth = float(age_depth_m(np.array([150.0]))[0])
        self.assertGreaterEqual(depth, 5600.0)
        self.assertLessEqual(depth, 6000.0)


class SeafloorWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grid = CubedSphere.create(32)
        cls.geology, _ = simulate_geology(
            cls.grid,
            GeologyConfig(seed=42, ticks=40, n_plates=10, n_continents=5),
        )

    def test_trenches_deeper_than_nearby_abyssal(self) -> None:
        elev = self.geology.elevation_m
        age = self.geology.seafloor_age_ma
        ocean = self.geology.continental < 0.25
        trench = self.geology.history["subduction"] > 0.35
        trench &= ocean
        if not np.any(trench):
            self.skipTest("no trench cells in this seed/resolution")
        # Compare trench cells to median ocean depth (more negative = deeper).
        abyssal = ocean & (age > 40.0) & ~trench
        if not np.any(abyssal):
            self.skipTest("no abyssal reference cells")
        trench_depth = float(np.median(elev[trench]))
        abyssal_depth = float(np.median(elev[abyssal]))
        self.assertLess(trench_depth, abyssal_depth - 500.0)

    def test_passive_shelves_wider_than_active(self) -> None:
        passive, active = shelf_mask(self.geology, self.grid)
        # Width proxy: fraction of near-coast cells classified as each shelf type.
        if not np.any(passive) or not np.any(active):
            self.skipTest("need both margin types")
        # Count shelf cells as a crude width proxy at this resolution.
        self.assertGreaterEqual(int(passive.sum()), 3 * max(int(active.sum()), 1))

    def test_seafloor_age_field_present_and_finite(self) -> None:
        age = self.geology.seafloor_age_ma
        self.assertEqual(age.shape, (self.grid.size,))
        ocean = self.geology.continental < 0.25
        self.assertTrue(np.isfinite(age[ocean]).all())
        self.assertGreater(float(age[ocean].max()), 5.0)


class SeafloorBuilderUnitTests(unittest.TestCase):
    def test_build_returns_ocean_elevation_array(self) -> None:
        grid = CubedSphere.create(16)
        age = np.full(grid.size, 60.0)
        continental = np.zeros(grid.size)
        memory = {
            "subduction": np.zeros(grid.size),
            "arc": np.zeros(grid.size),
            "ridge": np.zeros(grid.size),
            "transform": np.zeros(grid.size),
            "passive_margin": np.zeros(grid.size),
            "continental_rift": np.zeros(grid.size),
        }
        memory["subduction"][0] = 1.0
        elev, extras = build_seafloor_elevation(
            grid, age, continental, memory, seed=1
        )
        self.assertEqual(elev.shape, (grid.size,))
        self.assertIn("trench", extras)
        self.assertIn("back_arc", extras)
        self.assertLess(float(elev[0]), float(np.median(elev)))


if __name__ == "__main__":
    unittest.main()
