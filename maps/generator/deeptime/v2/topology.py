"""Connected-component labels for landmasses and other spherical regions."""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components

from .grid import CubedSphere


def component_labels(grid: CubedSphere, mask: np.ndarray) -> np.ndarray:
    """Label connected True regions; label 0 is the largest by cell count."""
    mask = np.asarray(mask, dtype=bool)
    labels = np.full(grid.size, -1, dtype=np.int32)
    members = np.flatnonzero(mask)
    if members.size == 0:
        return labels

    # Map global cell index -> dense subgraph index.
    local = np.full(grid.size, -1, dtype=np.int32)
    local[members] = np.arange(members.size, dtype=np.int32)

    neighbors = grid.neighbors[members]
    valid = neighbors >= 0
    src = np.repeat(np.arange(members.size, dtype=np.int32), neighbors.shape[1])
    dst_global = neighbors.ravel()
    keep = valid.ravel() & mask[dst_global]
    src = src[keep]
    dst = local[dst_global[keep]]
    # Undirected: keep each edge once.
    undirected = src < dst
    src = src[undirected]
    dst = dst[undirected]

    graph = sparse.coo_matrix(
        (np.ones(len(src), dtype=np.int8), (src, dst)),
        shape=(members.size, members.size),
    )
    graph = graph + graph.T
    n_components, raw = connected_components(
        csgraph=graph, directed=False, return_labels=True
    )
    if n_components == 0:
        return labels

    counts = np.bincount(raw, minlength=n_components)
    order = np.argsort(-counts)
    remap = np.empty(n_components, dtype=np.int32)
    remap[order] = np.arange(n_components, dtype=np.int32)
    labels[members] = remap[raw]
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
