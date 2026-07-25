"""Directional climate model on the cubed sphere."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import CubedSphere
from .ocean import compute_ocean


@dataclass
class ClimateFields:
    temperature_c: np.ndarray
    hottest_month_c: np.ndarray
    coldest_month_c: np.ndarray
    hottest_wet_bulb_c: np.ndarray
    seasonal_range_c: np.ndarray
    wind_xyz: np.ndarray
    precipitation_mm_yr: np.ndarray
    pet_mm_yr: np.ndarray
    humidity: np.ndarray
    continentality: np.ndarray
    monsoon_index: np.ndarray
    snow_fraction: np.ndarray
    sea_ice_fraction: np.ndarray
    cdd24: np.ndarray
    sst_c: np.ndarray | None = None
    upwelling: np.ndarray | None = None


_CHUNK = 2_000_000


def _ocean_influence(
    grid: CubedSphere, ocean: np.ndarray, steps: int = 24, chunk: int = _CHUNK
) -> np.ndarray:
    """Propagate ocean influence without allocating an (N, 8) temporary at once."""
    influence = ocean.astype(np.float64)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    nxt = np.empty_like(influence)
    for _ in range(steps):
        for start in range(0, grid.size, chunk):
            end = min(start + chunk, grid.size)
            v = valid[start:end]
            s = safe[start:end]
            neighbor_max = np.where(v, influence[s], 0.0).max(axis=1)
            nxt[start:end] = np.maximum(influence[start:end], neighbor_max * 0.86)
        influence, nxt = nxt, influence
    return np.clip(influence, 0, 1)


def _wind_vectors(grid: CubedSphere) -> np.ndarray:
    xyz = grid.xyz
    z_axis = np.array([0.0, 0.0, 1.0])
    east = np.cross(z_axis, xyz)
    weak = np.linalg.norm(east, axis=1) < 1e-8
    east[weak] = np.cross(np.array([1.0, 0.0, 0.0]), xyz[weak])
    east /= np.maximum(np.linalg.norm(east, axis=1, keepdims=True), 1e-12)
    north = np.cross(xyz, east)
    lat = grid.lat_deg
    abs_lat = np.abs(lat)
    zonal = np.where(abs_lat < 28.0, -1.0, np.where(abs_lat < 62.0, 1.0, -0.65))
    meridional = np.where(
        abs_lat < 28.0,
        -0.22 * np.sign(lat),
        np.where(abs_lat < 55.0, 0.10 * np.sign(lat), -0.06 * np.sign(lat)),
    )
    wind = zonal[:, None] * east + meridional[:, None] * north
    return wind / np.maximum(np.linalg.norm(wind, axis=1, keepdims=True), 1e-12)


def _upstream_neighbors(
    grid: CubedSphere, wind: np.ndarray, chunk: int = _CHUNK
) -> np.ndarray:
    """Pick the neighbour most aligned with wind, processing cells in slices.

    Avoids materialising the full (N, 8, 3) direction temporary (~4.8 GB at T1).
    """
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    chosen = np.empty(grid.size, dtype=np.int64)
    for start in range(0, grid.size, chunk):
        end = min(start + chunk, grid.size)
        v = valid[start:end]
        s = safe[start:end]
        xyz = grid.xyz[start:end]
        neighbor_xyz = grid.xyz[s]
        direction = xyz[:, None, :] - neighbor_xyz
        radial = np.einsum("mki,mi->mk", direction, xyz)
        direction -= radial[:, :, None] * xyz[:, None, :]
        direction /= np.maximum(
            np.linalg.norm(direction, axis=2, keepdims=True), 1e-12
        )
        alignment = np.einsum("mki,mi->mk", direction, wind[start:end])
        alignment = np.where(v, alignment, -np.inf)
        local = np.argmax(alignment, axis=1)
        chosen[start:end] = s[np.arange(end - start), local]
    return chosen


def compute_climate(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    era: str = "present",
) -> ClimateFields:
    elevation_m = np.asarray(elevation_m, dtype=np.float64)
    land = elevation_m >= sea_level_m
    ocean = ~land
    lat = grid.lat_deg
    abs_lat = np.abs(lat)
    ocean_influence = _ocean_influence(grid, ocean)
    continentality = np.where(land, 1.0 - ocean_influence, 0.0)

    sea_level_temp = 28.5 - 0.0062 * abs_lat**2
    cooling = np.maximum(elevation_m - sea_level_m, 0.0) / 1000.0 * 6.5
    lgm_cooling = 5.0 if era == "lgm" else 0.0
    temperature = sea_level_temp - cooling - lgm_cooling
    seasonal_range = (
        3.0
        + 18.0 * (abs_lat / 90.0) ** 1.2
        + 16.0 * continentality * (abs_lat / 70.0)
    )
    hottest = temperature + 0.5 * seasonal_range
    coldest = temperature - 0.5 * seasonal_range

    wind = _wind_vectors(grid)
    upstream = _upstream_neighbors(grid, wind)
    humidity_air = ocean.astype(np.float64)
    precipitation = np.zeros(grid.size, dtype=np.float64)
    for _ in range(64):
        incoming = humidity_air[upstream] * 0.985
        uplift = np.maximum(
            0.0, elevation_m - elevation_m[upstream]
        ) / 1800.0
        condensation = np.clip(0.018 + 0.42 * uplift, 0.0, 0.72)
        rain = incoming * condensation * land
        precipitation += rain
        humidity_air = np.where(ocean, 1.0, np.clip(incoming - rain, 0.0, 1.0))

    ocean_state = compute_ocean(grid, land, wind, temperature)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = land & np.any(valid & ocean[safe], axis=1)
    neighbor_sst = np.where(valid, ocean_state.sst_c[safe], temperature[:, None])
    ocean_nb = valid & ocean[safe]
    sst_coast = np.where(
        ocean_nb.any(axis=1),
        np.where(ocean_nb, neighbor_sst, -np.inf).max(axis=1),
        temperature,
    )
    temperature = np.where(coastal, 0.55 * temperature + 0.45 * sst_coast, temperature)
    hottest = temperature + 0.5 * seasonal_range
    coldest = temperature - 0.5 * seasonal_range

    itcz = np.exp(-((lat / 10.0) ** 2))
    subtropical_dry = np.exp(-((abs_lat - 27.0) / 8.5) ** 2)
    upwelling_onshore = np.zeros(grid.size)
    for slot in range(grid.neighbors.shape[1]):
        n = safe[:, slot]
        mask = valid[:, slot] & coastal & ocean[n]
        upwelling_onshore[mask] = np.maximum(
            upwelling_onshore[mask], ocean_state.upwelling[n[mask]]
        )

    precipitation = (
        precipitation * 950.0
        + 1600.0 * itcz * (0.35 + 0.65 * ocean_influence)
        - 500.0 * subtropical_dry * continentality
        - 900.0 * upwelling_onshore * land.astype(float)
    )
    # Rain shadow after mm conversion so lee drying survives large-scale terms.
    # Multi-hop barrier: dry cells that sit below high terrain along the wind path.
    barrier_m = np.zeros(grid.size, dtype=np.float64)
    cursor = np.arange(grid.size)
    peak = elevation_m.copy()
    for _ in range(6):
        cursor = upstream[cursor]
        peak = np.maximum(peak, elevation_m[cursor])
        barrier_m = np.maximum(barrier_m, peak - elevation_m)
    descent_m = np.maximum(0.0, elevation_m[upstream] - elevation_m)
    shadow_m = np.maximum(descent_m, 0.65 * barrier_m)
    lee = land & (shadow_m > 40.0)
    precipitation = np.where(
        lee, precipitation * np.exp(-shadow_m / 900.0), precipitation
    )
    ascent_m = np.maximum(0.0, elevation_m - elevation_m[upstream])
    windward = land & (ascent_m > 40.0)
    precipitation = np.where(
        windward, precipitation * (1.0 + ascent_m / 1000.0), precipitation
    )
    precipitation = np.clip(precipitation, 30.0, 4800.0)
    if era == "lgm":
        precipitation *= 0.82

    pet = np.clip(140.0 + 48.0 * np.maximum(temperature, -5.0), 80.0, 2300.0)
    humidity = np.clip(
        0.18 + 0.62 * precipitation / (precipitation + pet) + 0.2 * ocean_influence,
        0.05,
        0.98,
    )
    hottest_wet_bulb = hottest - (1.0 - humidity) * 8.0

    monsoon = np.clip(
        continentality
        * np.exp(-((abs_lat - 20.0) / 16.0) ** 2)
        * (precipitation / 1800.0)
        * (0.55 + 0.45 * ocean_influence),
        0,
        1,
    )
    snow = np.where(land, np.clip((2.0 - coldest) / 22.0, 0, 1), 0.0)
    sea_ice = np.where(
        ocean,
        np.clip((-1.5 - coldest) / 18.0, 0, 0.88),
        0.0,
    )
    cdd24 = np.maximum(hottest - 24.0, 0.0) * 120.0
    return ClimateFields(
        temperature_c=temperature,
        hottest_month_c=hottest,
        coldest_month_c=coldest,
        hottest_wet_bulb_c=hottest_wet_bulb,
        seasonal_range_c=seasonal_range,
        wind_xyz=wind,
        precipitation_mm_yr=precipitation,
        pet_mm_yr=pet,
        humidity=humidity,
        continentality=continentality,
        monsoon_index=monsoon,
        snow_fraction=snow,
        sea_ice_fraction=sea_ice,
        cdd24=cdd24,
        sst_c=ocean_state.sst_c,
        upwelling=ocean_state.upwelling,
    )
