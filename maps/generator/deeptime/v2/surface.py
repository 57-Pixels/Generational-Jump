"""Stream-power erosion, sediment, lakes coupling, and glaciation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .climate import ClimateFields
from .grid import CubedSphere
from .hydrology import HydrologyFields, compute_hydrology

EARTH_RADIUS_M = 6_371_000.0


@dataclass
class SurfaceResult:
    elevation_m: np.ndarray
    hydrology: HydrologyFields
    ice_thickness_m: np.ndarray
    endorheic_mask: np.ndarray
    fjord_mask: np.ndarray
    sediment_m: np.ndarray
    ice_sea_level_equivalent_m: float


def _cell_spacing_m(grid: CubedSphere) -> np.ndarray:
    return EARTH_RADIUS_M * np.sqrt(np.maximum(grid.area_sr, 1e-12))


def _equilibrium_line_altitude_m(
    grid: CubedSphere, climate: ClimateFields
) -> np.ndarray:
    """ELA falls toward the poles and with colder air temperatures."""
    abs_lat = np.abs(grid.lat_deg)
    ela = 4800.0 - 55.0 * abs_lat - 90.0 * np.maximum(-climate.temperature_c, 0.0)
    return np.clip(ela, 50.0, 5500.0)


def _hillslope_diffusion(
    grid: CubedSphere,
    elevation: np.ndarray,
    land: np.ndarray,
    dx: np.ndarray,
    d: float,
    dt: float,
) -> np.ndarray:
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    elev_nb = np.where(valid, elevation[safe], elevation[:, None])
    land_nb = valid & land[safe]
    lap = np.where(land_nb, elev_nb - elevation[:, None], 0.0).sum(axis=1)
    count = np.maximum(land_nb.sum(axis=1), 1)
    lap = lap / count
    # Explicit diffusion; clamp for stability on coarse grids.
    step = np.clip(d * dt / np.maximum(dx**2, 1.0), 0.0, 0.2)
    return np.where(land, elevation + step * lap, elevation)


def _stream_power_step(
    grid: CubedSphere,
    elevation: np.ndarray,
    land: np.ndarray,
    hydro: HydrologyFields,
    climate: ClimateFields,
    dx: np.ndarray,
    dt: float,
    k: float = 3.0e-6,
    m: float = 0.5,
    n: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Detachment-limited incision plus downstream sediment flux."""
    recv = hydro.receiver
    elev = elevation.copy()
    sediment = np.zeros(grid.size, dtype=np.float64)
    has_recv = land & (recv >= 0)
    drop = np.zeros(grid.size, dtype=np.float64)
    drop[has_recv] = np.maximum(elev[has_recv] - elev[recv[has_recv]], 0.0)
    slope = drop / np.maximum(dx, 1.0)
    q = np.maximum(hydro.discharge_m3_s, 0.0)
    incision = k * (q**m) * (slope**n)

    # Canyon mode: arid high-slope cells concentrate incision, limit widening.
    arid = land & (climate.precipitation_mm_yr < 350.0)
    canyon = arid & (slope > 0.02) & (q > 5.0)
    incision = np.where(canyon, incision * 2.4, incision)

    # Cap so a single step cannot erase more than a fraction of local relief.
    max_cut = np.maximum(0.15 * drop, 0.5)
    cut = np.minimum(incision * dt, max_cut)
    cut = np.where(land & has_recv, cut, 0.0)
    elev -= cut
    sediment += cut

    # Deposit where transport capacity collapses (low slope / lake / coast).
    capacity = 0.35 * (q**1.1) * np.maximum(slope, 1e-4)
    deposit = np.minimum(sediment, np.maximum(0.0, sediment - capacity * dt / 1e3))
    lake = hydro.lake_id >= 0
    coastal = land & ~has_recv
    deposit = np.where(lake | coastal | (slope < 0.002), sediment * 0.45, deposit * 0.25)
    deposit = np.minimum(deposit, sediment)
    elev += deposit
    sediment -= deposit

    # Move remaining sediment one step downstream.
    moved = np.zeros_like(sediment)
    donors = np.flatnonzero(has_recv & (sediment > 0))
    for cell in donors:
        moved[recv[cell]] += sediment[cell] * 0.7
        sediment[cell] *= 0.3
    sediment += moved
    elev += sediment * 0.05
    sediment *= 0.95
    return elev, sediment


