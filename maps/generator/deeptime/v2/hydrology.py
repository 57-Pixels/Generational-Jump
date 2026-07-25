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
    endorheic_mask: np.ndarray | None = None


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
    seed: int = 0,
    stochastic: bool = True,
) -> np.ndarray:
    """Receivers with optional probabilistic downhill routing.

    ``stochastic=False`` selects the unique steepest neighbour (legacy
    identity); ``stochastic=True`` weights among all downhill neighbours to
    avoid D8-aligned drainage spikes.
    """
    receiver = np.full(grid.size, -1, dtype=np.int32)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    touches_ocean = land & np.any(valid & (~land[safe]), axis=1)
    inland = land & ~touches_ocean

    neighbor_filled = np.where(valid, filled[safe], np.inf)
    drop = filled[:, None] - neighbor_filled
    downhill = valid & (drop > 1e-7)
    has_lower = downhill.any(axis=1)

    if stochastic:
        weights = np.where(downhill, np.power(np.maximum(drop, 0.0), 1.1), 0.0)
        total = weights.sum(axis=1, keepdims=True)
        probs = np.where(total > 0, weights / np.maximum(total, 1e-12), 0.0)
        cdf = np.cumsum(probs, axis=1)
        cell_ids = np.arange(grid.size, dtype=np.int64)
        u = ((cell_ids * 1_000_003 + int(seed) * 7919) % 1_000_003) / 1_000_003.0
        picked = (cdf >= u[:, None]) & (probs > 0)
        any_pick = picked.any(axis=1)
        fallback = np.argmax(weights, axis=1)
        best_slot = np.where(any_pick, np.argmax(picked, axis=1), fallback)
    else:
        scored = np.where(downhill, neighbor_filled, np.inf)
        best_slot = np.argmin(scored, axis=1)

    best = safe[np.arange(grid.size), best_slot]
    use_lower = inland & has_lower
    use_parent = inland & ~use_lower
    receiver[use_lower] = best[use_lower]
    receiver[use_parent] = parent[use_parent]
    return receiver


