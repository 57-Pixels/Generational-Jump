"""End-to-end v2 world pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .climate import ClimateFields, compute_climate
from .environment import EnvironmentFields, compute_environment
from .geology import GeologyConfig, GeologyFields, simulate_geology
from .grid import CubedSphere
from .hydrology import HydrologyFields, compute_hydrology
from .plates import PlateModel
from .resources import Deposit, DepositContext, generate_deposits
from .settlement import (
    IncentiveFields,
    SettlementFields,
    SettlementInputs,
    compute_settlement,
)
from .topology import area_fraction, component_labels

EARTH_RADIUS_KM = 6371.0
# Fixed reference sea level on the elevation field. Land fraction is emergent.
PRESENT_SEA_LEVEL_M = 0.0
LGM_SEA_LEVEL_DROP_M = 120.0


@dataclass(frozen=True)
class WorldConfig:
    seed: int = 42
    grid_n: int = 64
    ticks: int = 80
    dt_ma: float = 8.0
    n_plates: int = 12
    n_continents: int = 7
    era: str = "present"
    export_width: int = 1024
    export_height: int = 512


@dataclass
class WorldResult:
    config: WorldConfig
    grid: CubedSphere
    plate_model: PlateModel
    geology: GeologyFields
    sea_level_m: float
    land: np.ndarray
    land_fraction: float
    climate: ClimateFields
    hydrology: HydrologyFields
    environment: EnvironmentFields
    deposits: list[Deposit]
    bulk_materials: dict[str, np.ndarray]
    incentives: IncentiveFields
    settlement: SettlementFields


def _deposit_context(
    world_grid: CubedSphere,
    geology: GeologyFields,
    sea_level_m: float,
    climate: ClimateFields,
    environment: EnvironmentFields,
) -> DepositContext:
    elevation = geology.elevation_m
    land = elevation >= sea_level_m
    water_depth = np.maximum(sea_level_m - elevation, 0.0)
    area_km2 = world_grid.area_sr * EARTH_RADIUS_KM**2
    h = geology.history
    l = geology.lithology
    p = geology.paleoclimate
    stable = np.clip(
        geology.continental * (1.0 - np.clip(geology.orogeny, 0, 1)), 0, 1
    )
    shelf = np.clip(
        (water_depth < 800.0).astype(float)
        * (water_depth > 0).astype(float)
        * (0.35 + 0.65 * geology.continental),
        0,
        1,
    )
    valid = world_grid.neighbors >= 0
    safe = np.where(valid, world_grid.neighbors, 0)
    coast = world_grid.smooth(
        (land & np.any(valid & (~land[safe]), axis=1)).astype(float), 2
    )
    factors = {
        "wetland": p["wetland"],
        "basin": geology.basin_depth,
        "organic_shale": l["organic_shale"],
        "maturity": np.clip(0.55 * geology.basin_depth + 0.35 * geology.sediment, 0, 1),
        "source": l["organic_shale"],
        "reservoir": l["sandstone"],
        "seal": np.clip(0.6 * geology.sediment + 0.35 * l["evaporite"], 0, 1),
        "trap": np.clip(0.55 * geology.basin_depth + 0.35 * h["collision"], 0, 1),
        "stable": stable,
        "felsic": l["felsic"],
        "ancient_craton": l["ancient_craton"],
        "exhumation": h["exhumation"],
        "weathering": p["tropical_weathering"],
        "shelf": shelf,
        "redox": np.clip(0.5 * geology.sediment + 0.4 * p["wetland"], 0, 1),
        "upwelling": p["upwelling"],
        "mafic": l["mafic"],
        "ultramafic": l["ultramafic"],
        "arc": h["arc"],
        "hydrothermal": h["hydrothermal"],
        "rift": h["continental_rift"],
        "rift_or_arc": np.maximum(h["continental_rift"], h["arc"]),
        "rift_or_alkaline": np.maximum(h["continental_rift"], h["alkaline"]),
        "collision": h["collision"],
        "collision_or_arc": np.maximum(h["collision"], h["arc"]),
        "sediment": geology.sediment,
        "restricted": np.clip(
            0.45 * geology.basin_depth
            + 0.55 * geology.sediment * p["aridity"] * (1.0 - coast),
            0,
            1,
        ),
        "brine": np.clip(
            0.45 * geology.basin_depth
            + 0.55 * geology.sediment * (0.35 + p["aridity"]),
            0,
            1,
        ),
        "carbonate": l["carbonate"],
        "alkaline": h["alkaline"],
        "heavy_mineral": l["heavy_mineral_source"],
        "coastal_reworking": np.clip(coast * geology.sediment, 0, 1),
        "closed": np.clip(
            land
            * geology.sediment
            * p["aridity"]
            * (1.0 - np.clip(geology.orogeny, 0, 1)),
            0,
            1,
        ),
        "aridity": p["aridity"],
        "quartz": l["quartz"],
        "purity": np.clip(l["quartz"] * (1.0 - l["mafic"]) * (1.0 - geology.sediment), 0, 1),
        "evaporite": l["evaporite"],
    }
    water_stress = np.clip(
        1.0 - climate.precipitation_mm_yr / np.maximum(climate.pet_mm_yr, 1.0),
        0,
        1,
    )
    return DepositContext(
        area_km2=area_km2,
        land=land,
        lon_deg=world_grid.lon_deg,
        lat_deg=world_grid.lat_deg,
        slope=environment.slope,
        ruggedness=environment.ruggedness,
        water_depth=water_depth,
        water_stress=water_stress,
        factors=factors,
    )


def _incentives(
    grid: CubedSphere,
    deposits: list[Deposit],
    environment: EnvironmentFields,
    hydrology: HydrologyFields,
) -> IncentiveFields:
    resource = np.zeros(grid.size)
    if deposits:
        lon = np.deg2rad(np.array([deposit.lon for deposit in deposits]))
        lat = np.deg2rad(np.array([deposit.lat for deposit in deposits]))
        xyz = np.stack(
            (np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)),
            axis=1,
        )
        cells = grid.indices_for_xyz(xyz)
        values = np.array(
            [
                np.clip(
                    0.35
                    + 0.25 * np.log10(max(deposit.reserve_2025_t, 1.0)) / 10.0
                    + 0.25 * deposit.accessibility,
                    0,
                    1,
                )
                for deposit in deposits
            ]
        )
        np.maximum.at(resource, cells, values)
        resource = grid.smooth(resource, iterations=3, self_weight=3.0)
        resource /= max(float(resource.max()), 1e-9)
    river_access = grid.smooth(hydrology.river_mask.astype(float), 2)
    trade = np.clip(
        0.65 * environment.harbor_score
        + 0.25 * river_access
        + 0.25 * hydrology.delta_score,
        0,
        1,
    )
    strategy = np.clip(
        0.7 * environment.pass_score + 0.25 * environment.harbor_score,
        0,
        1,
    )
    return IncentiveFields(
        resource=resource,
        trade=trade,
        strategy=strategy,
        policy=np.zeros(grid.size),
        institutional=np.zeros(grid.size),
    )


def _settlement_inputs(
    grid: CubedSphere,
    land: np.ndarray,
    climate: ClimateFields,
    environment: EnvironmentFields,
    hydrology: HydrologyFields,
    geology: GeologyFields,
    incentives: IncentiveFields,
) -> SettlementInputs:
    water = np.clip(
        0.58 * environment.aquifer_potential
        + 0.42 * hydrology.runoff_mm_yr / 1000.0,
        0,
        1,
    )
    food = environment.soil_fertility
    buildability = np.clip(
        1.0 - 0.65 * environment.slope - 0.45 * environment.ruggedness, 0, 1
    )
    disease = np.clip(
        1.0
        - 0.55
        * np.clip((climate.temperature_c - 18.0) / 14.0, 0, 1)
        * climate.humidity,
        0.15,
        1,
    )
    hazard = np.clip(
        1.0
        - 0.5 * np.clip(geology.orogeny, 0, 1)
        - 0.2 * hydrology.delta_score,
        0.1,
        1,
    )
    infrastructure = np.clip(
        0.5 + 0.3 * incentives.trade + 0.2 * incentives.resource, 0, 1
    )
    grid_reliability = np.where(
        land, np.clip(0.58 + 0.35 * infrastructure, 0, 0.96), 0
    )
    capital = np.where(land, np.clip(0.52 + 0.4 * incentives.trade, 0, 0.94), 0)
    energy = np.where(land, np.clip(0.58 + 0.3 * incentives.resource, 0, 0.92), 0)
    river_logistics = grid.smooth(hydrology.river_mask.astype(float), 2)
    logistics = np.clip(
        0.4 * buildability + 0.35 * incentives.trade + 0.25 * river_logistics, 0, 1
    )
    return SettlementInputs(
        land=land,
        temperature_c=climate.temperature_c,
        hottest_wet_bulb_c=climate.hottest_wet_bulb_c,
        coldest_month_c=climate.coldest_month_c,
        humidity=climate.humidity,
        water=water,
        food=food,
        buildability=buildability,
        disease_safety=disease,
        hazard_safety=hazard,
        grid_reliability=grid_reliability,
        capital_access=capital,
        energy_headroom=energy,
        cdd24=climate.cdd24,
        outdoor_labor_share=np.clip(0.55 - 0.25 * incentives.trade, 0.18, 0.65),
        service_energy=grid_reliability,
        service_water=np.clip(0.35 + 0.65 * water, 0, 1),
        service_food=np.clip(0.4 + 0.6 * food, 0, 1),
        logistics_access=logistics,
    )


def generate_world(config: WorldConfig) -> WorldResult:
    if config.era not in ("present", "lgm"):
        raise ValueError("era must be present or lgm")
    grid = CubedSphere.create(config.grid_n)
    geology, plate_model = simulate_geology(
        grid,
        GeologyConfig(
            seed=config.seed,
            ticks=config.ticks,
            dt_ma=config.dt_ma,
            n_plates=config.n_plates,
            n_continents=config.n_continents,
        ),
    )
    sea_level = (
        PRESENT_SEA_LEVEL_M
        if config.era == "present"
        else PRESENT_SEA_LEVEL_M - LGM_SEA_LEVEL_DROP_M
    )
    land = geology.elevation_m >= sea_level
    land_fraction = area_fraction(land, grid.area_sr)
    geology.landmass_id = component_labels(grid, land)
    climate = compute_climate(grid, geology.elevation_m, sea_level, era=config.era)
    hydrology = compute_hydrology(grid, geology.elevation_m, sea_level, climate)
    environment = compute_environment(
        grid,
        geology.elevation_m,
        sea_level,
        geology.continental,
        geology.orogeny,
        climate,
        hydrology,
    )
    deposit_context = _deposit_context(
        grid, geology, sea_level, climate, environment
    )
    deposits, bulk = generate_deposits(deposit_context, config.seed)
    incentives = _incentives(grid, deposits, environment, hydrology)
    inputs = _settlement_inputs(
        grid,
        land,
        climate,
        environment,
        hydrology,
        geology,
        incentives,
    )
    settlement = compute_settlement(inputs, incentives)
    return WorldResult(
        config=config,
        grid=grid,
        plate_model=plate_model,
        geology=geology,
        sea_level_m=sea_level,
        land=land,
        land_fraction=land_fraction,
        climate=climate,
        hydrology=hydrology,
        environment=environment,
        deposits=deposits,
        bulk_materials=bulk,
        incentives=incentives,
        settlement=settlement,
    )
