"""Priority-flood drainage, rivers, lakes, and deltas."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from .climate import ClimateFields
from .grid import CubedSphere
from .topology import component_labels

EARTH_RADIUS_KM = 6371.0


@dataclass
class HydrologyFields:
    filled_elevation_m: np.ndarray
    depression_depth_m: np.ndarray
    receiver: np.ndarray
    drainage_area_km2: np.ndarray
    runoff_mm_yr: np.ndarray
    discharge_m3_s: np.ndarray
    river_mask: np.ndarray
    lake_id: np.ndarray
    delta_score: np.ndarray


def _priority_flood(
    grid: CubedSphere, elevation_m: np.ndarray, land: np.ndarray
) -> tuple[np.ndarray, np.ndarray, list[int]]:
    filled = np.asarray(elevation_m, dtype=np.float64).copy()
    parent = np.full(grid.size, -1, dtype=np.int32)
    visited = ~land.copy()
    heap: list[tuple[float, int]] = []
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    touches_ocean = land & np.any(valid & (~land[safe]), axis=1)
    for cell in np.flatnonzero(touches_ocean):
        visited[cell] = True
        heapq.heappush(heap, (float(filled[cell]), int(cell)))

    # A landlocked all-land synthetic input still gets deterministic outlets.
    if not heap and np.any(land):
        outlet = int(np.argmin(np.where(land, filled, np.inf)))
        visited[outlet] = True
        heapq.heappush(heap, (float(filled[outlet]), outlet))

    pop_order: list[int] = []
    while heap:
        spill, cell = heapq.heappop(heap)
        pop_order.append(cell)
        for neighbor in grid.neighbors[cell]:
            if neighbor < 0:
                continue
            n = int(neighbor)
            if not land[n] or visited[n]:
                continue
            visited[n] = True
            parent[n] = cell
            filled[n] = max(float(elevation_m[n]), spill)
            heapq.heappush(heap, (float(filled[n]), n))
    return filled, parent, pop_order


def _receivers(
    grid: CubedSphere,
    filled: np.ndarray,
    land: np.ndarray,
    parent: np.ndarray,
) -> np.ndarray:
    receiver = np.full(grid.size, -1, dtype=np.int32)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    for cell in np.flatnonzero(land):
        neighbors = safe[cell, valid[cell]]
        wet = neighbors[~land[neighbors]]
        if len(wet):
            receiver[cell] = -1
            continue
        lower = neighbors[filled[neighbors] < filled[cell] - 1e-7]
        if len(lower):
            receiver[cell] = int(lower[np.argmin(filled[lower])])
        else:
            receiver[cell] = int(parent[cell])
    return receiver


def compute_hydrology(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    climate: ClimateFields,
) -> HydrologyFields:
    elevation = np.asarray(elevation_m, dtype=np.float64)
    land = elevation >= sea_level_m
    filled, parent, pop_order = _priority_flood(grid, elevation, land)
    receiver = _receivers(grid, filled, land, parent)

    runoff = np.clip(
        climate.precipitation_mm_yr - 0.55 * climate.pet_mm_yr, 0.0, 4000.0
    )
    cell_area = grid.area_sr * EARTH_RADIUS_KM**2
    drainage = np.where(land, cell_area, 0.0)
    # mm/year × km² converts to 1e3 m³/year.
    discharge = np.where(land, runoff * cell_area * 1000.0 / 31_557_600.0, 0.0)
    for cell in reversed(pop_order):
        downstream = int(receiver[cell])
        if downstream >= 0:
            drainage[downstream] += drainage[cell]
            discharge[downstream] += discharge[cell]

    land_drainage = drainage[land]
    threshold = (
        float(np.percentile(land_drainage, 82)) if len(land_drainage) else np.inf
    )
    river = land & (drainage >= threshold) & (discharge > 15.0)
    # Grow rivers downstream along receivers so every channel reaches the coast.
    # Without this, mid-threshold gaps leave inland stubs and wonky jumps.
    grown = river.copy()
    for cell in np.flatnonzero(river):
        current = int(cell)
        seen: set[int] = set()
        while current >= 0 and current not in seen:
            seen.add(current)
            if land[current]:
                grown[current] = True
            downstream = int(receiver[current])
            if downstream < 0:
                break
            current = downstream
    river = grown
    depression = np.where(land, np.maximum(filled - elevation, 0.0), 0.0)
    lake_mask = land & (depression > 20.0)
    lake_id = component_labels(grid, lake_mask)

    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = land & np.any(valid & (~land[safe]), axis=1)
    local_relief = np.where(
        valid,
        np.abs(elevation[:, None] - elevation[safe]),
        0.0,
    ).max(axis=1)
    delta = np.zeros(grid.size)
    if np.any(coastal):
        q_scale = max(float(np.percentile(discharge[coastal], 90)), 1.0)
        delta[coastal] = np.clip(discharge[coastal] / q_scale, 0, 1) * np.exp(
            -local_relief[coastal] / 300.0
        )
    return HydrologyFields(
        filled_elevation_m=filled,
        depression_depth_m=depression,
        receiver=receiver,
        drainage_area_km2=drainage,
        runoff_mm_yr=runoff,
        discharge_m3_s=discharge,
        river_mask=river,
        lake_id=lake_id,
        delta_score=delta,
    )
