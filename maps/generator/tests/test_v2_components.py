"""Connected-component labelling on the cubed sphere."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.grid import CubedSphere
from deeptime.v2.topology import component_labels


def _legacy_components(grid: CubedSphere, mask: np.ndarray) -> list[np.ndarray]:
    mask = np.asarray(mask, dtype=bool)
    seen = np.zeros(grid.size, dtype=bool)
    result: list[np.ndarray] = []
    for start in np.flatnonzero(mask):
        if seen[start]:
            continue
        stack = [int(start)]
        seen[start] = True
        cells: list[int] = []
        while stack:
            cell = stack.pop()
            cells.append(cell)
            for neighbor in grid.neighbors[cell]:
                if neighbor < 0:
                    continue
                n = int(neighbor)
                if mask[n] and not seen[n]:
                    seen[n] = True
                    stack.append(n)
        result.append(np.asarray(cells, dtype=np.int32))
    return sorted(result, key=len, reverse=True)


def _legacy_labels(grid: CubedSphere, mask: np.ndarray) -> np.ndarray:
    labels = np.full(grid.size, -1, dtype=np.int32)
    for label, cells in enumerate(_legacy_components(grid, mask)):
        labels[cells] = label
    return labels


class ComponentLabelTests(unittest.TestCase):
    def test_matches_legacy_dfs_on_world_mask(self) -> None:
        grid = CubedSphere.create(32)
        mask = grid.xyz[:, 0] > 0.15
        got = component_labels(grid, mask)
        expected = _legacy_labels(grid, mask)
        np.testing.assert_array_equal(got, expected)

    def test_label_zero_is_largest_component(self) -> None:
        grid = CubedSphere.create(24)
        # Two separated caps of different sizes.
        mask = (grid.xyz[:, 0] > 0.55) | (grid.xyz[:, 1] > 0.75)
        labels = component_labels(grid, mask)
        counts = np.bincount(labels[labels >= 0])
        self.assertGreater(len(counts), 0)
        self.assertEqual(int(np.argmax(counts)), 0)
        self.assertEqual(int(counts[0]), int(counts.max()))

    def test_grid_components_wrapper_matches_labels(self) -> None:
        grid = CubedSphere.create(16)
        mask = grid.xyz[:, 2] > 0.2
        labels = component_labels(grid, mask)
        components = grid.components(mask)
        rebuilt = np.full(grid.size, -1, dtype=np.int32)
        for label, cells in enumerate(components):
            rebuilt[cells] = label
        np.testing.assert_array_equal(rebuilt, labels)


if __name__ == "__main__":
    unittest.main()