def river_segment_bearings_deg(
    grid: CubedSphere,
    hydrology: HydrologyFields,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Facet-based D-infinity bearings (degrees clockwise from north).

    For each selected cell, project neighbours into the local tangent plane, sort
    them by angle, and take the steepest planar facet between adjacent
    neighbour pairs. That yields continuous aspects instead of eight D8 spikes.
    """
    if mask is None:
        cells = np.flatnonzero(hydrology.river_mask)
    else:
        cells = np.flatnonzero(mask)
    if cells.size == 0:
        return np.zeros(0, dtype=np.float64)

    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    filled = hydrology.filled_elevation_m
    xyz = grid.xyz
    z_axis = np.array([0.0, 0.0, 1.0])
    east = np.cross(z_axis, xyz)
    weak = np.linalg.norm(east, axis=1) < 1e-8
    east[weak] = np.cross(np.array([1.0, 0.0, 0.0]), xyz[weak])
    east /= np.maximum(np.linalg.norm(east, axis=1, keepdims=True), 1e-12)
    north = np.cross(xyz, east)

    bearings: list[float] = []
    for cell in cells:
        slots = np.flatnonzero(valid[cell])
        if slots.size < 3:
            continue
        nbs = safe[cell, slots]
        delta = xyz[nbs] - xyz[cell]
        radial = delta @ xyz[cell]
        delta = delta - radial[:, None] * xyz[cell]
        e = delta @ east[cell]
        n = delta @ north[cell]
        ang = np.arctan2(e, n)
        order = np.argsort(ang)
        e = e[order]
        n = n[order]
        z = filled[nbs[order]] - filled[cell]
        best_slope = -np.inf
        best_aspect = 0.0
        count = len(order)
        for i in range(count):
            j = (i + 1) % count
            # Planar facet through origin and two neighbours in ENZ.
            p1 = np.array([e[i], n[i], z[i]], dtype=np.float64)
            p2 = np.array([e[j], n[j], z[j]], dtype=np.float64)
            normal = np.cross(p1, p2)
            if abs(normal[2]) < 1e-12:
                continue
            ge = -normal[0] / normal[2]
            gn = -normal[1] / normal[2]
            slope = float(np.hypot(ge, gn))
            if slope <= best_slope:
                continue
            aspect = float(np.degrees(np.arctan2(-ge, -gn)) % 360.0)
            if z[i] < 0.0 or z[j] < 0.0 or slope > 0.0:
                best_slope = slope
                best_aspect = aspect
        if best_slope > 0.0:
            bearings.append(best_aspect)
    return np.asarray(bearings, dtype=np.float64)


def _classify_depressions(
    grid: CubedSphere,
    land: np.ndarray,
    elevation: np.ndarray,
    filled: np.ndarray,
    climate: ClimateFields,
    receiver: np.ndarray,
    runoff: np.ndarray,
    discharge: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return lake_id, endorheic_mask, and receivers with basin sinks applied."""
    depression = np.where(land, np.maximum(filled - elevation, 0.0), 0.0)
    pit = land & (depression > 8.0)
    labels = component_labels(grid, pit)
    lake_id = np.full(grid.size, -1, dtype=np.int32)
    endorheic = np.zeros(grid.size, dtype=bool)
    recv = receiver.copy()

    for lid in np.unique(labels):
        if lid < 0:
            continue
        cells = np.flatnonzero(labels == lid)
        if cells.size < 2:
            continue
        precip = float(climate.precipitation_mm_yr[cells].mean())
        pet = float(climate.pet_mm_yr[cells].mean())
        local_runoff = float(runoff[cells].mean())
        inflow = float(discharge[cells].max())
        # Inflow-driven lakes vs arid salt pans.
        wet = (
            (precip >= 0.5 * pet)
            or (local_runoff > 25.0)
            or (inflow > 80.0 and precip > 80.0)
            or (precip - pet > -250.0 and float(depression[cells].max()) > 35.0)
        )
        deepest = int(cells[np.argmin(elevation[cells])])
        if wet:
            lake_id[cells] = int(lid)
        else:
            endorheic[cells] = True
        for cell in cells:
            if int(cell) == deepest:
                recv[cell] = -1
                continue
            best = deepest
            best_elev = elevation[deepest]
            for nb in grid.neighbors[cell]:
                if nb < 0:
                    continue
                if wet and lake_id[nb] != lid:
                    continue
                if (not wet) and (not endorheic[nb]):
                    continue
                if elevation[nb] < best_elev - 1e-6:
                    best = int(nb)
                    best_elev = float(elevation[nb])
            recv[cell] = best
    return lake_id, endorheic, recv


def compute_hydrology(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    climate: ClimateFields,
    seed: int = 0,
) -> HydrologyFields:
    elevation = np.asarray(elevation_m, dtype=np.float64)
    land = elevation >= sea_level_m
    filled, parent, pop_order = _priority_flood(grid, elevation, land)
    receiver = _receivers(grid, filled, land, parent, seed=seed)

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

    lake_id, endorheic, receiver = _classify_depressions(
        grid, land, elevation, filled, climate, receiver, runoff, discharge
    )

    # Re-accumulate discharge after lake/endorheic receiver rewiring.
    drainage = np.where(land, cell_area, 0.0)
    discharge = np.where(land, runoff * cell_area * 1000.0 / 31_557_600.0, 0.0)
    # Topological order: cells with higher filled elevation first.
    order = np.argsort(-filled)
    for cell in order:
        if not land[cell]:
            continue
        downstream = int(receiver[cell])
        if downstream >= 0:
            drainage[downstream] += drainage[cell]
            discharge[downstream] += discharge[cell]

    land_drainage = drainage[land]
    threshold = (
        float(np.percentile(land_drainage, 82)) if len(land_drainage) else np.inf
    )
    river = land & (drainage >= threshold) & (discharge > 15.0)
    # Grow rivers downstream along receivers so every channel reaches a sink.
    grown = river.copy()
    for cell in np.flatnonzero(river):
        current = int(cell)
        seen: set[int] = set()
        while current >= 0 and current not in seen:
            seen.add(current)
            if land[current]:
                grown[current] = True
            if lake_id[current] >= 0 or endorheic[current]:
                break
            downstream = int(receiver[current])
            if downstream < 0:
                break
            current = downstream
    river = grown
    depression = np.where(land, np.maximum(filled - elevation, 0.0), 0.0)

    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = land & np.any(valid & (~land[safe]), axis=1)
    local_relief = np.zeros(grid.size, dtype=np.float64)
    chunk = 2_000_000
    for start in range(0, grid.size, chunk):
        end = min(start + chunk, grid.size)
        v = valid[start:end]
        s = safe[start:end]
        local_relief[start:end] = np.where(
            v, np.abs(elevation[start:end, None] - elevation[s]), 0.0
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
        endorheic_mask=endorheic,
    )
