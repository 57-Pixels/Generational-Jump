"""Grid neighbour construction scaling and correctness."""

from __future__ import annotations

import os
import resource
import unittest

import numpy as np

from deeptime.v2.grid import CubedSphere, _face_vectors


def _legacy_neighbors(n: int) -> np.ndarray:
    """Oracle: the pre-task-2 set-based adjacency builder."""
    delta = (np.pi / 2.0) / n
    centers = -np.pi / 4.0 + (np.arange(n) + 0.5) * delta
    alpha, beta = np.meshgrid(centers, centers, indexing="xy")
    source = np.arange(6 * n * n, dtype=np.int32).reshape(6, n, n)
    pairs: list[np.ndarray] = []
    for di, dj in (
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ):
        aa = alpha + di * delta
        bb = beta + dj * delta
        for face in range(6):
            target_xyz = _face_vectors(face, aa, bb).reshape(-1, 3)
            target = CubedSphere.indices_for_xyz_static(target_xyz, n)
            src = source[face].ravel()
            pair = np.stack((np.minimum(src, target), np.maximum(src, target)), axis=1)
            pairs.append(pair[pair[:, 0] != pair[:, 1]])
    edge_cells = np.unique(np.concatenate(pairs, axis=0), axis=0).astype(np.int32)
    adjacency: list[set[int]] = [set() for _ in range(6 * n * n)]
    for left, right in edge_cells:
        adjacency[int(left)].add(int(right))
        adjacency[int(right)].add(int(left))
    max_degree = max(len(items) for items in adjacency)
    neighbors = np.full((6 * n * n, max_degree), -1, dtype=np.int32)
    for cell, items in enumerate(adjacency):
        ordered = sorted(items)
        neighbors[cell, : len(ordered)] = ordered
    return neighbors


def _row_sets(neighbors: np.ndarray) -> list[frozenset[int]]:
    return [frozenset(int(x) for x in row if x >= 0) for row in neighbors]


class GridScalingTests(unittest.TestCase):
    def test_neighbors_match_legacy_and_are_symmetric(self) -> None:
        for n in (4, 8, 16, 32):
            with self.subTest(n=n):
                CubedSphere.create.cache_clear()
                grid = CubedSphere.create(n)
                legacy = _row_sets(_legacy_neighbors(n))
                got = _row_sets(grid.neighbors)
                self.assertEqual(got, legacy)
                for a, row in enumerate(got):
                    for b in row:
                        self.assertIn(a, got[b], f"n={n}: asymmetric {a}->{b}")

    def test_degree_distribution_is_exactly_24_sevens(self) -> None:
        for n in (8, 16, 32, 64):
            with self.subTest(n=n):
                CubedSphere.create.cache_clear()
                grid = CubedSphere.create(n)
                degree = (grid.neighbors >= 0).sum(axis=1)
                sevens = int((degree == 7).sum())
                eights = int((degree == 8).sum())
                self.assertEqual(sevens, 24)
                self.assertEqual(eights, grid.size - 24)
                self.assertTrue(np.all((degree == 7) | (degree == 8)))

    def test_lon_lat_and_edge_cells_lazy_but_correct(self) -> None:
        CubedSphere.create.cache_clear()
        grid = CubedSphere.create(16)
        expected_lon = np.rad2deg(np.arctan2(grid.xyz[:, 1], grid.xyz[:, 0]))
        expected_lat = np.rad2deg(np.arcsin(np.clip(grid.xyz[:, 2], -1.0, 1.0)))
        np.testing.assert_allclose(grid.lon_deg, expected_lon)
        np.testing.assert_allclose(grid.lat_deg, expected_lat)
        # Undirected unique pairs; every neighbour relation appears once.
        edges = grid.edge_cells
        self.assertEqual(edges.shape[1], 2)
        self.assertTrue(np.all(edges[:, 0] < edges[:, 1]))
        adjacency = _row_sets(grid.neighbors)
        edge_set = {frozenset((int(a), int(b))) for a, b in edges}
        expected = {
            frozenset((a, b)) for a, row in enumerate(adjacency) for b in row if a < b
        }
        self.assertEqual(edge_set, expected)

    @unittest.skipUnless(os.environ.get("DEEPTIME_SLOW"), "slow")
    def test_create_1024_within_budget(self) -> None:
        CubedSphere.create.cache_clear()
        import time

        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        t0 = time.perf_counter()
        grid = CubedSphere.create(1024)
        elapsed = time.perf_counter() - t0
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        self.assertEqual(grid.size, 6 * 1024 * 1024)
        self.assertLess(elapsed, 60.0)
        self.assertLess(peak - before + before, 2500.0)  # absolute peak < 2.5 GB
        self.assertLess(peak, 2500.0)


if __name__ == "__main__":
    unittest.main()
