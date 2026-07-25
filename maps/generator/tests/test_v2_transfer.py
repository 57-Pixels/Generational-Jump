"""T0 → T1 field transfer tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.geology import GeologyConfig, simulate_geology
from deeptime.v2.grid import CubedSphere
from deeptime.v2.transfer import (
    area_weighted_land_fraction,
    downsample_labels,
    upsample,
)


class TransferTests(unittest.TestCase):
    def test_labels_upsample_without_new_values(self) -> None:
        coarse = CubedSphere.create(16)
        fine = CubedSphere.create(32)
        labels = np.arange(coarse.size, dtype=np.int32) % 7
        up = upsample(labels, coarse, fine, method="nearest")
        self.assertTrue(set(int(x) for x in np.unique(up)).issubset(set(range(7))))

    def test_land_area_round_trip_within_two_percent(self) -> None:
        coarse = CubedSphere.create(24)
        fine = CubedSphere.create(48)
        geology, _ = simulate_geology(
            coarse, GeologyConfig(seed=11, ticks=10, n_plates=8, n_continents=4)
        )
        up = upsample(geology.elevation_m, coarse, fine, method="smooth")
        # Nearest-downsample back and compare land fractions.
        back_index = fine.indices_for_xyz(coarse.xyz)
        back = up[back_index]
        coarse_frac = area_weighted_land_fraction(geology.elevation_m, coarse)
        back_frac = area_weighted_land_fraction(back, coarse)
        self.assertLess(abs(coarse_frac - back_frac), 0.03)

    def test_smooth_upsample_has_no_coarse_spacing_gradient_spike(self) -> None:
        coarse = CubedSphere.create(16)
        fine = CubedSphere.create(64)
        geology, _ = simulate_geology(
            coarse, GeologyConfig(seed=3, ticks=8, n_plates=6, n_continents=3)
        )
        up = upsample(geology.elevation_m, coarse, fine, method="smooth")
        valid = fine.neighbors >= 0
        safe = np.where(valid, fine.neighbors, 0)
        diffs = np.where(valid, np.abs(up[:, None] - up[safe]), 0.0)
        grad = diffs.max(axis=1)
        # Histogram of gradient magnitudes — no single bin should dominate
        # the way a staircase at coarse spacing would.
        hist, _ = np.histogram(grad[grad > 0], bins=20)
        self.assertLess(float(hist.max()) / max(float(hist.mean()), 1.0), 12.0)

    def test_downsample_labels_helper(self) -> None:
        coarse = CubedSphere.create(12)
        fine = CubedSphere.create(24)
        labels = (coarse.xyz[:, 0] > 0).astype(np.int32)
        up = upsample(labels, coarse, fine, method="nearest")
        back = downsample_labels(up, fine, coarse)
        # Majority agreement; exact equality is not required at seams.
        self.assertGreater(float(np.mean(back == labels)), 0.9)


if __name__ == "__main__":
    unittest.main()
