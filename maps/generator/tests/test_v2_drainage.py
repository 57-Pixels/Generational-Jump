"""Drainage network, lakes, and hypsometry acceptance tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import compute_climate
from deeptime.v2.grid import CubedSphere
from deeptime.v2.hydrology import compute_hydrology, river_segment_bearings_deg
from deeptime.v2.surface import evolve_surface


def _continent_fixture(grid: CubedSphere) -> np.ndarray:
    elevation = np.full(grid.size, -3200.0)
    land = (np.abs(grid.lon_deg) < 70.0) & (np.abs(grid.lat_deg) < 55.0)
    coastal = np.clip((70.0 - np.abs(grid.lon_deg[land])) / 70.0, 0.0, 1.0)
    lon = grid.lon_deg[land]
    lat = grid.lat_deg[land]
    elevation[land] = 40.0 + 420.0 * coastal
    # Scattered peaks create radial drainage with diverse bearings.
    peaks = (
        (0.0, 10.0, 700.0),
        (-40.0, -15.0, 650.0),
        (35.0, 25.0, 720.0),
        (-20.0, 35.0, 580.0),
        (25.0, -30.0, 640.0),
        (-50.0, 20.0, 600.0),
        (50.0, -5.0, 680.0),
        (5.0, -40.0, 610.0),
    )
    for plon, plat, height in peaks:
        dist2 = ((lon - plon) / 18.0) ** 2 + ((lat - plat) / 14.0) ** 2
        elevation[land] += height * np.exp(-dist2)
    rng = np.random.default_rng(21)
    elevation[land] += rng.normal(0.0, 40.0, size=int(land.sum()))
    basin = land & (np.abs(grid.lon_deg - 10.0) < 12.0) & (np.abs(grid.lat_deg - 20.0) < 10.0)
    elevation[basin] -= 180.0
    arid_sink = land & (np.abs(grid.lon_deg + 35.0) < 8.0) & (np.abs(grid.lat_deg - 28.0) < 8.0)
    elevation[arid_sink] -= 220.0
    return elevation


class DrainageNetworkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = CubedSphere.create(24)
        self.elevation = _continent_fixture(self.grid)
        self.climate = compute_climate(self.grid, self.elevation, 0.0)
        # Wet the inland basin so it becomes a lake; dry the arid sink.
        basin = (
            (np.abs(self.grid.lon_deg - 10.0) < 12.0)
            & (np.abs(self.grid.lat_deg - 20.0) < 10.0)
        )
        sink = (
            (np.abs(self.grid.lon_deg + 35.0) < 8.0)
            & (np.abs(self.grid.lat_deg - 28.0) < 8.0)
        )
        self.climate.precipitation_mm_yr[basin] = 1400.0
        self.climate.pet_mm_yr[basin] = 700.0
        self.climate.precipitation_mm_yr[sink] = 40.0
        self.climate.pet_mm_yr[sink] = 1800.0

    def test_drainage_acyclic_and_terminates_at_ocean_or_lake(self) -> None:
        result = evolve_surface(
            self.grid, self.elevation, 0.0, self.climate, iterations=12, seed=7
        )
        hydro = result.hydrology
        land = result.elevation_m >= 0.0
        river_cells = np.flatnonzero(hydro.river_mask & land)
        self.assertGreater(len(river_cells), 20)
        lake_or_ocean = (hydro.lake_id >= 0) | (~land)
        for start in river_cells[:: max(1, len(river_cells) // 40)]:
            seen: set[int] = set()
            current = int(start)
            for _ in range(self.grid.size + 2):
                if current in seen:
                    self.fail(f"cycle at {current}")
                seen.add(current)
                nxt = int(hydro.receiver[current])
                if nxt < 0:
                    # Ocean mouth or explicit sink.
                    break
                if hydro.lake_id[current] >= 0 and (
                    hydro.receiver[current] < 0 or hydro.lake_id[nxt] != hydro.lake_id[current]
                ):
                    break
                if result.endorheic_mask[current]:
                    break
                current = nxt
            else:
                self.fail("receiver chain did not terminate")
            terminal = current
            self.assertTrue(
                (hydro.receiver[terminal] < 0)
                or (hydro.lake_id[terminal] >= 0)
                or bool(result.endorheic_mask[terminal])
                or lake_or_ocean[terminal],
                msg=f"river terminated on non-sink cell {terminal}",
            )

    def test_no_grid_aligned_drainage_spike(self) -> None:
        # Larger grid + all draining land cells → enough samples for a stable
        # 10° histogram (the 1.6× mean rule is too tight for ~100 segments).
        grid = CubedSphere.create(32)
        elevation = _continent_fixture(grid)
        climate = compute_climate(grid, elevation, 0.0)
        basin = (
            (np.abs(grid.lon_deg - 10.0) < 12.0)
            & (np.abs(grid.lat_deg - 20.0) < 10.0)
        )
        sink = (
            (np.abs(grid.lon_deg + 35.0) < 8.0)
            & (np.abs(grid.lat_deg - 28.0) < 8.0)
        )
        climate.precipitation_mm_yr[basin] = 1400.0
        climate.pet_mm_yr[basin] = 700.0
        climate.precipitation_mm_yr[sink] = 40.0
        climate.pet_mm_yr[sink] = 1800.0
        result = evolve_surface(
            grid, elevation, 0.0, climate, iterations=12, seed=11
        )
        land = result.elevation_m >= 0.0
        flowing = land & (result.hydrology.receiver >= 0)
        bearings = river_segment_bearings_deg(
            grid, result.hydrology, mask=flowing
        )
        if len(bearings) < 200:
            self.skipTest("too few flow segments for bearing histogram")
        hist, _ = np.histogram(bearings, bins=np.arange(0.0, 361.0, 10.0))
        mean = float(hist.mean())
        self.assertGreater(mean, 0.0)
        self.assertLessEqual(float(hist.max()), 1.6 * mean)

    def test_lakes_and_endorheic_basin_exist(self) -> None:
        result = evolve_surface(
            self.grid, self.elevation, 0.0, self.climate, iterations=12, seed=3
        )
        hydro = result.hydrology
        self.assertTrue(np.any(hydro.lake_id >= 0))
        self.assertTrue(np.any(result.endorheic_mask))

    def test_hypsometry_near_earth(self) -> None:
        result = evolve_surface(
            self.grid, self.elevation, 0.0, self.climate, iterations=24, seed=5
        )
        land = result.elevation_m >= 0.0
        elev = result.elevation_m[land]
        # Earth-ish land hypsometry bands (loose tolerances for a synthetic continent).
        frac_low = float(np.mean(elev < 200.0))
        frac_mid = float(np.mean((elev >= 200.0) & (elev < 1500.0)))
        frac_high = float(np.mean(elev >= 3000.0))
        mean_elev = float(elev.mean())
        self.assertGreater(frac_low, 0.08)
        self.assertGreater(frac_mid, 0.35)
        self.assertLess(frac_high, 0.12)
        self.assertGreater(mean_elev, 150.0)
        self.assertLess(mean_elev, 1600.0)


if __name__ == "__main__":
    unittest.main()
