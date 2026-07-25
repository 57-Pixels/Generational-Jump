"""Nested refinement window tests."""

from __future__ import annotations

import unittest

import numpy as np

from deeptime.v2.climate import compute_climate
from deeptime.v2.grid import CubedSphere
from deeptime.v2.refine import (
    WindowSpec,
    blend_windows,
    extract_window,
    refine_window,
)


class RefineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parent = CubedSphere.create(16)
        self.elevation = np.full(self.parent.size, -3000.0)
        land = (np.abs(self.parent.lon_deg) < 40.0) & (
            np.abs(self.parent.lat_deg) < 30.0
        )
        self.elevation[land] = (
            200.0
            + 600.0 * np.clip(self.parent.xyz[land, 0], 0, 1)
            + 250.0 * np.sin(np.deg2rad(self.parent.lat_deg[land] * 4.0))
        )
        self.climate = compute_climate(self.parent, self.elevation, 0.0)
        self.spec = WindowSpec(
            lon_min=-20.0,
            lon_max=20.0,
            lat_min=-15.0,
            lat_max=15.0,
            target_km=80.0,
            margin=0.1,
        )

    def test_refined_downsampled_matches_parent_rms(self) -> None:
        window = extract_window(
            self.parent, self.elevation, self.climate, self.spec, seed=3
        )
        refined = refine_window(window, iterations=8, seed=3)
        # Sample refined field back onto parent cells inside the core window.
        core = (
            (self.parent.lon_deg >= self.spec.lon_min)
            & (self.parent.lon_deg <= self.spec.lon_max)
            & (self.parent.lat_deg >= self.spec.lat_min)
            & (self.parent.lat_deg <= self.spec.lat_max)
        )
        parent_vals = self.elevation[core]
        # Nearest refined cell by lon/lat.
        recon = np.empty(int(core.sum()))
        lon = self.parent.lon_deg[core]
        lat = self.parent.lat_deg[core]
        for i, (lo, la) in enumerate(zip(lon, lat)):
            d2 = (refined.lon_deg - lo) ** 2 + (refined.lat_deg - la) ** 2
            recon[i] = refined.elevation_m[int(np.argmin(d2))]
        rms = float(np.sqrt(np.mean((recon - parent_vals) ** 2)))
        self.assertLessEqual(rms, 50.0)

    def test_seam_gradient_within_tolerance(self) -> None:
        # Two overlapping windows; blended seam gradient must stay controlled.
        left = WindowSpec(-25.0, 5.0, -12.0, 12.0, target_km=90.0, margin=0.15)
        right = WindowSpec(-5.0, 25.0, -12.0, 12.0, target_km=90.0, margin=0.15)
        w_left = refine_window(
            extract_window(self.parent, self.elevation, self.climate, left, seed=1),
            iterations=6,
            seed=1,
        )
        w_right = refine_window(
            extract_window(self.parent, self.elevation, self.climate, right, seed=1),
            iterations=6,
            seed=1,
        )
        blended = blend_windows([w_left, w_right])
        # Measure gradient across the shared lon≈0 seam vs just inside.
        seam = np.abs(blended.lon_deg) < 1.5
        inside = (blended.lon_deg > 3.0) & (blended.lon_deg < 8.0)
        if int(seam.sum()) < 4 or int(inside.sum()) < 4:
            self.skipTest("seam fixture too sparse")
        # Finite-difference proxy via nearest-neighbour differences.
        def mean_grad(mask: np.ndarray) -> float:
            idxs = np.flatnonzero(mask)
            grads = []
            for i in idxs:
                d2 = (blended.lon_deg - blended.lon_deg[i]) ** 2 + (
                    blended.lat_deg - blended.lat_deg[i]
                ) ** 2
                d2[i] = np.inf
                j = int(np.argmin(d2))
                dist = max(np.sqrt(d2[j]) * 111.0, 1.0)
                grads.append(abs(blended.elevation_m[i] - blended.elevation_m[j]) / dist)
            return float(np.mean(grads))

        g_seam = mean_grad(seam)
        g_inside = mean_grad(inside)
        self.assertLessEqual(g_seam, 1.2 * max(g_inside, 1e-6) + 1e-6)

    def test_refinement_deterministic_and_order_independent(self) -> None:
        a = refine_window(
            extract_window(self.parent, self.elevation, self.climate, self.spec, seed=9),
            iterations=5,
            seed=9,
        )
        b = refine_window(
            extract_window(self.parent, self.elevation, self.climate, self.spec, seed=9),
            iterations=5,
            seed=9,
        )
        np.testing.assert_allclose(a.elevation_m, b.elevation_m, atol=1e-9)
        left = WindowSpec(-20.0, 5.0, -10.0, 10.0, target_km=100.0, margin=0.1)
        right = WindowSpec(-5.0, 20.0, -10.0, 10.0, target_km=100.0, margin=0.1)
        wl = refine_window(
            extract_window(self.parent, self.elevation, self.climate, left, seed=2),
            iterations=4,
            seed=2,
        )
        wr = refine_window(
            extract_window(self.parent, self.elevation, self.climate, right, seed=2),
            iterations=4,
            seed=2,
        )
        blend_ab = blend_windows([wl, wr])
        blend_ba = blend_windows([wr, wl])
        # Same sample locations after merge — compare by sorting lon/lat keys.
        def keyed(win):
            order = np.lexsort((win.lat_deg, win.lon_deg))
            return win.lon_deg[order], win.lat_deg[order], win.elevation_m[order]

        la, lalat, lae = keyed(blend_ab)
        lb, lblat, lbe = keyed(blend_ba)
        np.testing.assert_allclose(la, lb, atol=1e-9)
        np.testing.assert_allclose(lalat, lblat, atol=1e-9)
        np.testing.assert_allclose(lae, lbe, atol=1e-6)


if __name__ == "__main__":
    unittest.main()
