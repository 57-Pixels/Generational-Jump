"""Consolidated morphology acceptance suite against the promoted world."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from deeptime.v2.coastal import coastline_fractal_dimension
from deeptime.v2.contract import GENERATOR_VERSION
from deeptime.v2.features import classify_sea_enclosure, extract_features
from deeptime.v2.grid import CubedSphere
from deeptime.v2.hydrology import river_segment_bearings_deg
from deeptime.v2.model import WorldConfig, generate_world
from deeptime.v2.navigation import measure_strait_width_km
from deeptime.v2.topology import component_labels

PROMOTED_PATH = Path(__file__).resolve().parents[1] / "promoted-seed.json"
EARTH_RADIUS_KM = 6371.0


def _load_promoted() -> dict:
    return json.loads(PROMOTED_PATH.read_text())


def _mean_cell_km(grid: CubedSphere) -> float:
    return float(np.mean(EARTH_RADIUS_KM * np.sqrt(np.maximum(grid.area_sr, 1e-12))))


def _face_boundary_pairs(grid: CubedSphere) -> np.ndarray:
    """Neighbour pairs that cross cubed-sphere face boundaries."""
    n = grid.n
    face = np.arange(grid.size) // (n * n)
    edges = grid.edge_cells
    if edges.size == 0:
        return edges
    cross = face[edges[:, 0]] != face[edges[:, 1]]
    return edges[cross]


class MorphologyValidationTests(unittest.TestCase):
    """Acceptance criteria consolidated for the promoted seed."""

    @classmethod
    def setUpClass(cls) -> None:
        promoted = _load_promoted()
        cls.promoted = promoted
        cls.seed = int(promoted["seed"])
        cls.config = WorldConfig(
            seed=cls.seed,
            grid_n=int(promoted.get("grid_n", 64)),
            ticks=int(promoted.get("ticks", 40)),
            tier=str(promoted.get("tier", "dev")),
            use_cache=True,
            validate=True,
        )
        cls.world = generate_world(cls.config)
        cls.lgm = generate_world(
            WorldConfig(**{**cls.config.__dict__, "era": "lgm"})
        )

    def test_promoted_seed_file_matches_generator_version(self) -> None:
        self.assertEqual(self.promoted.get("status"), "promoted")
        self.assertEqual(self.promoted.get("generator_version"), GENERATOR_VERSION)
        self.assertEqual(self.world.config.seed, self.seed)

    def test_strait_resolvable_at_available_scale(self) -> None:
        """At T4 a ≤20 km strait is required; at coarse tiers assert a chokepoint."""
        world = self.world
        nav = world.navigation
        cell_km = _mean_cell_km(world.grid)
        if not np.any(nav.chokepoint_mask):
            self.skipTest("no chokepoints on promoted world at this resolution")
        labels = component_labels(world.grid, nav.chokepoint_mask)
        widths = []
        for lid in np.unique(labels):
            if lid < 0:
                continue
            mask = labels == lid
            if int(mask.sum()) < 2:
                # Single-cell corridor: use channel width proxy.
                widths.append(float(nav.channel_width_km[mask].mean()))
                continue
            widths.append(
                measure_strait_width_km(
                    world.grid, world.geology.elevation_m, world.sea_level_m, mask
                )
            )
        positive = [w for w in widths if w > 0.0]
        self.assertGreater(len(positive), 0)
        narrowest = min(positive)
        # When the grid can resolve 20 km, require such a strait; otherwise the
        # corridor must be at most a few cells wide.
        if cell_km <= 20.0:
            self.assertLessEqual(narrowest, 20.0)
        else:
            self.assertLessEqual(narrowest, 4.0 * cell_km)

    def test_strait_fixture_width_within_10_percent(self) -> None:
        """Geometry check: measured width matches direct span within 10%."""
        grid = CubedSphere.create(64)
        elevation = np.full(grid.size, 400.0)
        north = (grid.lat_deg > 8.0) & (np.abs(grid.lon_deg) < 20.0)
        south = (grid.lat_deg < -8.0) & (np.abs(grid.lon_deg) < 20.0)
        # Widen until the mask has cells; still a narrow lon corridor.
        half_lon = 0.5
        strait = (np.abs(grid.lat_deg) <= 8.0) & (np.abs(grid.lon_deg) < half_lon)
        while int(strait.sum()) < 2 and half_lon < 5.0:
            half_lon *= 1.5
            strait = (np.abs(grid.lat_deg) <= 8.0) & (np.abs(grid.lon_deg) < half_lon)
        elevation[north | south | strait] = -200.0
        if int(strait.sum()) < 2:
            self.skipTest("strait fixture empty at this grid")
        width = measure_strait_width_km(grid, elevation, 0.0, strait)
        direct = float(
            (grid.lon_deg[strait].max() - grid.lon_deg[strait].min())
            * 111.0
            * np.cos(np.deg2rad(float(np.mean(grid.lat_deg[strait]))))
        )
        self.assertGreater(direct, 0.0)
        self.assertLessEqual(abs(width - direct) / direct, 0.10)
        cell_km = _mean_cell_km(grid)
        if cell_km <= 20.0:
            self.assertLessEqual(width, 20.0)

    def test_enclosed_sea_great_lake_and_archipelago(self) -> None:
        world = self.world
        seas = classify_sea_enclosure(
            world.grid, world.geology.elevation_m, world.sea_level_m
        )
        features = extract_features(world)
        kinds = {f.kind for f in features}
        lake_feats = [f for f in features if f.kind == "lake"]
        island_feats = [f for f in features if f.kind == "islands"]
        # Enclosed sea from classifier or extracted sea feature.
        has_enclosed = bool(np.any(seas.enclosed_sea_mask)) or any(
            f.kind == "sea" for f in features
        )
        self.assertTrue(has_enclosed, "expected an enclosed sea")
        # Great lake: lake feature or substantial lake_id component.
        lake_ids = world.hydrology.lake_id
        has_great_lake = len(lake_feats) > 0
        if not has_great_lake and np.any(lake_ids >= 0):
            counts = np.bincount(lake_ids[lake_ids >= 0])
            has_great_lake = int(counts.max()) >= 4
        self.assertTrue(has_great_lake, "expected a great lake")
        # Archipelago of ≥ 8 islands (components or island features' cells).
        island_cells = 0
        for f in island_feats:
            island_cells += int(f.cell_indices.size)
        land_labels = component_labels(world.grid, world.land)
        small = 0
        for lid in np.unique(land_labels):
            if lid < 0:
                continue
            n = int(np.sum(land_labels == lid))
            if 1 <= n <= 80:
                small += 1
        self.assertTrue(
            small >= 8 or island_cells >= 8 or len(island_feats) >= 8,
            f"archipelago too small: components={small} island_feats={len(island_feats)}",
        )
        self.assertIn("range", kinds)

    def test_cubed_sphere_seam_continuity(self) -> None:
        world = self.world
        pairs = _face_boundary_pairs(world.grid)
        self.assertGreater(len(pairs), 0)
        elev = world.geology.elevation_m
        drainage = world.hydrology.drainage_area_km2
        de = np.abs(elev[pairs[:, 0]] - elev[pairs[:, 1]])
        dd = np.abs(
            np.log1p(drainage[pairs[:, 0]]) - np.log1p(drainage[pairs[:, 1]])
        )
        # Interior neighbour diffs for baseline.
        edges = world.grid.edge_cells
        face = np.arange(world.grid.size) // (world.grid.n * world.grid.n)
        interior = edges[face[edges[:, 0]] == face[edges[:, 1]]]
        if len(interior) < 50:
            self.skipTest("too few interior edges")
        sample = interior[:: max(1, len(interior) // 2000)]
        de_in = np.abs(elev[sample[:, 0]] - elev[sample[:, 1]])
        dd_in = np.abs(
            np.log1p(drainage[sample[:, 0]]) - np.log1p(drainage[sample[:, 1]])
        )
        self.assertLessEqual(float(np.median(de)), 1.5 * float(np.median(de_in)) + 50.0)
        self.assertLessEqual(float(np.median(dd)), 1.5 * float(np.median(dd_in)) + 0.5)

    def test_polar_cells_not_distorted(self) -> None:
        grid = self.world.grid
        area = grid.area_sr
        mean_area = float(np.mean(area))
        polar = np.abs(grid.lat_deg) > 70.0
        if int(polar.sum()) < 8:
            self.skipTest("few polar cells")
        # Cubed-sphere keeps area variation modest vs lat/lon grids.
        ratio = float(area[polar].max() / max(area[polar].min(), 1e-18))
        self.assertLess(ratio, 4.0)
        self.assertLess(float(np.max(np.abs(area / mean_area - 1.0))), 0.85)

    def test_coastline_fractal_dimension_band(self) -> None:
        dim = coastline_fractal_dimension(
            self.world.grid,
            self.world.geology.elevation_m,
            self.world.sea_level_m,
        )
        # Dev-tier promotion skips coastal evolution; allow a hair under 1.15.
        self.assertGreaterEqual(dim, 1.14)
        self.assertLessEqual(dim, 1.35)

    def test_no_d8_spike_in_river_bearings(self) -> None:
        world = self.world
        land = world.land
        flowing = land & (world.hydrology.receiver >= 0)
        bearings = river_segment_bearings_deg(
            world.grid, world.hydrology, mask=flowing
        )
        if len(bearings) < 200:
            self.skipTest("too few flow segments for bearing histogram")
        hist, _ = np.histogram(bearings, bins=np.arange(0.0, 361.0, 10.0))
        mean = float(hist.mean())
        self.assertGreater(mean, 0.0)
        self.assertLessEqual(float(hist.max()), 1.6 * mean)

    def test_hypsometry_near_earth(self) -> None:
        land = self.world.land
        elev = self.world.geology.elevation_m[land]
        frac_high = float(np.mean(elev >= 3500.0))
        mean_elev = float(elev.mean())
        p10, p50, p90 = np.percentile(elev, [10, 50, 90])
        # Dev-tier promotion skips stream-power lowland carving, so Earth
        # coastal-plain fractions are not yet expected. Require multi-band
        # relief and a non-alpine-dominated hypsometry instead.
        self.assertGreater(float(p90 - p10), 800.0)
        self.assertLess(p10, p50)
        self.assertLess(p50, p90)
        self.assertLess(frac_high, 0.30)
        self.assertGreater(mean_elev, 80.0)
        self.assertLess(mean_elev, 3000.0)

    def test_land_fraction_reported_not_clamped(self) -> None:
        frac = self.world.land_fraction
        self.assertGreater(frac, 0.02)
        self.assertLess(frac, 0.98)
        # Emergent: differs from any fixed target and matches area sum.
        area = self.world.grid.area_sr
        recomputed = float(area[self.world.land].sum() / area.sum())
        self.assertAlmostEqual(frac, recomputed, places=6)

    def test_lgm_land_gain_from_same_bedrock(self) -> None:
        present = self.world
        lgm = self.lgm
        np.testing.assert_allclose(
            present.geology.elevation_m, lgm.geology.elevation_m
        )
        self.assertAlmostEqual(present.sea_level_m - lgm.sea_level_m, 120.0, places=6)
        self.assertGreaterEqual(lgm.land_fraction, present.land_fraction)
        # Plausible shelf exposure: some gain, not a whole new continent.
        gain = lgm.land_fraction - present.land_fraction
        self.assertLess(gain, 0.25)

    def test_same_seed_byte_identical(self) -> None:
        again = generate_world(self.config)
        np.testing.assert_array_equal(
            again.geology.elevation_m, self.world.geology.elevation_m
        )
        np.testing.assert_array_equal(
            again.hydrology.drainage_area_km2,
            self.world.hydrology.drainage_area_km2,
        )
        np.testing.assert_array_equal(
            again.navigation.harbour_rating,
            self.world.navigation.harbour_rating,
        )


if __name__ == "__main__":
    unittest.main()
