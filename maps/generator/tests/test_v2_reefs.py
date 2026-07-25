"""Volcanic arcs, hotspot chains, and reef/atoll acceptance tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.grid import CubedSphere
from deeptime.v2.reefs import (
    build_hotspot_chain,
    build_volcanic_arcs,
    grow_reefs,
)
from deeptime.v2.topology import component_labels


class ReefTests(unittest.TestCase):
    def test_atolls_sit_on_drowned_warm_edifices(self) -> None:
        grid = CubedSphere.create(24)
        elevation = np.full(grid.size, -3500.0)
        # Young volcanic island (emergent) and an older drowned edifice nearby.
        young = (np.abs(grid.lon_deg - 20.0) < 4.0) & (np.abs(grid.lat_deg - 5.0) < 4.0)
        drowned = (np.abs(grid.lon_deg + 30.0) < 5.0) & (np.abs(grid.lat_deg - 8.0) < 5.0)
        elevation[young] = 400.0
        elevation[drowned] = -25.0
        # Shallow apron around the young island so fringing reefs can attach.
        valid = grid.neighbors >= 0
        safe = np.where(valid, grid.neighbors, 0)
        apron = (~young) & (elevation < 0.0) & np.any(valid & young[safe], axis=1)
        elevation[apron] = -18.0
        sst = np.full(grid.size, 26.0)
        sst[np.abs(grid.lat_deg) > 30.0] = 10.0
        edifice = young | drowned | apron
        reefs = grow_reefs(grid, elevation, sst, edifice_mask=edifice, sea_level_m=0.0)
        self.assertTrue(np.any(reefs.atoll_mask))
        self.assertTrue(np.all((drowned | apron)[reefs.atoll_mask] | edifice[reefs.atoll_mask]))
        self.assertTrue(np.all(sst[reefs.atoll_mask] >= 18.0))
        self.assertTrue(np.all(elevation[reefs.atoll_mask] < 0.0))
        # Fringing reefs cling beside the emergent edifice in warm photic water.
        near_young = reefs.fringing_mask & np.any(valid & young[safe], axis=1)
        self.assertTrue(np.any(near_young))

    def test_hotspot_chain_ages_increase_monotonically(self) -> None:
        grid = CubedSphere.create(28)
        elevation = np.full(grid.size, -4000.0)
        chain = build_hotspot_chain(
            grid,
            elevation,
            start_lon=-40.0,
            start_lat=12.0,
            azimuth_deg=70.0,
            n_edifices=6,
            spacing_km=280.0,
            seed=3,
        )
        ages = chain.age_ma[chain.edifice_id >= 0]
        order = np.argsort(chain.edifice_id[chain.edifice_id >= 0])
        ages_along = ages[order]
        # Unique edifice mean ages must increase along the chain.
        means = []
        for eid in range(int(chain.edifice_id.max()) + 1):
            cells = chain.edifice_id == eid
            if not np.any(cells):
                continue
            means.append(float(chain.age_ma[cells].mean()))
        self.assertGreaterEqual(len(means), 5)
        self.assertTrue(np.all(np.diff(means) > 0.0))

    def test_archipelago_of_at_least_eight_islands(self) -> None:
        grid = CubedSphere.create(32)
        elevation = np.full(grid.size, -3800.0)
        continental = np.zeros(grid.size)
        memory = {
            "subduction": np.zeros(grid.size),
            "arc": np.zeros(grid.size),
        }
        # Synthetic arc corridor in the western Pacific analogue.
        arc = (
            (grid.lon_deg > 120.0)
            & (grid.lon_deg < 150.0)
            & (np.abs(grid.lat_deg) < 25.0)
        )
        memory["subduction"][arc] = 0.8
        memory["arc"][arc] = 0.7
        arcs = build_volcanic_arcs(grid, elevation, memory, sea_level_m=0.0, seed=9)
        elevation = arcs.elevation_m
        # Add a short hotspot chain for more islands.
        chain = build_hotspot_chain(
            grid,
            elevation,
            start_lon=-150.0,
            start_lat=-10.0,
            azimuth_deg=300.0,
            n_edifices=5,
            spacing_km=220.0,
            seed=11,
        )
        elevation = chain.elevation_m
        land = elevation >= 0.0
        labels = component_labels(grid, land)
        island_ids = [i for i in np.unique(labels) if i >= 0]
        # Count small islands (not a continent-sized mass).
        islands = 0
        for iid in island_ids:
            cells = int((labels == iid).sum())
            if 1 <= cells <= 40:
                islands += 1
        self.assertGreaterEqual(islands, 8)


if __name__ == "__main__":
    unittest.main()
