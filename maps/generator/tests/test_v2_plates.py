import math
import unittest

import numpy as np

from deeptime.v2.grid import CubedSphere
from deeptime.v2.plates import (
    BOUNDARY_CONVERGENT,
    BOUNDARY_DIVERGENT,
    PlateModel,
    rodrigues_rotate,
)


class CubedSphereTests(unittest.TestCase):
    def test_cell_areas_sum_to_sphere(self) -> None:
        grid = CubedSphere.create(12)
        self.assertAlmostEqual(float(grid.area_sr.sum()), 4.0 * math.pi, places=8)

    def test_neighbors_are_reciprocal(self) -> None:
        grid = CubedSphere.create(10)
        adjacency = [set(row[row >= 0].tolist()) for row in grid.neighbors]
        for cell, neighbors in enumerate(adjacency):
            for neighbor in neighbors:
                self.assertIn(cell, adjacency[neighbor])

    def test_rodrigues_preserves_distance_and_unit_norm(self) -> None:
        points = np.array([[1.0, 0.0, 0.0], [0.2, 0.8, 0.4]])
        points /= np.linalg.norm(points, axis=1, keepdims=True)
        before = float(points[0] @ points[1])
        rotated = rodrigues_rotate(points, np.array([0.0, 0.0, 1.0]), 0.7)
        self.assertAlmostEqual(float(rotated[0] @ rotated[1]), before, places=12)
        np.testing.assert_allclose(np.linalg.norm(rotated, axis=1), 1.0, atol=1e-12)


class PlateKinematicsTests(unittest.TestCase):
    def test_voronoi_plates_are_connected(self) -> None:
        grid = CubedSphere.create(14)
        model = PlateModel.initialize(grid, n_plates=9, seed=7)
        model.assert_connected(grid)

    def test_head_on_and_separating_boundaries_have_signed_class(self) -> None:
        grid = CubedSphere.create(10)
        model = PlateModel.two_plate_fixture(grid, opening_km_ma=-20.0)
        boundary = model.boundaries(grid)
        active = boundary.kind[boundary.kind != 0]
        self.assertGreater(active.size, 0)
        self.assertTrue(np.any(active == BOUNDARY_CONVERGENT))

        separating = PlateModel.two_plate_fixture(grid, opening_km_ma=20.0)
        boundary = separating.boundaries(grid)
        active = boundary.kind[boundary.kind != 0]
        self.assertTrue(np.any(active == BOUNDARY_DIVERGENT))

    def test_advancing_recomputes_labels_without_fragmenting(self) -> None:
        grid = CubedSphere.create(12)
        model = PlateModel.initialize(grid, n_plates=8, seed=42)
        for _ in range(8):
            model.advance(grid, dt_ma=5.0)
            model.assert_connected(grid)


if __name__ == "__main__":
    unittest.main()
