"""Coastal wave energy, shelter/exposure, and fractal-dimension tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import _wind_vectors
from deeptime.v2.coastal import (
    coastline_fractal_dimension,
    evolve_coastline,
)
from deeptime.v2.grid import CubedSphere


def _smooth_blob(grid: CubedSphere) -> np.ndarray:
    elevation = np.full(grid.size, -3000.0)
    land = grid.xyz[:, 0] > 0.35
    elevation[land] = 120.0
    return elevation


def _ragged_continent(grid: CubedSphere) -> np.ndarray:
    elevation = np.full(grid.size, -3200.0)
    land = (np.abs(grid.lon_deg) < 55.0) & (np.abs(grid.lat_deg) < 45.0)
    lon = grid.lon_deg[land]
    lat = grid.lat_deg[land]
    elevation[land] = 80.0 + 30.0 * np.sin(np.deg2rad(lon * 6.0)) * np.cos(
        np.deg2rad(lat * 5.0)
    )
    # Embayments and headlands.
    elevation[land] += 70.0 * np.sin(np.deg2rad(lon * 11.0 + lat))
    rng = np.random.default_rng(4)
    elevation[land] += rng.normal(0.0, 18.0, size=int(land.sum()))
    return elevation


class CoastalTests(unittest.TestCase):
    def test_coastline_fractal_dimension_in_earth_band(self) -> None:
        grid = CubedSphere.create(28)
        elevation = _ragged_continent(grid)
        wind = _wind_vectors(grid)
        result = evolve_coastline(
            grid, elevation, 0.0, wind, iterations=24, seed=3
        )
        dim = coastline_fractal_dimension(grid, result.elevation_m, 0.0)
        self.assertGreaterEqual(dim, 1.15)
        self.assertLessEqual(dim, 1.35)
        # Smooth blob should score well below the evolved ragged coast.
        blob_dim = coastline_fractal_dimension(grid, _smooth_blob(grid), 0.0)
        self.assertLess(blob_dim, dim)

    def test_exposed_coasts_retreat_sheltered_accumulate(self) -> None:
        grid = CubedSphere.create(24)
        elevation = np.full(grid.size, -3000.0)
        # Meridional land so west coast faces open ocean fetch.
        land = (grid.lon_deg > -10.0) & (grid.lon_deg < 40.0) & (np.abs(grid.lat_deg) < 40.0)
        elevation[land] = 150.0
        # Cut a sheltered bay on the east side.
        bay = land & (grid.lon_deg > 25.0) & (np.abs(grid.lat_deg) < 8.0)
        elevation[bay] = 40.0
        wind = _wind_vectors(grid)
        # Force mid-latitude westerlies across the domain for a clear exposure contrast.
        wind[:] = 0.0
        east = np.cross(np.array([0.0, 0.0, 1.0]), grid.xyz)
        east /= np.maximum(np.linalg.norm(east, axis=1, keepdims=True), 1e-12)
        wind[:] = east
        before = elevation.copy()
        result = evolve_coastline(
            grid, elevation, 0.0, wind, iterations=30, seed=5
        )
        valid = grid.neighbors >= 0
        safe = np.where(valid, grid.neighbors, 0)
        coastal = (before >= 0.0) & np.any(valid & (before[safe] < 0.0), axis=1)
        west_exposed = coastal & (grid.lon_deg < 0.0) & (np.abs(grid.lat_deg) < 30.0)
        east_sheltered = coastal & (grid.lon_deg > 20.0) & (np.abs(grid.lat_deg) < 15.0)
        if not np.any(west_exposed) or not np.any(east_sheltered):
            self.skipTest("coast fixture missing exposure contrast")
        west_delta = float((result.elevation_m - before)[west_exposed].mean())
        east_delta = float((result.elevation_m - before)[east_sheltered].mean())
        # Exposed west retreats (negative), sheltered east gains sediment.
        self.assertLess(west_delta, -0.5)
        self.assertGreater(east_delta, 0.5)
        self.assertGreater(east_delta - west_delta, 2.0)
        self.assertTrue(np.any(result.wave_energy[west_exposed] > result.wave_energy[east_sheltered].mean()))


if __name__ == "__main__":
    unittest.main()