def _glacial_step(
    grid: CubedSphere,
    elevation: np.ndarray,
    land: np.ndarray,
    climate: ClimateFields,
    ice: np.ndarray,
    dx: np.ndarray,
    dt: float,
    glacial_boost: float,
) -> tuple[np.ndarray, np.ndarray]:
    ela = _equilibrium_line_altitude_m(grid, climate)
    accum = np.where(land, np.clip((elevation - ela) / 800.0, -0.85, 1.8), 0.0)
    # Polar ice sheets as standing features.
    polar = land & (np.abs(grid.lat_deg) > 70.0)
    accum = np.where(polar, np.maximum(accum, 0.45), accum)
    ice = np.maximum(ice + accum * (dt / 40.0), 0.0)
    ice = np.where(land, ice, 0.0)

    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    # Route ice toward the lowest neighbour; erode with ice throughput.
    elev_nb = np.where(valid, elevation[safe], np.inf)
    low_slot = np.argmin(elev_nb, axis=1)
    target = safe[np.arange(grid.size), low_slot]
    can_flow = land & valid[np.arange(grid.size), low_slot] & (
        elevation > elev_nb[np.arange(grid.size), low_slot] + 1.0
    )
    flux = np.zeros(grid.size, dtype=np.float64)
    moving = ice * np.where(can_flow, 0.35, 0.0)
    ice = ice - moving
    # Scatter into targets (may collide; acceptable for this coarse model).
    for cell in np.flatnonzero(moving > 0):
        flux[cell] += float(moving[cell])
        ice[target[cell]] += float(moving[cell])
        flux[target[cell]] += float(moving[cell])

    ice = np.minimum(np.maximum(ice, 0.0), 3500.0)
    steep = np.maximum(elevation - elev_nb[np.arange(grid.size), low_slot], 0.0) / np.maximum(
        dx, 1.0
    )
    erosion = glacial_boost * 4.0e-3 * (ice * 0.5 + flux) * (0.5 + steep) * (dt / 60.0)
    # Prefer valley floors and ice streams; allow overdeepening below sea level.
    neighbor_min = elev_nb.min(axis=1)
    valley = land & (elevation <= neighbor_min + 80.0)
    high_lat = np.abs(grid.lat_deg) > 55.0
    erosion = np.where(valley, erosion * 3.0, erosion * 0.35)
    erosion = np.where(valley & high_lat, erosion * 1.8, erosion)
    # Hard caps: metres per step, and do not excavate abyssal depths on continent.
    erosion = np.minimum(erosion, 40.0)
    erosion = np.minimum(erosion, np.maximum(5.0, 0.25 * np.maximum(ice, flux)))
    elevation = elevation - np.where(land, erosion, 0.0)
    elevation = np.where(land, np.maximum(elevation, -500.0), elevation)
    return elevation, ice


def find_fjords(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    ice_thickness_m: np.ndarray,
    sea_level_m: float,
    continent: np.ndarray | None = None,
) -> np.ndarray:
    """Below-sea-level overdeepened valleys connected to the ocean."""
    elev = np.asarray(elevation_m, dtype=np.float64)
    ocean = elev < sea_level_m
    if continent is None:
        # Treat shallow drowned cells as candidate continental troughs.
        continent = ocean & (elev > sea_level_m - 600.0)
        continent |= elev >= sea_level_m
    # Overdeepened trough on former land: slightly below sea level.
    trough = continent & (elev < sea_level_m - 1.0) & (elev > sea_level_m - 800.0)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    open_ocean = ocean & ~trough
    seed = trough & np.any(valid & open_ocean[safe], axis=1)
    near_ice = np.any(valid & (ice_thickness_m[safe] > 10.0), axis=1)
    seed |= trough & near_ice & np.any(valid & ocean[safe], axis=1)
    # Isolated overdeepened valley cells still count if ice-worn.
    seed |= trough & (ice_thickness_m > 30.0)

    fjord = seed.copy()
    changed = True
    while changed:
        changed = False
        grow = trough & ~fjord & np.any(valid & fjord[safe], axis=1)
        if np.any(grow):
            fjord[grow] = True
            changed = True
    return fjord


def evolve_surface(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    climate: ClimateFields,
    iterations: int = 40,
    seed: int = 0,
    glacial_boost: float = 1.0,
    dt_yr: float = 400.0,
) -> SurfaceResult:
    """Iterate fluvial incision, diffusion, sediment, and glacial erosion."""
    elev = np.asarray(elevation_m, dtype=np.float64).copy()
    initial = elev.copy()
    continent = initial >= sea_level_m
    ice = np.zeros(grid.size, dtype=np.float64)
    sediment = np.zeros(grid.size, dtype=np.float64)
    dx = _cell_spacing_m(grid)
    hydro = compute_hydrology(grid, elev, sea_level_m, climate, seed=seed)

    for step in range(max(iterations, 0)):
        land = elev >= sea_level_m
        hydro = compute_hydrology(
            grid, elev, sea_level_m, climate, seed=seed + step
        )
        elev, sed_step = _stream_power_step(
            grid, elev, land, hydro, climate, dx, dt_yr
        )
        sediment = 0.85 * sediment + sed_step
        elev = _hillslope_diffusion(grid, elev, land, dx, d=0.01, dt=dt_yr)
        # Glaciate original continent so valleys may overdeepen below sea level.
        elev, ice = _glacial_step(
            grid, elev, continent, climate, ice, dx, dt_yr, glacial_boost
        )
        # Keep true ocean basins from being filled by onshore sediment diffusion.
        elev = np.where(~continent, np.minimum(elev, initial), elev)

    land = elev >= sea_level_m
    hydro = compute_hydrology(grid, elev, sea_level_m, climate, seed=seed)
    endorheic = (
        hydro.endorheic_mask
        if hydro.endorheic_mask is not None
        else np.zeros(grid.size, dtype=bool)
    )
    fjords = find_fjords(grid, elev, ice, sea_level_m, continent=continent)
    ocean_area = float(np.maximum((~land).astype(np.float64) * grid.area_sr, 0.0).sum())
    ice_volume = float((ice * grid.area_sr).sum() * EARTH_RADIUS_M**2)
    ocean_area_m2 = ocean_area * EARTH_RADIUS_M**2
    sle = ice_volume / ocean_area_m2 if ocean_area_m2 > 0 else 0.0
    return SurfaceResult(
        elevation_m=elev,
        hydrology=hydro,
        ice_thickness_m=ice,
        endorheic_mask=endorheic,
        fjord_mask=fjords,
        sediment_m=sediment,
        ice_sea_level_equivalent_m=float(sle),
    )
