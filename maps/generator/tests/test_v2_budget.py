"""Memory budgets and bit-identity for climate/hydrology hot paths."""

from __future__ import annotations

import os
import resource
import unittest

import numpy as np

from deeptime.v2.climate import (
    _ocean_influence,
    _upstream_neighbors,
    _wind_vectors,
    compute_climate,
)
from deeptime.v2.grid import CubedSphere
from deeptime.v2.hydrology import _priority_flood, _receivers, compute_hydrology


def _legacy_ocean_influence(
    grid: CubedSphere, ocean: np.ndarray, steps: int = 24
) -> np.ndarray:
    influence = ocean.astype(np.float64)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    for _ in range(steps):
        neighbor_max = np.where(valid, influence[safe], 0.0).max(axis=1)
        influence = np.maximum(influence, neighbor_max * 0.86)
    return np.clip(influence, 0, 1)


def _legacy_upstream_neighbors(grid: CubedSphere, wind: np.ndarray) -> np.ndarray:
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    neighbor_xyz = grid.xyz[safe]
    direction = grid.xyz[:, None, :] - neighbor_xyz
    radial = np.einsum("mki,mi->mk", direction, grid.xyz)
    direction -= radial[:, :, None] * grid.xyz[:, None, :]
    direction /= np.maximum(np.linalg.norm(direction, axis=2, keepdims=True), 1e-12)
    alignment = np.einsum("mki,mi->mk", direction, wind)
    alignment = np.where(valid, alignment, -np.inf)
    chosen = np.argmax(alignment, axis=1)
    return safe[np.arange(grid.size), chosen]


def _legacy_receivers(
    grid: CubedSphere,
    filled: np.ndarray,
    land: np.ndarray,
    parent: np.ndarray,
) -> np.ndarray:
    receiver = np.full(grid.size, -1, dtype=np.int32)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    for cell in np.flatnonzero(land):
        neighbors = safe[cell, valid[cell]]
        wet = neighbors[~land[neighbors]]
        if len(wet):
            receiver[cell] = -1
            continue
        lower = neighbors[filled[neighbors] < filled[cell] - 1e-7]
        if len(lower):
            receiver[cell] = int(lower[np.argmin(filled[lower])])
        else:
            receiver[cell] = int(parent[cell])
    return receiver


class ClimateHydrologyIdentityTests(unittest.TestCase):
    def test_ocean_influence_matches_legacy(self) -> None:
        for n in (32, 64):
            with self.subTest(n=n):
                grid = CubedSphere.create(n)
                ocean = grid.xyz[:, 0] < 0.1
                got = _ocean_influence(grid, ocean)
                expected = _legacy_ocean_influence(grid, ocean)
                np.testing.assert_allclose(got, expected, rtol=0, atol=0)

    def test_upstream_neighbors_matches_legacy(self) -> None:
        for n in (32, 64):
            with self.subTest(n=n):
                grid = CubedSphere.create(n)
                wind = _wind_vectors(grid)
                got = _upstream_neighbors(grid, wind)
                expected = _legacy_upstream_neighbors(grid, wind)
                np.testing.assert_array_equal(got, expected)

    def test_receivers_match_legacy(self) -> None:
        for n in (32, 64):
            with self.subTest(n=n):
                grid = CubedSphere.create(n)
                elevation = np.full(grid.size, -3000.0)
                land = grid.xyz[:, 0] > 0.0
                elevation[land] = 200.0 + 800.0 * grid.xyz[land, 0]
                filled, parent, _ = _priority_flood(grid, elevation, land)
                got = _receivers(grid, filled, land, parent, stochastic=False)
                expected = _legacy_receivers(grid, filled, land, parent)
                np.testing.assert_array_equal(got, expected)


class BudgetTests(unittest.TestCase):
    # Measured on the build host after task 4 (4 vCPU / 15 GB):
    #   n=256: delta ≈ 229 MB, peak ≈ 462 MB, ~2.1 s
    #   n=512: delta ≈ 786 MB, peak ≈ 1642 MB, ~10 s
    CLIMATE_HYDRO_PEAK_MB = 900.0

    def test_climate_hydrology_budget_at_256(self) -> None:
        CubedSphere.create.cache_clear()
        grid = CubedSphere.create(256)
        elevation = np.full(grid.size, -2800.0)
        land = grid.xyz[:, 2] > -0.15
        elevation[land] = 120.0 + 1500.0 * np.clip(grid.xyz[land, 2], 0, 1)

        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        climate = compute_climate(grid, elevation, 0.0)
        hydro = compute_hydrology(grid, elevation, 0.0, climate)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        delta = peak - before
        # Comment the measured number into failures for easy regression notes.
        self.assertLess(
            delta,
            self.CLIMATE_HYDRO_PEAK_MB,
            msg=f"climate+hydro RSS delta {delta:.0f} MB (peak {peak:.0f})",
        )
        self.assertTrue(np.isfinite(climate.precipitation_mm_yr).all())
        self.assertTrue(np.isfinite(hydro.discharge_m3_s).all())

    @unittest.skipUnless(os.environ.get("DEEPTIME_SLOW"), "slow")
    def test_climate_hydrology_peak_under_3gb_at_512(self) -> None:
        CubedSphere.create.cache_clear()
        grid = CubedSphere.create(512)
        elevation = np.full(grid.size, -2800.0)
        land = grid.xyz[:, 0] > 0.0
        elevation[land] = 250.0
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        climate = compute_climate(grid, elevation, 0.0)
        compute_hydrology(grid, elevation, 0.0, climate)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        self.assertLess(peak, 3000.0, msg=f"peak RSS {peak:.0f} MB (before {before:.0f})")


if __name__ == "__main__":
    unittest.main()
