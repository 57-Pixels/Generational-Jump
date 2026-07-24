"""Directional climate model on the cubed sphere."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import CubedSphere


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


def _ocean_influence(grid: CubedSphere, ocean: np.ndarray, steps: int = 24) -> np.ndarray:
    influence = ocean.astype(np.float64)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    for _ in range(steps):
        neighbor_max = np.where(valid, influence[safe], 0.0).max(axis=1)
        influence = np.maximum(influence, neighbor_max * 0.86)
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


def _upstream_neighbors(grid: CubedSphere, wind: np.ndarray) -> np.ndarray:
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    neighbor_xyz = grid.xyz[safe]
    # Direction travelled from candidate neighbor toward this cell.
    direction = grid.xyz[:, None, :] - neighbor_xyz
    radial = np.einsum("mki,mi->mk", direction, grid.xyz)
    direction -= radial[:, :, None] * grid.xyz[:, None, :]
    direction /= np.maximum(np.linalg.norm(direction, axis=2, keepdims=True), 1e-12)
    alignment = np.einsum("mki,mi->mk", direction, wind)
    alignment = np.where(valid, alignment, -np.inf)
    chosen = np.argmax(alignment, axis=1)
    return safe[np.arange(grid.size), chosen]


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

    # ITCZ convection and subtropical subsidence.
    itcz = np.exp(-((lat / 10.0) ** 2))
    subtropical_dry = np.exp(-((abs_lat - 27.0) / 8.5) ** 2)
    precipitation = (
        precipitation * 950.0
        + 1600.0 * itcz * (0.35 + 0.65 * ocean_influence)
        - 500.0 * subtropical_dry * continentality
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

    # A coarse seasonal rainfall contrast; continental tropical/subtropical
    # cells receive the strongest monsoon tendency.
    monsoon = np.clip(
        continentality
        * np.exp(-((abs_lat - 20.0) / 16.0) ** 2)
        * (precipitation / 1800.0),
        0,
        1,
    )
    snow = np.where(land, np.clip((2.0 - coldest) / 22.0, 0, 1), 0.0)
    # Partial sea ice avoids the old opaque, straight white polar bars.
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
    )
