"""Soils, water, coasts, fisheries, harbors, and passes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .climate import ClimateFields
from .grid import CubedSphere
from .hydrology import HydrologyFields


@dataclass
class EnvironmentFields:
    soil_fertility: np.ndarray
    aquifer_recharge_mm_yr: np.ndarray
    aquifer_potential: np.ndarray
    fishery_productivity: np.ndarray
    harbor_score: np.ndarray
    pass_score: np.ndarray
    slope: np.ndarray
    ruggedness: np.ndarray


def compute_environment(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    continental: np.ndarray,
    orogeny: np.ndarray,
    climate: ClimateFields,
    hydrology: HydrologyFields,
) -> EnvironmentFields:
    elevation = np.asarray(elevation_m, dtype=np.float64)
    land = elevation >= sea_level_m
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    neighbor_elevation = elevation[safe]
    difference = np.where(valid, np.abs(neighbor_elevation - elevation[:, None]), 0.0)
    ruggedness = np.clip(difference.max(axis=1) / 2200.0, 0, 1)
    slope = np.clip(difference.mean(axis=1) / 900.0, 0, 1)

    thermal_food = np.exp(-((climate.temperature_c - 17.0) / 16.0) ** 2)
    water_food = np.clip(
        climate.precipitation_mm_yr / 900.0, 0, 1
    ) * np.clip(1.8 - climate.precipitation_mm_yr / 2600.0, 0.2, 1)
    drainage_scale = max(
        float(np.percentile(hydrology.drainage_area_km2[land], 95))
        if np.any(land)
        else 1.0,
        1.0,
    )
    alluvial = np.clip(
        np.log1p(hydrology.drainage_area_km2)
        / np.log1p(drainage_scale),
        0,
        1,
    )
    fresh_minerals = np.clip(0.35 * continental + 0.45 * orogeny, 0, 1)
    fertility = (
        0.28 * thermal_food
        + 0.25 * water_food
        + 0.32 * alluvial
        + 0.15 * fresh_minerals
    )
    fertility *= (1.0 - 0.72 * slope) * (1.0 - 0.6 * climate.snow_fraction)
    fertility = np.where(land, np.clip(fertility, 0, 1), 0.0)

    recharge = np.clip(
        climate.precipitation_mm_yr - 0.7 * climate.pet_mm_yr, 0, None
    )
    storage = np.clip(
        0.45
        + 0.35 * (hydrology.depression_depth_m > 0)
        + 0.25 * (1.0 - orogeny)
        - 0.25 * slope,
        0,
        1,
    )
    aquifer = np.where(
        land, np.clip(recharge / 800.0, 0, 1) * storage, 0.0
    )

    ocean = ~land
    shelf = ocean & (elevation > sea_level_m - 700.0)
    river_nutrients = np.where(valid, hydrology.river_mask[safe], False).any(axis=1)
    east = np.cross(np.array([0.0, 0.0, 1.0]), grid.xyz)
    east /= np.maximum(np.linalg.norm(east, axis=1, keepdims=True), 1e-12)
    upwelling = np.abs(np.einsum("ij,ij->i", climate.wind_xyz, east))
    fishery = np.where(
        ocean,
        shelf.astype(float)
        * (0.35 + 0.35 * upwelling + 0.3 * river_nutrients.astype(float))
        * (1.0 - 0.75 * climate.sea_ice_fraction),
        0.0,
    )
    fishery = np.clip(fishery, 0, 1)

    ocean_neighbors = np.where(valid, ocean[safe], False).sum(axis=1)
    degree = np.maximum(valid.sum(axis=1), 1)
    ocean_fraction = ocean_neighbors / degree
    coastal = land & (ocean_neighbors > 0)
    shelter = np.exp(-((ocean_fraction - 0.35) / 0.28) ** 2)
    river_access = np.where(valid, hydrology.river_mask[safe], False).any(axis=1)
    harbor = np.where(
        coastal,
        shelter
        * (1.0 - 0.72 * slope)
        * (0.72 + 0.28 * river_access)
        * (1.0 - climate.snow_fraction * 0.35),
        0.0,
    )

    neighbor_mean = np.where(valid, neighbor_elevation, 0.0).sum(axis=1) / degree
    local_saddle = np.clip((neighbor_mean - elevation) / 900.0, 0, 1)
    mountain_context = np.clip((neighbor_mean - sea_level_m) / 1800.0, 0, 1)
    pass_score = np.where(
        land,
        local_saddle * mountain_context * (0.4 + 0.6 * ruggedness),
        0.0,
    )
    return EnvironmentFields(
        soil_fertility=fertility,
        aquifer_recharge_mm_yr=recharge,
        aquifer_potential=aquifer,
        fishery_productivity=fishery,
        harbor_score=np.clip(harbor, 0, 1),
        pass_score=np.clip(pass_score, 0, 1),
        slope=slope,
        ruggedness=ruggedness,
    )
