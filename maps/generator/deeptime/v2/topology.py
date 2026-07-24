"""Connected-component labels for landmasses and other spherical regions."""

from __future__ import annotations

import numpy as np

from .grid import CubedSphere


def component_labels(grid: CubedSphere, mask: np.ndarray) -> np.ndarray:
    labels = np.full(grid.size, -1, dtype=np.int32)
    for label, cells in enumerate(grid.components(mask)):
        labels[cells] = label
    return labels


def fit_area_fraction_level(
    values: np.ndarray,
    area: np.ndarray,
    target_fraction_above: float,
) -> float:
    """Weighted threshold with target area at or above the returned value."""
    if not 0.0 < target_fraction_above < 1.0:
        raise ValueError("target fraction must be between zero and one")
    order = np.argsort(values)[::-1]
    cumulative = np.cumsum(area[order])
    target = target_fraction_above * float(area.sum())
    index = int(np.searchsorted(cumulative, target, side="left"))
    index = min(index, len(order) - 1)
    return float(values[order[index]])


def area_fraction(mask: np.ndarray, area: np.ndarray) -> float:
    return float(area[np.asarray(mask, dtype=bool)].sum() / area.sum())
