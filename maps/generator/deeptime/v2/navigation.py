"""Navigability: straits, harbours, shelf break, and tidal proxies."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .climate import ClimateFields
from .coastal import compute_wave_energy
from .grid import CubedSphere
from .topology import component_labels

EARTH_RADIUS_KM = 6371.0


@dataclass
class NavigationFields:
    harbour_rating: np.ndarray
    channel_depth_m: np.ndarray
    channel_width_km: np.ndarray
    chokepoint_mask: np.ndarray
    shelf_break_mask: np.ndarray
    shelf_break_depth_m: np.ndarray
    tidal_range_proxy_m: np.ndarray
    approach_width_km: np.ndarray


def measure_strait_width_km(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    strait_mask: np.ndarray,
) -> float:
    """Narrowest cross-strait width for a marked corridor (km)."""
    if not np.any(strait_mask):
        return 0.0
    lon = grid.lon_deg[strait_mask]
    lat = grid.lat_deg[strait_mask]
    # Principal axis: use lon/lat spans; width is the minor span.
    dlon = float(lon.max() - lon.min()) * 111.0 * np.cos(
        np.deg2rad(float(np.mean(lat)))
    )
    dlat = float(lat.max() - lat.min()) * 111.0
    return float(max(min(dlon, dlat), 0.0))


def harbour_rating(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    wave_energy: np.ndarray,
) -> np.ndarray:
    """0–1 harbour score from depth, shelter, approach, and hinterland."""
    elev = np.asarray(elevation_m, dtype=np.float64)
    land = elev >= sea_level_m
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    n_valid = np.maximum(valid.sum(axis=1), 1)
    coastal = land & np.any(valid & ocean[safe], axis=1)
    rating = np.zeros(grid.size, dtype=np.float64)
    if not np.any(coastal):
        return rating

    # Depth: neighbouring ocean depth (adequate berth / approach).
    ocean_depth = np.where(ocean, np.maximum(sea_level_m - elev, 0.0), 0.0)
    near_depth = np.where(valid, ocean_depth[safe], 0.0).max(axis=1)
    depth_score = np.clip(near_depth / 40.0, 0.0, 1.0)

    # Shelter: enclosure dominates on coarse grids; calm seas still matter.
    if np.any(wave_energy[coastal] > 0):
        wmax = float(np.percentile(wave_energy[coastal], 95))
    else:
        wmax = 1.0
    calm = 1.0 - np.clip(wave_energy / max(wmax, 1e-6), 0.0, 1.0)
    land_frac = np.where(valid, land[safe], False).sum(axis=1) / n_valid
    enclosure = np.clip((land_frac - 0.25) / 0.55, 0.0, 1.0)
    shelter = 0.35 * calm + 0.65 * enclosure

    # Approach: prefer a mouth (some ocean access), not a fully open coast.
    ocean_frac = np.where(valid, ocean[safe], False).sum(axis=1) / n_valid
    approach = np.clip(1.0 - np.abs(ocean_frac - 0.35) / 0.55, 0.0, 1.0)

    # Hinterland: gentle land behind the port.
    hinter = np.zeros(grid.size)
    for i in np.flatnonzero(coastal):
        vals = []
        for nb in grid.neighbors[i]:
            if nb >= 0 and land[nb]:
                vals.append(elev[nb])
        if vals:
            hinter[i] = float(
                np.clip(1.0 - (np.mean(vals) - sea_level_m) / 800.0, 0.0, 1.0)
            )
        else:
            hinter[i] = 0.3

    rating[coastal] = (
        0.15 * depth_score[coastal]
        + 0.55 * shelter[coastal]
        + 0.15 * approach[coastal]
        + 0.15 * hinter[coastal]
    )
    return np.clip(rating, 0.0, 1.0)


def chokepoint_geometry(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    chokepoint_mask: np.ndarray,
) -> list[dict]:
    """Summarise each chokepoint corridor: width, length, depth, alternatives."""
    elev = np.asarray(elevation_m, dtype=np.float64)
    labels = component_labels(grid, chokepoint_mask)
    ocean = elev < sea_level_m
    cell_km = EARTH_RADIUS_KM * np.sqrt(np.maximum(grid.area_sr, 1e-12))
    summaries: list[dict] = []
    for label in np.unique(labels):
        if label < 0:
            continue
        mask = labels == label
        if int(mask.sum()) < 1:
            continue
        width = measure_strait_width_km(grid, elev, sea_level_m, mask)
        length = float(np.sum(cell_km[mask]))
        depth = float(np.mean(np.maximum(sea_level_m - elev[mask], 0.0)))
        # Alternative routes: other ocean cells outside this corridor component.
        alternatives = int(np.sum(ocean & ~mask)) > int(mask.sum())
        summaries.append(
            {
                "id": int(label),
                "width_km": round(width, 2),
                "length_km": round(length, 2),
                "mean_depth_m": round(depth, 1),
                "cell_count": int(mask.sum()),
                "has_alternative_route": bool(alternatives),
                "lon": float(np.mean(grid.lon_deg[mask])),
                "lat": float(np.mean(grid.lat_deg[mask])),
            }
        )
    summaries.sort(key=lambda s: s["width_km"])
    return summaries


def navigation_to_geojson(nav: NavigationFields, grid: CubedSphere) -> dict:
    """Point features for top harbours, chokepoints, and shelf-break samples."""
    features: list[dict] = []
    harbour = nav.harbour_rating
    top = np.argsort(-harbour)[:24]
    for rank, idx in enumerate(top):
        score = float(harbour[idx])
        if score < 0.35:
            break
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        float(grid.lon_deg[idx]),
                        float(grid.lat_deg[idx]),
                    ],
                },
                "properties": {
                    "kind": "harbour",
                    "rank": rank + 1,
                    "rating": round(score, 3),
                    "channel_depth_m": round(float(nav.channel_depth_m[idx]), 1),
                    "approach_width_km": round(
                        float(nav.approach_width_km[idx]), 2
                    ),
                },
            }
        )
    choke_idx = np.flatnonzero(nav.chokepoint_mask)
    if choke_idx.size:
        # Sample up to 40 chokepoint cells.
        step = max(1, choke_idx.size // 40)
        for idx in choke_idx[::step][:40]:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(grid.lon_deg[idx]),
                            float(grid.lat_deg[idx]),
                        ],
                    },
                    "properties": {
                        "kind": "chokepoint",
                        "channel_depth_m": round(
                            float(nav.channel_depth_m[idx]), 1
                        ),
                        "channel_width_km": round(
                            float(nav.channel_width_km[idx]), 2
                        ),
                    },
                }
            )
    shelf_idx = np.flatnonzero(nav.shelf_break_mask)
    if shelf_idx.size:
        step = max(1, shelf_idx.size // 60)
        for idx in shelf_idx[::step][:60]:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(grid.lon_deg[idx]),
                            float(grid.lat_deg[idx]),
                        ],
                    },
                    "properties": {
                        "kind": "shelf_break",
                        "depth_m": round(
                            float(nav.shelf_break_depth_m[idx]), 1
                        ),
                        "tidal_range_proxy_m": round(
                            float(nav.tidal_range_proxy_m[idx]), 2
                        ),
                    },
                }
            )
    return {"type": "FeatureCollection", "name": "navigation-v2", "features": features}


def compute_navigation(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    wind: np.ndarray,
    climate: ClimateFields,
) -> NavigationFields:
    elev = np.asarray(elevation_m, dtype=np.float64)
    land = elev >= sea_level_m
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    wave = compute_wave_energy(grid, elev, sea_level_m, wind)
    harbours = harbour_rating(grid, elev, sea_level_m, wave)

    # Channel depth/width along coastal approaches.
    depth = np.where(ocean, np.maximum(sea_level_m - elev, 0.0), 0.0)
    channel_depth = np.where(valid, depth[safe], 0.0).max(axis=1)
    channel_depth = np.where(land, channel_depth, depth)
    ocean_deg = np.where(valid, ocean[safe], False).sum(axis=1)
    cell_km = EARTH_RADIUS_KM * np.sqrt(np.maximum(grid.area_sr, 1e-12))
    channel_width = ocean_deg.astype(np.float64) * cell_km

    # Chokepoints: narrow ocean corridors between land masses.
    chokepoint = ocean & (ocean_deg <= 3) & np.any(valid & land[safe], axis=1)
    # Require two land neighbours roughly opposite — approx: land_deg >= 2.
    land_deg = np.where(valid, land[safe], False).sum(axis=1)
    chokepoint &= land_deg >= 2

    # Shelf break: ocean cells near the -130 to -200 m transition.
    shelf = ocean & (elev > sea_level_m - 200.0) & (elev < sea_level_m - 80.0)
    deep = ocean & (elev <= sea_level_m - 200.0)
    shelf_break = shelf & np.any(valid & deep[safe], axis=1)
    shelf_depth = np.where(shelf_break, sea_level_m - elev, 0.0)

    # Tidal range proxy: funnel embayments amplify.
    enclosure = land_deg.astype(np.float64) / 8.0
    funnel = ocean & (enclosure > 0.35) & (enclosure < 0.85)
    tidal = np.where(funnel, 1.5 + 4.0 * enclosure, 0.6 + 0.4 * enclosure)
    tidal = np.where(ocean, tidal, 0.0)

    approach = channel_width.copy()
    return NavigationFields(
        harbour_rating=harbours,
        channel_depth_m=channel_depth,
        channel_width_km=channel_width,
        chokepoint_mask=chokepoint,
        shelf_break_mask=shelf_break,
        shelf_break_depth_m=shelf_depth,
        tidal_range_proxy_m=tidal,
        approach_width_km=approach,
    )
