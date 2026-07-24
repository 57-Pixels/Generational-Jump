import math
import unittest
from collections import deque

import numpy as np

from deeptime.v2.geology import (
    CONTINENT_MIN_KM,
    GeologyConfig,
    _apply_crust_events,
    _seed_crust_fields,
)
from deeptime.v2.grid import CubedSphere
from deeptime.v2.model import WorldConfig, generate_world
from deeptime.v2.plates import PlateModel


def _isoperimetric(mask: np.ndarray) -> float:
    area = float(mask.sum())
    if area < 20:
        return 0.0
    er = np.logical_xor(mask, np.roll(mask, 1, 0)) | np.logical_xor(
        mask, np.roll(mask, 1, 1)
    )
    perimeter = float(er.sum())
    return (4.0 * math.pi * area) / (perimeter * perimeter + 1e-9)


class CrustMorphologyTests(unittest.TestCase):
    def test_seed_cores_are_anisotropic_not_round_caps(self) -> None:
        grid = CubedSphere.create(16)
        plates = PlateModel.initialize(grid, n_plates=8, seed=3)
        rng = np.random.default_rng(3)
        thickness, _ids, _age = _seed_crust_fields(
            grid, plates, GeologyConfig(seed=3, n_continents=5), rng
        )
        land = thickness >= CONTINENT_MIN_KM
        rgb = grid.to_equirect(land.astype(np.float64)[:, None], 180, 90)[:, :, 0] > 0.5
        circs = []
        h, w = rgb.shape
        visited = np.zeros_like(rgb, dtype=bool)
        for y in range(h):
            for x in range(w):
                if not rgb[y, x] or visited[y, x]:
                    continue
                q = deque([(y, x)])
                visited[y, x] = True
                cells = []
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for ny, nx in (
                        (cy - 1, cx),
                        (cy + 1, cx),
                        (cy, (cx - 1) % w),
                        (cy, (cx + 1) % w),
                    ):
                        if 0 <= ny < h and rgb[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            q.append((ny, nx))
                if len(cells) < 40:
                    continue
                component = np.zeros_like(rgb, dtype=bool)
                for cy, cx in cells:
                    component[cy, cx] = True
                circs.append(_isoperimetric(component))
        self.assertTrue(circs)
        self.assertLess(float(np.mean(circs)), 0.45)

    def test_rift_thins_and_collision_thickens(self) -> None:
        grid = CubedSphere.create(10)
        thickness = np.full(grid.size, 35.0)
        continent_id = np.zeros(grid.size, dtype=np.int32)
        basement_age = np.full(grid.size, 1000.0)
        current = {
            name: np.zeros(grid.size)
            for name in (
                "ridge",
                "continental_rift",
                "subduction",
                "arc",
                "collision",
                "suture",
                "transform",
                "passive_margin",
                "hydrothermal",
                "mafic",
                "alkaline",
                "exhumation",
            )
        }
        half = grid.size // 2
        current["collision"][:half] = 1.0
        current["continental_rift"][half:] = 1.0
        rng = np.random.default_rng(0)
        out, _ids, _age = _apply_crust_events(
            thickness, continent_id, basement_age, current, grid, dt_ma=10.0, rng=rng
        )
        self.assertGreater(float(out[:half].mean()), float(thickness[:half].mean()))
        self.assertLess(float(out[half:].mean()), float(thickness[half:].mean()))

    def test_land_fraction_is_emergent_not_clamped(self) -> None:
        fractions = []
        for seed in (2, 5, 11, 17, 23):
            world = generate_world(
                WorldConfig(
                    seed=seed, grid_n=12, ticks=12, export_width=64, export_height=32
                )
            )
            fractions.append(world.land_fraction)
            self.assertGreater(world.land_fraction, 0.02)
            self.assertLess(world.land_fraction, 0.98)
            self.assertAlmostEqual(world.sea_level_m, 0.0, places=6)
        self.assertGreater(max(fractions) - min(fractions), 0.01)


if __name__ == "__main__":
    unittest.main()
