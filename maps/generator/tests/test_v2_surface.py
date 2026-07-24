import unittest

import numpy as np

from deeptime.v2.climate import compute_climate
from deeptime.v2.environment import compute_environment
from deeptime.v2.grid import CubedSphere
from deeptime.v2.hydrology import compute_hydrology


class SurfaceLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = CubedSphere.create(12)
        self.elevation = np.full(self.grid.size, -3000.0)
        self.land = self.grid.xyz[:, 0] > 0.0
        self.elevation[self.land] = 250.0

    def test_climate_has_latitude_and_lapse_rate(self) -> None:
        climate = compute_climate(self.grid, self.elevation, sea_level_m=0.0)
        equator = np.abs(self.grid.lat_deg) < 8
        poles = np.abs(self.grid.lat_deg) > 65
        self.assertGreater(float(climate.temperature_c[equator].mean()), float(climate.temperature_c[poles].mean()))

        high = self.elevation.copy()
        high[self.land] += 2500.0
        high_climate = compute_climate(self.grid, high, sea_level_m=0.0)
        self.assertLess(float(high_climate.temperature_c[self.land].mean()), float(climate.temperature_c[self.land].mean()))

    def test_ocean_is_not_rendered_as_solid_polar_white(self) -> None:
        climate = compute_climate(self.grid, self.elevation, sea_level_m=0.0)
        polar_ocean = (~self.land) & (np.abs(self.grid.lat_deg) > 65)
        self.assertTrue(np.all(climate.sea_ice_fraction[polar_ocean] < 1.0))

    def test_hydrology_receiver_chains_reach_ocean(self) -> None:
        # Tilt the synthetic hemisphere toward its ocean edge.
        elevation = self.elevation.copy()
        elevation[self.land] += 800.0 * self.grid.xyz[self.land, 0]
        climate = compute_climate(self.grid, elevation, sea_level_m=0.0)
        hydro = compute_hydrology(self.grid, elevation, 0.0, climate)
        for start in np.flatnonzero(self.land)[::20]:
            seen: set[int] = set()
            current = int(start)
            for _ in range(self.grid.size):
                if current < 0:
                    break
                self.assertNotIn(current, seen)
                seen.add(current)
                current = int(hydro.receiver[current])
            else:
                self.fail("receiver chain did not terminate")

    def test_floodplain_is_more_fertile_than_high_ridge(self) -> None:
        elevation = self.elevation.copy()
        elevation[self.land] += 1200.0 * np.abs(self.grid.xyz[self.land, 2])
        climate = compute_climate(self.grid, elevation, 0.0)
        hydro = compute_hydrology(self.grid, elevation, 0.0, climate)
        env = compute_environment(
            self.grid,
            elevation,
            0.0,
            continental=np.where(self.land, 1.0, 0.0),
            orogeny=np.clip(elevation / 2000.0, 0, 1),
            climate=climate,
            hydrology=hydro,
        )
        river_land = self.land & (hydro.drainage_area_km2 > np.percentile(hydro.drainage_area_km2[self.land], 80))
        ridge = self.land & (elevation > np.percentile(elevation[self.land], 80))
        self.assertGreater(float(env.soil_fertility[river_land].mean()), float(env.soil_fertility[ridge].mean()))


if __name__ == "__main__":
    unittest.main()
