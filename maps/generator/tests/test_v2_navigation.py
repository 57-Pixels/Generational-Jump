"""Navigability product tests: straits, harbours, shelf break, tides."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import compute_climate, _wind_vectors
from deeptime.v2.grid import CubedSphere
from deeptime.v2.navigation import (
    compute_navigation,
    harbour_rating,
    measure_strait_width_km,
)


class NavigationTests(unittest.TestCase):
    def test_strait_width_matches_geometry(self) -> None:
        grid = CubedSphere.create(24)
        elevation = np.full(grid.size, 400.0)
        # Two seas linked by a narrow corridor.
        north = (grid.lat_deg > 8.0) & (np.abs(grid.lon_deg) < 20.0)
        south = (grid.lat_deg < -8.0) & (np.abs(grid.lon_deg) < 20.0)
        strait = (np.abs(grid.lat_deg) <= 8.0) & (np.abs(grid.lon_deg) < 3.0)
        elevation[north | south | strait] = -200.0
        width = measure_strait_width_km(grid, elevation, 0.0, strait)
        # Direct geometric width ≈ lon span at mid-lat.
        direct = float(
            (grid.lon_deg[strait].max() - grid.lon_deg[strait].min())
            * 111.0
            * np.cos(np.deg2rad(0.0))
        )
        self.assertGreater(direct, 0.0)
        self.assertLessEqual(abs(width - direct) / direct, 0.10)

    def test_harbour_rating_correlates_with_shelter(self) -> None:
        grid = CubedSphere.create(24)
        elevation = np.full(grid.size, -3000.0)
        land = (grid.lon_deg > -5.0) & (grid.lon_deg < 45.0) & (np.abs(grid.lat_deg) < 28.0)
        elevation[land] = 120.0
        # Narrow flooded embayment: high-enclosure coasts along the inlet walls.
        bay = (
            (grid.lon_deg > 18.0)
            & (grid.lon_deg < 42.0)
            & (np.abs(grid.lat_deg) < 4.0)
        )
        elevation[bay] = -60.0
        land = elevation >= 0.0
        wind = _wind_vectors(grid)
        climate = compute_climate(grid, elevation, 0.0)
        nav = compute_navigation(grid, elevation, 0.0, wind, climate)
        valid = grid.neighbors >= 0
        safe = np.where(valid, grid.neighbors, 0)
        n_valid = np.maximum(valid.sum(axis=1), 1)
        coastal = land & np.any(valid & (~land)[safe], axis=1)
        land_frac = np.where(valid, land[safe], False).sum(axis=1) / n_valid
        sheltered = coastal & (land_frac >= 0.55)
        exposed = coastal & (land_frac <= 0.40)
        if sheltered.sum() < 2 or exposed.sum() < 2:
            self.skipTest("insufficient shelter contrast")
        self.assertGreater(
            float(nav.harbour_rating[sheltered].mean()),
            float(nav.harbour_rating[exposed].mean()),
        )
        # Twin sites: pick top-2 harbour cells and require high rating.
        top = np.argsort(-nav.harbour_rating)[:2]
        self.assertTrue(np.all(nav.harbour_rating[top] >= 0.55))


if __name__ == "__main__":
    unittest.main()
