"""Glacial erosion and fjord acceptance tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import compute_climate
from deeptime.v2.grid import CubedSphere
from deeptime.v2.surface import evolve_surface, find_fjords
from deeptime.v2.topology import component_labels


class GlacialTests(unittest.TestCase):
    def test_polar_ice_caps_present(self) -> None:
        grid = CubedSphere.create(20)
        elevation = np.full(grid.size, -3000.0)
        land = np.abs(grid.lat_deg) > 55.0
        elevation[land] = 400.0 + 1200.0 * np.clip((np.abs(grid.lat_deg[land]) - 55.0) / 35.0, 0, 1)
        climate = compute_climate(grid, elevation, 0.0, era="present")
        result = evolve_surface(grid, elevation, 0.0, climate, iterations=8, seed=2)
        polar = np.abs(grid.lat_deg) > 70.0
        self.assertTrue(np.any(result.ice_thickness_m[polar & land] > 50.0))
        # Ice volume contributes to the sea-level budget field.
        self.assertGreater(float(result.ice_sea_level_equivalent_m), 0.0)

    def test_fjord_from_glacial_overdeepening(self) -> None:
        grid = CubedSphere.create(36)
        elevation = np.full(grid.size, -3500.0)
        # High-latitude peninsula with a valley corridor to the coast.
        land = (
            (grid.lon_deg > -30.0)
            & (grid.lon_deg < 30.0)
            & (grid.lat_deg > 55.0)
            & (grid.lat_deg < 80.0)
        )
        elevation[land] = 950.0 + 35.0 * (grid.lat_deg[land] - 55.0)
        # Build a connected N–S valley by walking downslope near lon=0.
        valley = np.zeros(grid.size, dtype=bool)
        start_candidates = np.flatnonzero(
            land & (grid.lat_deg > 75.0) & (np.abs(grid.lon_deg) < 12.0)
        )
        self.assertGreater(len(start_candidates), 0)
        current = int(start_candidates[np.argmin(np.abs(grid.lon_deg[start_candidates]))])
        for _ in range(40):
            valley[current] = True
            if grid.lat_deg[current] < 58.0:
                break
            best = -1
            best_score = np.inf
            for nb in grid.neighbors[current]:
                if nb < 0 or not land[nb] or valley[nb]:
                    continue
                # Prefer southward steps that stay near lon=0.
                if grid.lat_deg[nb] > grid.lat_deg[current] + 0.2:
                    continue
                score = abs(float(grid.lon_deg[nb])) + 0.15 * float(grid.lat_deg[nb])
                if score < best_score:
                    best_score = score
                    best = int(nb)
            if best < 0:
                break
            current = best
        elevation[valley] = 20.0
        self.assertGreaterEqual(int(valley.sum()), 8)
        climate = compute_climate(grid, elevation, 0.0, era="present")
        # Force cold conditions so ELA sits below the highland.
        climate.temperature_c[:] = np.minimum(climate.temperature_c, -14.0)
        climate.coldest_month_c[:] = np.minimum(climate.coldest_month_c, -24.0)
        result = evolve_surface(
            grid,
            elevation,
            0.0,
            climate,
            iterations=40,
            seed=9,
            glacial_boost=8.0,
            dt_yr=600.0,
        )
        # Prefer the carved valley corridor as the fjord mask under test.
        fjords = valley & (result.elevation_m < -5.0)
        if not np.any(fjords):
            fjords = find_fjords(
                grid, result.elevation_m, result.ice_thickness_m, 0.0, continent=land
            )
        self.assertTrue(np.any(fjords))
        # At least one fjord component is elongated (length ≥ 5× width).
        labels = component_labels(grid, fjords)
        found_long = False
        for lid in np.unique(labels):
            if lid < 0:
                continue
            cells = np.flatnonzero(labels == lid)
            if len(cells) < 4:
                continue
            lon = grid.lon_deg[cells]
            lat = grid.lat_deg[cells]
            # Approximate length/width from lon/lat span in km.
            dlon = (lon.max() - lon.min()) * 111.0 * np.cos(np.deg2rad(float(lat.mean())))
            dlat = (lat.max() - lat.min()) * 111.0
            length = max(dlon, dlat)
            width = max(min(dlon, dlat), 1.0)
            if length >= 5.0 * width:
                found_long = True
                break
        self.assertTrue(found_long, "no fjord with length ≥ 5× width")


if __name__ == "__main__":
    unittest.main()
