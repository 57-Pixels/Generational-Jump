"""River GeoJSON export: continuous polylines to the coast."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.export import _river_geojson
from deeptime.v2.model import WorldConfig, generate_world


class RiverExportTests(unittest.TestCase):
    def test_rivers_are_polylines_reaching_ocean(self) -> None:
        world = generate_world(
            WorldConfig(seed=42, grid_n=24, ticks=16, export_width=128, export_height=64)
        )
        # Every river cell walks receivers to the ocean or a lake/endorheic sink.
        river = world.hydrology.river_mask
        receiver = world.hydrology.receiver
        lake_id = world.hydrology.lake_id
        endorheic = world.hydrology.endorheic_mask
        if endorheic is None:
            endorheic = np.zeros(world.grid.size, dtype=bool)
        land = world.land
        for start in np.flatnonzero(river)[::5]:
            current = int(start)
            seen: set[int] = set()
            reached_sink = False
            for _ in range(world.grid.size):
                if current in seen:
                    break
                seen.add(current)
                if lake_id[current] >= 0 or endorheic[current]:
                    reached_sink = True
                    break
                downstream = int(receiver[current])
                if downstream < 0:
                    neighbors = world.grid.neighbors[current]
                    neighbors = neighbors[neighbors >= 0]
                    reached_sink = bool(np.any(~land[neighbors]))
                    break
                if not river[downstream]:
                    break
                current = downstream
            self.assertTrue(
                reached_sink, msg=f"river cell {start} does not reach ocean/lake"
            )

        geo = _river_geojson(world)
        self.assertGreater(len(geo["features"]), 0)
        lon = world.grid.lon_deg
        lat = world.grid.lat_deg

        for feature in geo["features"]:
            coords = feature["geometry"]["coordinates"]
            self.assertEqual(feature["geometry"]["type"], "LineString")
            self.assertGreaterEqual(len(coords), 2)
            for a, b in zip(coords, coords[1:]):
                self.assertLess(abs(a[0] - b[0]), 180.0)
            if feature["properties"].get("role") != "mouth":
                continue
            end_lon, end_lat = coords[-1]
            d2 = (lon - end_lon) ** 2 + (lat - end_lat) ** 2
            end_cell = int(np.argmin(d2))
            neighbors = world.grid.neighbors[end_cell]
            neighbors = neighbors[neighbors >= 0]
            touches_ocean = (not land[end_cell]) or np.any(~land[neighbors])
            inland_sink = bool(lake_id[end_cell] >= 0 or endorheic[end_cell])
            self.assertTrue(
                touches_ocean or inland_sink,
                msg=f"mouth at {coords[-1]} not coastal or lake",
            )

    def test_no_orphaned_two_point_only_network(self) -> None:
        world = generate_world(
            WorldConfig(seed=7, grid_n=20, ticks=12, export_width=128, export_height=64)
        )
        geo = _river_geojson(world)
        lengths = [len(f["geometry"]["coordinates"]) for f in geo["features"]]
        self.assertTrue(any(length >= 3 for length in lengths))


if __name__ == "__main__":
    unittest.main()
