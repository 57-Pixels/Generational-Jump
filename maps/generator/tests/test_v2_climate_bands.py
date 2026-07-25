"""Climate rain-shadow, SST asymmetry, and upwelling aridity tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import compute_climate
from deeptime.v2.grid import CubedSphere
from deeptime.v2.ocean import compute_ocean


class ClimateBandTests(unittest.TestCase):
    def test_rain_shadow_across_synthetic_ridge(self) -> None:
        grid = CubedSphere.create(24)
        elevation = np.full(grid.size, -3000.0)
        # Meridional continent + ridge so mid-latitude westerlies cross it.
        land = (np.abs(grid.lon_deg) < 80.0) & (np.abs(grid.lat_deg) < 55.0)
        elevation[land] = 200.0
        ridge = land & (np.abs(grid.lon_deg) < 8.0) & (np.abs(grid.lat_deg) < 50.0)
        elevation[ridge] = 3200.0
        climate = compute_climate(grid, elevation, 0.0)
        band = np.abs(grid.lat_deg - 40.0) < 12.0
        windward = land & band & (grid.lon_deg < -12.0) & (grid.lon_deg > -45.0)
        leeward = land & band & (grid.lon_deg > 12.0) & (grid.lon_deg < 45.0)
        if not np.any(windward) or not np.any(leeward):
            self.skipTest("ridge fixture produced empty flanks")
        wet = float(climate.precipitation_mm_yr[windward].mean())
        dry = float(climate.precipitation_mm_yr[leeward].mean())
        self.assertGreater(wet, 3.0 * dry)

    def test_west_east_sst_contrast_at_40_lat(self) -> None:
        grid = CubedSphere.create(32)
        elevation = np.full(grid.size, -3000.0)
        # Two meridional continents so oceans have west/east margins.
        land = (np.abs(grid.lon_deg) < 25) | (np.abs(grid.lon_deg - 180) < 25) | (
            np.abs(grid.lon_deg + 180) < 25
        )
        land &= np.abs(grid.lat_deg) < 70
        elevation[land] = 300.0
        climate = compute_climate(grid, elevation, 0.0)
        self.assertIsNotNone(climate.sst_c)
        band = (~land) & (np.abs(grid.lat_deg - 40.0) < 6.0)
        if int(band.sum()) < 10:
            self.skipTest("not enough ocean cells at 40N")
        # West-coast ocean (land immediately east) vs east-coast ocean.
        valid = grid.neighbors >= 0
        safe = np.where(valid, grid.neighbors, 0)
        lon = grid.lon_deg
        west_ocean = np.zeros(grid.size, dtype=bool)
        east_ocean = np.zeros(grid.size, dtype=bool)
        for i in range(grid.neighbors.shape[1]):
            n = safe[:, i]
            west_ocean |= band & valid[:, i] & land[n] & (grid.lon_deg[n] > lon)
            east_ocean |= band & valid[:, i] & land[n] & (grid.lon_deg[n] < lon)
        if not np.any(west_ocean) or not np.any(east_ocean):
            self.skipTest("missing west/east ocean margins")
        west_sst = float(climate.sst_c[west_ocean].mean())
        east_sst = float(climate.sst_c[east_ocean].mean())
        # Western boundary currents are warmer at ~40N in this model.
        delta = west_sst - east_sst
        self.assertGreater(delta, 2.0)
        self.assertLess(delta, 12.0)

    def test_coastal_desert_beside_upwelling(self) -> None:
        grid = CubedSphere.create(32)
        elevation = np.full(grid.size, -3000.0)
        land = grid.xyz[:, 0] > 0.15
        elevation[land] = 250.0
        climate = compute_climate(grid, elevation, 0.0)
        self.assertIsNotNone(climate.upwelling)
        desert = land & (climate.precipitation_mm_yr < 250.0)
        valid = grid.neighbors >= 0
        safe = np.where(valid, grid.neighbors, 0)
        beside_upwelling = np.zeros(grid.size, dtype=bool)
        for i in range(grid.neighbors.shape[1]):
            n = safe[:, i]
            beside_upwelling |= (
                desert & valid[:, i] & (~land[n]) & (climate.upwelling[n] > 0.25)
            )
        self.assertTrue(np.any(beside_upwelling))


if __name__ == "__main__":
    unittest.main()
