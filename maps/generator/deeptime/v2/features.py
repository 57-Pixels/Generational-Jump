"""Named geographic feature extraction with stable geometry-hashed IDs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from .grid import CubedSphere
from .topology import component_labels

EARTH_RADIUS_KM = 6371.0

# Canon pins — override table keyed by kind + coarse location token.
CANON_NAME_OVERRIDES: dict[str, str] = {
    "range:highspine": "Highspine",
    "plain:eastmarch": "Eastmarch",
    "gulf:east": "East Gulf",
    "islands:farreach": "Farreach",
}

_NAME_ROOTS = (
    "Aurel",
    "Veld",
    "Korv",
    "Sereth",
    "Dover",
    "Solmar",
    "Nerath",
    "Tesen",
    "Mirrin",
    "Cassian",
    "High",
    "East",
    "West",
    "South",
    "North",
    "Silver",
    "Iron",
    "Amber",
)


@dataclass(frozen=True)
class NamedFeature:
    kind: str
    feature_id: str
    name: str
    cell_indices: np.ndarray
    properties: dict[str, Any]


@dataclass(frozen=True)
class SeaClassification:
    enclosed_sea_mask: np.ndarray
    open_bay_mask: np.ndarray
    opening_width_km: np.ndarray
    basin_area_km2: np.ndarray


def _stable_id(kind: str, lon: np.ndarray, lat: np.ndarray) -> str:
    """Geometry hash — independent of iteration order."""
    if lon.size == 0:
        payload = f"{kind}|empty"
    else:
        # Quantize and sort so order does not matter.
        pts = sorted(
            (round(float(a), 2), round(float(b), 2)) for a, b in zip(lon, lat)
        )
        payload = kind + "|" + ";".join(f"{a:.2f},{b:.2f}" for a, b in pts)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"{kind}-{digest}"


def _name_from_id(feature_id: str, kind: str) -> str:
    token = feature_id.split("-", 1)[-1]
    n = int(token[:8], 16)
    root = _NAME_ROOTS[n % len(_NAME_ROOTS)]
    suffix = ("reach", "mere", "mark", "gate", "sound", "ridge", "bay", "holm")[
        (n // len(_NAME_ROOTS)) % 8
    ]
    base = f"{root}{suffix.capitalize()}"
    # Canon override by coarse kind token.
    for key, name in CANON_NAME_OVERRIDES.items():
        k_kind, _ = key.split(":", 1)
        if k_kind == kind and token.startswith(
            hashlib.sha1(key.encode()).hexdigest()[:2]
        ):
            return name
    return base


def _pin_canon_name(kind: str, name: str, lon: np.ndarray, lat: np.ndarray) -> str:
    """Apply explicit canon pins when a feature matches a known role."""
    if kind == "range" and lon.size and float(np.ptp(lat)) > float(np.ptp(lon)):
        # North–south cordillera → Highspine candidate.
        if float(np.mean(np.abs(lon))) < 80.0:
            return CANON_NAME_OVERRIDES.get("range:highspine", name)
    if kind == "plain" and lon.size:
        return CANON_NAME_OVERRIDES.get("plain:eastmarch", name)
    if kind == "gulf":
        return CANON_NAME_OVERRIDES.get("gulf:east", name)
    if kind == "islands":
        return CANON_NAME_OVERRIDES.get("islands:farreach", name)
    return name


def classify_sea_enclosure(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    *,
    enclosed_ratio_max: float = 0.045,
) -> SeaClassification:
    """Classify ocean basins by opening-width / sqrt(area) ratio.

    Low ratio → enclosed (Mediterranean-like); high → open bay/gulf.
    """
    elev = np.asarray(elevation_m, dtype=np.float64)
    ocean = elev < sea_level_m
    land = ~ocean
    labels = component_labels(grid, ocean)
    enclosed = np.zeros(grid.size, dtype=bool)
    open_bay = np.zeros(grid.size, dtype=bool)
    opening = np.zeros(grid.size, dtype=np.float64)
    area = np.zeros(grid.size, dtype=np.float64)
    cell_km2 = grid.area_sr * EARTH_RADIUS_KM**2
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)

    for lid in np.unique(labels):
        if lid < 0:
            continue
        mask = labels == lid
        basin_area = float(cell_km2[mask].sum())
        if basin_area < 20_000.0:
            continue
        # Opening width: only cells that gate to a different ocean component
        # through a land neighbour (true strait), not the whole shoreline.
        gateway = np.zeros(grid.size, dtype=bool)
        for i in np.flatnonzero(mask):
            for nb in grid.neighbors[i]:
                if nb < 0 or not land[nb]:
                    continue
                for nn in grid.neighbors[nb]:
                    if nn >= 0 and ocean[nn] and labels[nn] != lid:
                        gateway[i] = True
                        break
                if gateway[i]:
                    break
        if not np.any(gateway):
            width_km = 0.0
        else:
            width_km = float(np.sqrt(cell_km2[gateway].sum()))
        ratio = width_km / max(np.sqrt(basin_area), 1.0)
        opening[mask] = width_km
        area[mask] = basin_area
        # World ocean: huge area → skip.
        if basin_area > 80e6:
            continue
        if ratio <= enclosed_ratio_max:
            enclosed[mask] = True
        else:
            open_bay[mask] = True
    return SeaClassification(
        enclosed_sea_mask=enclosed,
        open_bay_mask=open_bay,
        opening_width_km=opening,
        basin_area_km2=area,
    )


def _components_to_features(
    grid: CubedSphere,
    mask: np.ndarray,
    kind: str,
    *,
    min_cells: int = 2,
    max_cells: int | None = None,
    props: dict[str, Any] | None = None,
) -> list[NamedFeature]:
    labels = component_labels(grid, mask)
    out: list[NamedFeature] = []
    for lid in np.unique(labels):
        if lid < 0:
            continue
        cells = np.flatnonzero(labels == lid)
        if cells.size < min_cells:
            continue
        if max_cells is not None and cells.size > max_cells:
            continue
        lon = grid.lon_deg[cells]
        lat = grid.lat_deg[cells]
        fid = _stable_id(kind, lon, lat)
        name = _pin_canon_name(kind, _name_from_id(fid, kind), lon, lat)
        meta = {"cell_count": int(cells.size)}
        if props:
            meta.update(props)
        out.append(
            NamedFeature(
                kind=kind,
                feature_id=fid,
                name=name,
                cell_indices=cells,
                properties=meta,
            )
        )
    out.sort(key=lambda f: f.feature_id)
    return out


def extract_features(world: Any) -> list[NamedFeature]:
    """Extract seas, gulfs, lakes, ranges, islands, rivers, deltas, reefs."""
    grid = world.grid
    elev = world.geology.elevation_m
    sea = world.sea_level_m
    land = elev >= sea
    ocean = ~land
    features: list[NamedFeature] = []

    seas = classify_sea_enclosure(grid, elev, sea)
    features.extend(
        _components_to_features(
            grid, seas.enclosed_sea_mask, "sea", min_cells=4, props={"enclosed": True}
        )
    )
    features.extend(
        _components_to_features(
            grid, seas.open_bay_mask, "gulf", min_cells=4, props={"enclosed": False}
        )
    )

    # Lakes from hydrology.
    lake = world.hydrology.lake_id >= 0
    features.extend(_components_to_features(grid, lake, "lake", min_cells=2))

    # Mountain ranges: high contiguous land.
    high = land & (elev > 1500.0)
    features.extend(_components_to_features(grid, high, "range", min_cells=4))

    # Plains: low contiguous interior land.
    plain = land & (elev < 400.0) & (elev >= sea)
    features.extend(
        _components_to_features(grid, plain, "plain", min_cells=8, max_cells=500)
    )

    # Island groups: small land components.
    labels = component_labels(grid, land)
    island_mask = np.zeros(grid.size, dtype=bool)
    for lid in np.unique(labels):
        if lid < 0:
            continue
        cells = labels == lid
        n = int(cells.sum())
        if 1 <= n <= 80:
            island_mask |= cells
    features.extend(
        _components_to_features(grid, island_mask, "islands", min_cells=1, max_cells=80)
    )

    # River systems: connected river mask components.
    river = world.hydrology.river_mask
    features.extend(_components_to_features(grid, river, "river", min_cells=3))

    # Deltas.
    delta = world.hydrology.delta_score > 0.35
    features.extend(_components_to_features(grid, delta, "delta", min_cells=1))

    # Passes: low saddle in high terrain.
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    high_nb = np.any(valid & (elev[safe] > 1500.0), axis=1)
    pass_mask = land & high_nb & (elev < 2000.0) & (elev > 400.0)
    features.extend(_components_to_features(grid, pass_mask, "pass", min_cells=1))

    # Capes / peninsulas: coastal land with high ocean adjacency.
    ocean_deg = np.where(valid, ocean[safe], False).sum(axis=1)
    cape = land & (ocean_deg >= 3)
    features.extend(_components_to_features(grid, cape, "cape", min_cells=1, max_cells=30))

    features.sort(key=lambda f: (f.kind, f.feature_id))
    return features


def features_to_geojson(features: Iterable[NamedFeature], world: Any | None = None) -> dict:
    """Export features as point centroids (stable, lightweight)."""
    feats = []
    for f in features:
        if world is None:
            lon = lat = 0.0
        else:
            lon = float(np.mean(world.grid.lon_deg[f.cell_indices]))
            lat = float(np.mean(world.grid.lat_deg[f.cell_indices]))
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "id": f.feature_id,
                    "name": f.name,
                    "kind": f.kind,
                    **f.properties,
                },
            }
        )
    feats.sort(key=lambda x: x["properties"]["id"])
    return {
        "type": "FeatureCollection",
        "name": "features-v2",
        "features": feats,
    }
