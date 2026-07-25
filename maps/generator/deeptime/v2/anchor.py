"""Canon anchoring: score generated worlds against Veldara geography constraints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .grid import CubedSphere
from .topology import component_labels

EARTH_RADIUS_KM = 6371.0
KM2_PER_SR = EARTH_RADIUS_KM**2


@dataclass(frozen=True)
class AnchorScore:
    continent_scale: float
    veldara_claim: float
    west_cordillera: float
    gulf: float
    highspine: float
    eastmarch: float
    farreach: float
    harbours: float
    region_cells: np.ndarray = field(repr=False)

    @property
    def total(self) -> float:
        parts = (
            self.continent_scale,
            self.veldara_claim,
            self.west_cordillera,
            self.gulf,
            self.highspine,
            self.eastmarch,
            self.farreach,
            self.harbours,
        )
        return float(sum(parts) / len(parts))

    def as_dict(self) -> dict[str, float]:
        return {
            "continent_scale": self.continent_scale,
            "veldara_claim": self.veldara_claim,
            "west_cordillera": self.west_cordillera,
            "gulf": self.gulf,
            "highspine": self.highspine,
            "eastmarch": self.eastmarch,
            "farreach": self.farreach,
            "harbours": self.harbours,
            "total": self.total,
        }


def _cell_area_km2(grid: CubedSphere) -> np.ndarray:
    return grid.area_sr * KM2_PER_SR


def _largest_landmass(
    grid: CubedSphere, land: np.ndarray
) -> tuple[int, np.ndarray, float]:
    labels = component_labels(grid, land)
    best_id = -1
    best_area = 0.0
    area = _cell_area_km2(grid)
    for lid in np.unique(labels):
        if lid < 0:
            continue
        mask = labels == lid
        a = float(area[mask].sum())
        if a > best_area:
            best_area = a
            best_id = int(lid)
    mask = labels == best_id if best_id >= 0 else np.zeros(grid.size, dtype=bool)
    return best_id, mask, best_area


def _score_continent_scale(area_km2: float, plate_ids: np.ndarray, mask: np.ndarray) -> float:
    # Target 20–35M km² on one dominant plate.
    if area_km2 <= 0:
        return 0.0
    if 20.0e6 <= area_km2 <= 35.0e6:
        size = 1.0
    elif 12.0e6 <= area_km2 < 20.0e6:
        size = (area_km2 - 12.0e6) / 8.0e6
    elif 35.0e6 < area_km2 <= 50.0e6:
        size = 1.0 - (area_km2 - 35.0e6) / 15.0e6
    else:
        size = 0.0
    if not np.any(mask):
        return 0.0
    plates = plate_ids[mask]
    if plates.size == 0:
        return 0.0
    # Dominant plate fraction.
    vals, counts = np.unique(plates, return_counts=True)
    dominance = float(counts.max()) / float(counts.sum())
    return float(np.clip(size * dominance, 0.0, 1.0))


def _pick_veldara_region(
    grid: CubedSphere, landmass: np.ndarray, elevation: np.ndarray
) -> np.ndarray:
    """Heuristic claim region: mid-latitude western half of the largest landmass."""
    if not np.any(landmass):
        return np.zeros(grid.size, dtype=bool)
    lon = grid.lon_deg
    lat = grid.lat_deg
    mid = landmass & (np.abs(lat) < 55.0)
    if not np.any(mid):
        mid = landmass
    # Prefer the longitudinal half with more western ocean exposure.
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    ocean = ~landmass & (elevation < 0.0)
    # Use land mask from elevation for ocean adjacency.
    land = elevation >= 0.0
    ocean = ~land
    coastal = landmass & np.any(valid & ocean[safe], axis=1)
    west_coast = coastal & (lon <= np.median(lon[mid]))
    if np.any(west_coast):
        west_lon = float(np.median(lon[west_coast]))
    else:
        west_lon = float(np.percentile(lon[mid], 25))
    # ~3.2M km² target: grow from west coast inland.
    area = _cell_area_km2(grid)
    order = np.argsort(np.abs(lon[mid] - west_lon) + 0.35 * np.abs(lat[mid]))
    mid_idx = np.flatnonzero(mid)[order]
    chosen = np.zeros(grid.size, dtype=bool)
    running = 0.0
    for cell in mid_idx:
        chosen[cell] = True
        running += float(area[cell])
        if running >= 3.2e6:
            break
    return chosen


def _score_veldara_claim(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    if not np.any(region):
        return 0.0
    area = float(_cell_area_km2(grid)[region].sum())
    # Soft peak around 3.2M km².
    size = float(np.exp(-0.5 * ((area - 3.2e6) / 1.2e6) ** 2))
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coastal):
        return 0.0
    # Two-ocean access: coastal cells spanning a wide longitude range.
    lon_span = float(grid.lon_deg[coastal].max() - grid.lon_deg[coastal].min())
    access = np.clip(lon_span / 40.0, 0.0, 1.0)
    return float(np.clip(0.55 * size + 0.45 * access, 0.0, 1.0))


def _score_west_cordillera(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    if not np.any(region):
        return 0.0
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coastal):
        return 0.0
    west_lon = float(np.percentile(grid.lon_deg[coastal], 15))
    near_west = region & (grid.lon_deg < west_lon + 12.0)
    high = near_west & (elevation > 1200.0)
    if not np.any(high):
        return 0.0
    # Coast-parallel: high cells should span latitude more than longitude.
    dlat = float(grid.lat_deg[high].max() - grid.lat_deg[high].min())
    dlon = float(grid.lon_deg[high].max() - grid.lon_deg[high].min())
    parallel = np.clip(dlat / max(dlon, 1.0) / 2.0, 0.0, 1.0)
    presence = np.clip(float(high.sum()) / max(float(near_west.sum()), 1.0) * 4.0, 0.0, 1.0)
    return float(np.clip(0.5 * presence + 0.5 * parallel, 0.0, 1.0))


def _score_gulf(grid: CubedSphere, region: np.ndarray, elevation: np.ndarray) -> float:
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    # Semi-enclosed embayment: ocean cells with many land neighbours near region.
    near_region = ocean & np.any(valid & region[safe], axis=1)
    if not np.any(near_region):
        return 0.0
    enclosure = np.zeros(grid.size, dtype=np.float64)
    enclosure[near_region] = (
        np.where(valid[near_region], land[safe[near_region]], False).sum(axis=1)
        / np.maximum(valid[near_region].sum(axis=1), 1)
    )
    embayment = near_region & (enclosure > 0.45)
    if not np.any(embayment):
        return 0.0
    area = float(_cell_area_km2(grid)[embayment].sum())
    return float(np.clip(area / 150_000.0, 0.0, 1.0))


def _score_highspine(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    if not np.any(region):
        return 0.0
    interior = region.copy()
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    land = elevation >= 0.0
    ocean = ~land
    coastal = region & np.any(valid & ocean[safe], axis=1)
    interior[coastal] = False
    high = interior & (elevation > 1500.0)
    if not np.any(high):
        return 0.0
    # Pass corridor: a path of cells under 2000 m crossing the high belt in lon.
    lon_min = float(grid.lon_deg[high].min())
    lon_max = float(grid.lon_deg[high].max())
    mid_lat = float(np.median(grid.lat_deg[high]))
    band = (
        region
        & (np.abs(grid.lat_deg - mid_lat) < 8.0)
        & (grid.lon_deg >= lon_min - 2.0)
        & (grid.lon_deg <= lon_max + 2.0)
    )
    if not np.any(band):
        return 0.0
    passable = band & (elevation < 2000.0)
    has_pass = np.any(passable) and float(passable.sum()) >= 3
    range_score = np.clip(float(high.sum()) / 8.0, 0.0, 1.0)
    return float(np.clip(0.5 * range_score + (0.5 if has_pass else 0.0), 0.0, 1.0))


def score_eastmarch(
    grid: CubedSphere,
    elevation: np.ndarray,
    plate_id: np.ndarray,
    region: np.ndarray,
    *,
    glacial_mask: np.ndarray | None = None,
) -> float:
    """Eastmarch plain: long, low relief, no plate boundary, unglaciated."""
    if not np.any(region):
        return 0.0
    lon = grid.lon_deg
    mid_lon = float(np.median(lon[region]))
    east_half = region & (lon >= mid_lon - 2.0) & (elevation >= 0.0)
    plain = east_half & (elevation < 600.0)
    if int(plain.sum()) < 5:
        return 0.0
    # Plate boundary anywhere in the eastern half is a hard fail.
    plates = plate_id[east_half]
    vals, counts = np.unique(plates, return_counts=True)
    if len(vals) > 1 and float(counts.max()) / float(counts.sum()) < 0.98:
        return 0.0
    # Also fail if a high orogenic wall sits inside the eastern half.
    if np.any(east_half & (elevation > 1500.0)):
        return 0.0
    dlon = float(lon[plain].max() - lon[plain].min())
    dlat = float(grid.lat_deg[plain].max() - grid.lat_deg[plain].min())
    length_km = max(dlon, dlat) * 111.0
    length_score = np.clip(length_km / 800.0, 0.0, 1.0)
    relief = float(elevation[plain].max() - elevation[plain].min())
    relief_score = (
        1.0
        if relief < 300.0
        else float(np.clip(1.0 - (relief - 300.0) / 700.0, 0.0, 1.0))
    )
    if glacial_mask is not None and np.any(glacial_mask[plain]):
        glacial_score = 0.0
    else:
        glacial_score = 1.0
    return float(
        np.clip(
            0.4 * length_score + 0.4 * relief_score + 0.2 * glacial_score,
            0.0,
            1.0,
        )
    )


def _score_farreach(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    land = elevation >= 0.0
    if not np.any(region):
        return 0.0
    # Distance from claim coast to offshore islands.
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    ocean = ~land
    coast = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coast):
        return 0.0
    coast_xyz = grid.xyz[coast].mean(axis=0)
    coast_xyz /= max(float(np.linalg.norm(coast_xyz)), 1e-12)
    labels = component_labels(grid, land)
    claim_ids = set(np.unique(labels[region]).tolist())
    best = 0.0
    for lid in np.unique(labels):
        if lid < 0 or lid in claim_ids:
            continue
        mask = labels == lid
        size = int(mask.sum())
        if size < 2 or size > 80:
            continue
        center = grid.xyz[mask].mean(axis=0)
        center /= max(float(np.linalg.norm(center)), 1e-12)
        ang = float(np.arccos(np.clip(center @ coast_xyz, -1.0, 1.0)))
        dist_km = ang * EARTH_RADIUS_KM
        if dist_km <= 1500.0:
            best = max(best, 1.0 - dist_km / 1500.0)
    return float(best)


def _score_harbours(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coastal):
        return 0.0
    # Deep-water harbour proxy: coastal cell next to ocean deeper than 40 m,
    # with embayment (multiple ocean neighbours) and moderate local relief.
    deep = np.any(valid & (elevation[safe] < -40.0), axis=1)
    embayed = np.where(valid, ocean[safe], False).sum(axis=1) >= 2
    harbours = coastal & deep & embayed
    n = int(harbours.sum())
    return float(np.clip(n / 2.0, 0.0, 1.0))


def score_world(world: Any) -> AnchorScore:
    """Score a generated world against the eight Veldara canon constraints."""
    grid = world.grid
    elevation = world.geology.elevation_m
    land = elevation >= world.sea_level_m
    _, landmass, area = _largest_landmass(grid, land)
    continent = _score_continent_scale(area, world.geology.plate_id, landmass)
    region = _pick_veldara_region(grid, landmass, elevation)
    glacial = None
    if hasattr(world, "climate") and world.climate is not None:
        glacial = (world.climate.coldest_month_c < -15.0) & (
            world.climate.snow_fraction > 0.55
        )
    return AnchorScore(
        continent_scale=continent,
        veldara_claim=_score_veldara_claim(grid, region, elevation),
        west_cordillera=_score_west_cordillera(grid, region, elevation),
        gulf=_score_gulf(grid, region, elevation),
        highspine=_score_highspine(grid, region, elevation),
        eastmarch=score_eastmarch(
            grid, elevation, world.geology.plate_id, region, glacial_mask=glacial
        ),
        farreach=_score_farreach(grid, region, elevation),
        harbours=_score_harbours(grid, region, elevation),
        region_cells=np.flatnonzero(region),
    )
