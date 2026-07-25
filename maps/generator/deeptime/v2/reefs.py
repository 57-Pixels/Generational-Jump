"""Volcanic arcs, hotspot chains, and reef growth (Darwin sequence)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import CubedSphere

EARTH_RADIUS_KM = 6371.0


@dataclass
class ArcResult:
    elevation_m: np.ndarray
    edifice_mask: np.ndarray
    edifice_id: np.ndarray


@dataclass
class HotspotResult:
    elevation_m: np.ndarray
    edifice_id: np.ndarray
    age_ma: np.ndarray


@dataclass
class ReefResult:
    reef_mask: np.ndarray
    fringing_mask: np.ndarray
    barrier_mask: np.ndarray
    atoll_mask: np.ndarray


def _haversine_km(lon1: float, lat1: float, lon2: np.ndarray, lat2: np.ndarray) -> np.ndarray:
    rlon1, rlat1 = np.deg2rad(lon1), np.deg2rad(lat1)
    rlon2, rlat2 = np.deg2rad(lon2), np.deg2rad(lat2)
    dlon = rlon2 - rlon1
    dlat = rlat2 - rlat1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(rlat1) * np.cos(rlat2) * np.sin(dlon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.clip(np.sqrt(a), 0.0, 1.0))


def _destination(
    lon: float, lat: float, azimuth_deg: float, distance_km: float
) -> tuple[float, float]:
    δ = distance_km / EARTH_RADIUS_KM
    θ = np.deg2rad(azimuth_deg)
    φ1 = np.deg2rad(lat)
    λ1 = np.deg2rad(lon)
    φ2 = np.arcsin(
        np.sin(φ1) * np.cos(δ) + np.cos(φ1) * np.sin(δ) * np.cos(θ)
    )
    λ2 = λ1 + np.arctan2(
        np.sin(θ) * np.sin(δ) * np.cos(φ1),
        np.cos(δ) - np.sin(φ1) * np.sin(φ2),
    )
    return float(np.rad2deg(λ2)), float(np.rad2deg(φ2))


def build_volcanic_arcs(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    memory: dict[str, np.ndarray],
    sea_level_m: float = 0.0,
    seed: int = 0,
    spacing_km: float = 60.0,
) -> ArcResult:
    """Place discrete volcanic edifices along subduction/arc corridors."""
    elev = np.asarray(elevation_m, dtype=np.float64).copy()
    arc = np.asarray(memory.get("arc", np.zeros(grid.size)), dtype=np.float64)
    subduction = np.asarray(
        memory.get("subduction", np.zeros(grid.size)), dtype=np.float64
    )
    corridor = ((arc > 0.2) | ((subduction > 0.35) & (subduction < 0.85))) & (
        elevation_m > -5500.0
    )
    edifice_mask = np.zeros(grid.size, dtype=bool)
    edifice_id = np.full(grid.size, -1, dtype=np.int32)
    if not np.any(corridor):
        return ArcResult(elevation_m=elev, edifice_mask=edifice_mask, edifice_id=edifice_id)

    rng = np.random.default_rng(seed + 41)
    candidates = np.flatnonzero(corridor)
    # Greedy spacing: pick peaks along the corridor ~50–70 km apart.
    order = rng.permutation(candidates)
    centers: list[int] = []
    for cell in order:
        if elev[cell] > sea_level_m + 1500.0:
            continue
        lon_c = float(grid.lon_deg[cell])
        lat_c = float(grid.lat_deg[cell])
        if centers:
            d = _haversine_km(
                lon_c,
                lat_c,
                grid.lon_deg[np.asarray(centers)],
                grid.lat_deg[np.asarray(centers)],
            )
            if float(d.min()) < spacing_km * 0.85:
                continue
        centers.append(int(cell))
        if len(centers) >= 48:
            break

    for eid, cell in enumerate(centers):
        center = grid.xyz[cell]
        cosang = np.clip(grid.xyz @ center, -1.0, 1.0)
        ang = np.arccos(cosang)
        sigma = (28.0 + 8.0 * rng.random()) / EARTH_RADIUS_KM
        height = 900.0 + 700.0 * rng.random()
        bump = height * np.exp(-0.5 * (ang / sigma) ** 2)
        # Discrete cone, not a continuous ridge.
        mask = bump > 40.0
        elev = np.where(mask, np.maximum(elev, -450.0 + bump), elev)
        # Ensure the peak is emergent for island-arc analogues.
        if elev[cell] < sea_level_m + 50.0:
            elev[cell] = sea_level_m + 120.0 + 80.0 * rng.random()
        edifice_mask |= mask & (bump > 80.0)
        edifice_id[mask & (bump > 80.0)] = eid
    return ArcResult(elevation_m=elev, edifice_mask=edifice_mask, edifice_id=edifice_id)


def build_hotspot_chain(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    start_lon: float,
    start_lat: float,
    azimuth_deg: float,
    n_edifices: int = 6,
    spacing_km: float = 250.0,
    seed: int = 0,
) -> HotspotResult:
    """Hotspot chain with monotonic age progression along plate motion."""
    elev = np.asarray(elevation_m, dtype=np.float64).copy()
    edifice_id = np.full(grid.size, -1, dtype=np.int32)
    age_ma = np.zeros(grid.size, dtype=np.float64)
    rng = np.random.default_rng(seed + 7)
    lon, lat = start_lon, start_lat
    centers: list[int] = []
    ages_list: list[float] = []
    used: set[int] = set()
    guard = 0
    while len(centers) < n_edifices and guard < n_edifices * 8:
        guard += 1
        d = _haversine_km(lon, lat, grid.lon_deg, grid.lat_deg)
        order = np.argsort(d)
        nearest = -1
        for cand in order[:12]:
            cell = int(cand)
            if cell in used:
                continue
            nearest = cell
            break
        if nearest < 0:
            lon, lat = _destination(lon, lat, azimuth_deg, spacing_km * 0.5)
            continue
        used.add(nearest)
        centers.append(nearest)
        ages_list.append(float(len(centers) - 1) * (3.5 + rng.random()))
        lon, lat = _destination(lon, lat, azimuth_deg, spacing_km)

    if centers:
        center_xyz = grid.xyz[np.asarray(centers)]
        dots = grid.xyz @ center_xyz.T
        nearest_eid = np.argmax(dots, axis=1)
        for eid, cell in enumerate(centers):
            age = ages_list[eid]
            # Young tips emerge; older edifices subside below sea level.
            peak = 900.0 - 160.0 * age
            center = grid.xyz[cell]
            cosang = np.clip(grid.xyz @ center, -1.0, 1.0)
            ang = np.arccos(cosang)
            sigma = (40.0 + 1.2 * age) / EARTH_RADIUS_KM
            envelope = np.exp(-0.5 * (ang / np.maximum(sigma, 1e-6)) ** 2)
            mask = (nearest_eid == eid) & (envelope > 0.12)
            if peak > 0.0:
                elev = np.where(mask, np.maximum(elev, peak * envelope - 150.0), elev)
                elev[cell] = max(float(elev[cell]), peak * 0.6)
            else:
                drowned = -20.0 + peak * 0.05
                elev = np.where(mask, np.minimum(np.maximum(elev, drowned - 40.0), drowned), elev)
                elev[cell] = drowned
            edifice_id[mask] = eid
            age_ma[mask] = age
    return HotspotResult(elevation_m=elev, edifice_id=edifice_id, age_ma=age_ma)


def grow_reefs(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sst_c: np.ndarray,
    edifice_mask: np.ndarray,
    sea_level_m: float = 0.0,
    max_growth_mm_yr: float = 10.0,
) -> ReefResult:
    """Darwin reef sequence: fringing → barrier → atoll on volcanic edifices."""
    elev = np.asarray(elevation_m, dtype=np.float64)
    sst = np.asarray(sst_c, dtype=np.float64)
    warm = sst >= 18.0
    photic = (elev < sea_level_m) & (elev > sea_level_m - 50.0)
    land = elev >= sea_level_m
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)

    # Fringing: warm photic water next to emergent edifice land.
    near_land_edifice = np.any(
        valid & land[safe] & edifice_mask[safe], axis=1
    )
    fringing = warm & photic & near_land_edifice

    # Barrier: warm photic ring around shallow drowned edifice still near land.
    near_any_land = np.any(valid & land[safe], axis=1)
    barrier = (
        warm & photic & edifice_mask & near_any_land & ~fringing & ~land
    )

    # Atoll: warm photic reef over drowned edifice with no emergent core.
    drowned_edifice = edifice_mask & ~land & (elev > sea_level_m - 60.0)
    has_emergent_core = np.any(valid & land[safe] & edifice_mask[safe], axis=1)
    atoll = warm & photic & drowned_edifice & ~has_emergent_core & ~fringing

    reef = fringing | barrier | atoll
    # Growth capacity proxy (mm/yr), unused beyond mask construction for now.
    _ = max_growth_mm_yr
    return ReefResult(
        reef_mask=reef,
        fringing_mask=fringing,
        barrier_mask=barrier,
        atoll_mask=atoll,
    )


def apply_island_arc_and_hotspots(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    memory: dict[str, np.ndarray],
    seed: int = 0,
    include_hotspots: bool = True,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Seafloor hook: discrete arcs plus optional hotspot chains."""
    arcs = build_volcanic_arcs(grid, elevation_m, memory, seed=seed)
    elev = arcs.elevation_m
    extras: dict[str, np.ndarray] = {
        "arc_edifice": arcs.edifice_mask.astype(np.float64),
        "arc_edifice_id": arcs.edifice_id.astype(np.float64),
    }
    if not include_hotspots:
        return elev, extras
    rng = np.random.default_rng(seed + 99)
    ocean = elev < 0.0
    if np.any(ocean):
        starts = np.flatnonzero(ocean)
        for i in range(2):
            cell = int(rng.choice(starts))
            chain = build_hotspot_chain(
                grid,
                elev,
                start_lon=float(grid.lon_deg[cell]),
                start_lat=float(grid.lat_deg[cell]),
                azimuth_deg=float(rng.uniform(0, 360)),
                n_edifices=5,
                spacing_km=float(rng.uniform(200, 320)),
                seed=seed + 11 * (i + 1),
            )
            elev = chain.elevation_m
            extras[f"hotspot_age_{i}"] = chain.age_ma
            extras[f"hotspot_id_{i}"] = chain.edifice_id.astype(np.float64)
    return elev, extras
