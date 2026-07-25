"""Upsample coarse (T0) fields onto finer cubed-sphere grids."""

from __future__ import annotations

import numpy as np

from .grid import CubedSphere


def upsample(
    field: np.ndarray,
    source_grid: CubedSphere,
    target_grid: CubedSphere,
    method: str = "nearest",
) -> np.ndarray:
    """Sample ``field`` from ``source_grid`` onto ``target_grid`` cells.

    ``nearest`` — label-safe nearest cell (no new values introduced).
    ``smooth`` — nearest sample then a light target-grid smooth so T0 cell
    boundaries do not print through as staircase edges.
    """
    if method not in ("nearest", "smooth"):
        raise ValueError(f"unknown upsample method {method!r}")
    source_index = source_grid.indices_for_xyz(target_grid.xyz)
    sampled = np.asarray(field)[source_index]
    if method == "nearest":
        return sampled.copy()
    smoothed = target_grid.smooth(
        sampled.astype(np.float64), iterations=2, self_weight=2.5
    )
    return smoothed


def downsample_labels(
    labels: np.ndarray, fine_grid: CubedSphere, coarse_grid: CubedSphere
) -> np.ndarray:
    """Nearest sample of fine labels onto a coarser grid (for round-trip tests)."""
    index = fine_grid.indices_for_xyz(coarse_grid.xyz)
    return np.asarray(labels)[index]


def area_weighted_land_fraction(
    elevation_m: np.ndarray, grid: CubedSphere, sea_level_m: float = 0.0
) -> float:
    land = np.asarray(elevation_m) >= sea_level_m
    return float(grid.area_sr[land].sum() / grid.area_sr.sum())
