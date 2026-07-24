"""Export v2 spherical fields to viewer-friendly PNG and GeoJSON."""

from __future__ import annotations

import json
import math
import zlib
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .contract import GENERATOR_VERSION
from .model import WorldResult
from .tiles import MERCATOR_MAX_LAT, write_mercator_tiles


def _palette(values: np.ndarray, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    maximum = max(int(values.max()), 0)
    colors = rng.uniform(0.18, 0.92, size=(maximum + 2, 3))
    colors[0] = (0.08, 0.12, 0.20)
    index = np.where(values >= 0, values + 1, 0)
    return colors[index]


def _atlas_color(world: WorldResult) -> np.ndarray:
    grid = world.grid
    land = world.land
    elev = world.geology.elevation_m
    sea = world.sea_level_m
    temp = world.climate.temperature_c
    precip = world.climate.precipitation_mm_yr
    rgb = np.zeros((grid.size, 3), dtype=np.float64)

    depth = np.clip((sea - elev) / 5500.0, 0, 1)
    shallow = np.array([0.16, 0.42, 0.56])
    deep = np.array([0.035, 0.09, 0.23])
    rgb[~land] = shallow + (deep - shallow) * depth[~land, None]

    aridity = np.clip(
        1.0 - precip / np.maximum(world.climate.pet_mm_yr, 1.0), 0, 1
    )
    forest = np.clip((precip - 700.0) / 1700.0, 0, 1)
    cold = np.clip((5.0 - temp) / 25.0, 0, 1)
    desert_color = np.array([0.76, 0.65, 0.42])
    grass_color = np.array([0.43, 0.60, 0.31])
    forest_color = np.array([0.16, 0.42, 0.23])
    tundra_color = np.array([0.58, 0.62, 0.54])
    land_color = (
        aridity[:, None] * desert_color
        + (1.0 - aridity)[:, None]
        * ((1.0 - forest)[:, None] * grass_color + forest[:, None] * forest_color)
    )
    land_color = (
        land_color * (1.0 - 0.55 * cold[:, None])
        + tundra_color * 0.55 * cold[:, None]
    )
    shade = np.clip(0.82 + np.maximum(elev - sea, 0) / 5000.0, 0.65, 1.18)
    land_color *= shade[:, None]
    snow = world.climate.snow_fraction[:, None]
    land_color = land_color * (1.0 - 0.72 * snow) + np.array([0.92, 0.94, 0.95]) * (
        0.72 * snow
    )
    rgb[land] = land_color[land]

    sea_ice = world.climate.sea_ice_fraction[:, None]
    rgb[~land] = rgb[~land] * (1.0 - 0.55 * sea_ice[~land]) + np.array(
        [0.70, 0.79, 0.84]
    ) * (0.55 * sea_ice[~land])
    return np.clip(rgb, 0, 1)


def _heat_color(score: np.ndarray, land: np.ndarray) -> np.ndarray:
    score = np.clip(score, 0, 1)
    rgb = np.stack(
        (
            np.clip(1.8 * score, 0, 1),
            np.clip(1.8 * (1.0 - np.abs(score - 0.55) * 1.8), 0, 1),
            np.clip(1.5 * (1.0 - score), 0, 1),
        ),
        axis=1,
    )
    rgb[~land] = (0.04, 0.10, 0.22)
    return rgb


def _save_rgb(path: Path, rgb: np.ndarray) -> None:
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), mode="RGB").save(path)


def _irregular_ring(
    lon: float,
    lat: float,
    seed_key: str,
    scale_deg: float,
    vertices: int = 7,
) -> list[list[float]]:
    """Deterministic non-circular footprint around a lon/lat point."""
    digest = zlib.crc32(seed_key.encode("utf-8")) & 0xFFFFFFFF
    rng = np.random.default_rng(digest)
    cos_lat = max(math.cos(math.radians(lat)), 0.2)
    ring: list[list[float]] = []
    for index in range(vertices):
        angle = (2.0 * math.pi * index) / vertices + float(rng.uniform(-0.35, 0.35))
        radius = scale_deg * float(rng.uniform(0.40, 1.25))
        ring.append(
            [
                lon + (radius * math.cos(angle)) / cos_lat,
                lat + radius * math.sin(angle),
            ]
        )
    ring.append(ring[0])
    return ring


def _resource_geojson(world: WorldResult) -> dict:
    features = []
    for deposit in world.deposits:
        scale = 0.55 + 0.55 * min(math.log10(max(deposit.reserve_2025_t, 10.0)) / 10.0, 1.0)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "id": deposit.id,
                    "resource": deposit.deposit_class,
                    "name": deposit.name,
                    "prospect_score": round(deposit.prospect_score, 4),
                    "ore_resource_t": round(deposit.ore_resource_t, 2),
                    "grade": json.dumps(deposit.grade, sort_keys=True),
                    "depth_m": round(deposit.depth_m, 1),
                    "accessibility": round(deposit.accessibility, 4),
                    "processing_difficulty": round(
                        deposit.processing_difficulty, 4
                    ),
                    "recovery": round(deposit.recovery, 4),
                    "reserve_2025_t": round(deposit.reserve_2025_t, 2),
                    "byproducts": ", ".join(deposit.byproducts),
                    "lon": deposit.lon,
                    "lat": deposit.lat,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        _irregular_ring(
                            deposit.lon,
                            deposit.lat,
                            deposit.id,
                            scale_deg=scale,
                        )
                    ],
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "geological-resources-v2",
        "schema_version": "2.1",
        "features": features,
    }


def _river_geojson(world: WorldResult) -> dict:
    features: list[dict] = []
    for cell in np.flatnonzero(world.hydrology.river_mask):
        receiver = int(world.hydrology.receiver[cell])
        if receiver < 0:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "discharge_m3_s": round(
                        float(world.hydrology.discharge_m3_s[cell]), 2
                    ),
                    "drainage_km2": round(
                        float(world.hydrology.drainage_area_km2[cell]), 2
                    ),
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [
                            float(world.grid.lon_deg[cell]),
                            float(world.grid.lat_deg[cell]),
                        ],
                        [
                            float(world.grid.lon_deg[receiver]),
                            float(world.grid.lat_deg[receiver]),
                        ],
                    ],
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "rivers-v2",
        "schema_version": "2.0",
        "features": features,
    }


def _settlement_sites(world: WorldResult, maximum: int = 120) -> dict:
    score = world.settlement.settle_ac.copy()
    score[~world.land] = -1
    chosen: list[int] = []
    work = score.copy()
    for _ in range(maximum):
        cell = int(np.argmax(work))
        if work[cell] < 0.32:
            break
        chosen.append(cell)
        work[cell] = -1
        neighbors = world.grid.neighbors[cell]
        work[neighbors[neighbors >= 0]] = -1
    features = []
    for rank, cell in enumerate(chosen, start=1):
        lon = float(world.grid.lon_deg[cell])
        lat = float(world.grid.lat_deg[cell])
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "rank": rank,
                    "h_pre": round(float(world.settlement.h_pre[cell]), 4),
                    "h_ind": round(float(world.settlement.h_ind[cell]), 4),
                    "h_ac": round(float(world.settlement.h_ac[cell]), 4),
                    "settle_ind": round(
                        float(world.settlement.settle_ind[cell]), 4
                    ),
                    "settle_ac": round(float(world.settlement.settle_ac[cell]), 4),
                    "settle_no_incentive": round(
                        float(world.settlement.settle_ind_no_incentive[cell]), 4
                    ),
                    "mechanism": str(world.settlement.mechanism_ac[cell]),
                    "dominant_incentive": str(
                        world.settlement.dominant_incentive[cell]
                    ),
                    "ac_kwh_pc_yr": round(
                        float(
                            world.settlement.ac_energy_served_kwh_pc_yr[cell]
                        ),
                        1,
                    ),
                    "ac_water_l_pc_day": round(
                        float(world.settlement.ac_water_l_pc_day[cell]), 2
                    ),
                    "lon": lon,
                    "lat": lat,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        _irregular_ring(
                            lon, lat, f"settle-{rank}-{cell}", scale_deg=0.7
                        )
                    ],
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "name": "settlement-sites-v2",
        "schema_version": "2.1",
        "features": features,
    }


def _resource_overlay(world: WorldResult, base: np.ndarray) -> np.ndarray:
    height, width, _ = base.shape
    image = Image.fromarray((base * 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(image)
    for deposit in world.deposits:
        scale = 2.5 + 2.0 * min(math.log10(max(deposit.reserve_2025_t, 10.0)) / 10.0, 1.0)
        ring = _irregular_ring(deposit.lon, deposit.lat, deposit.id, scale_deg=scale)
        pixels = []
        for lon, lat in ring[:-1]:
            x = int((lon + 180.0) / 360.0 * width) % width
            y = int(np.clip((90.0 - lat) / 180.0 * height, 0, height - 1))
            pixels.append((x, y))
        hue = zlib.crc32(deposit.deposit_class.encode("utf-8")) & 0xFFFFFF
        color = ((hue >> 16) & 255, (hue >> 8) & 255, hue & 255)
        if len(pixels) >= 3:
            draw.polygon(pixels, fill=color, outline=(15, 15, 15))
    return np.asarray(image).astype(np.float64) / 255.0


def save_world(world: WorldResult, destinations: list[Path]) -> dict:
    suffix = "" if world.config.era == "present" else f"-{world.config.era}"
    width = world.config.export_width
    height = world.config.export_height
    grid = world.grid

    base_cells = _atlas_color(world)
    base = grid.to_equirect(base_cells, width, height)
    plates = grid.to_equirect(_palette(world.geology.plate_id, 11), width, height)
    continents = grid.to_equirect(
        _palette(world.geology.continent_id, 23), width, height
    )
    landmasses = grid.to_equirect(
        _palette(world.geology.landmass_id, 37), width, height
    )
    climate_cells = np.stack(
        (
            np.clip((world.climate.temperature_c + 30) / 70, 0, 1),
            np.clip(world.climate.precipitation_mm_yr / 3000, 0, 1),
            np.clip(world.climate.humidity, 0, 1),
        ),
        axis=1,
    )
    climate = grid.to_equirect(climate_cells, width, height)
    settlement = grid.to_equirect(
        _heat_color(world.settlement.settle_ac, world.land), width, height
    )
    river_cells = base_cells.copy()
    river_cells[world.hydrology.river_mask] = (0.20, 0.65, 0.95)
    rivers_raster = grid.to_equirect(river_cells, width, height)
    resources = _resource_overlay(world, base)

    resource_geojson = _resource_geojson(world)
    river_geojson = _river_geojson(world)
    settlement_geojson = _settlement_sites(world)
    deposit_counts: dict[str, int] = {}
    for deposit in world.deposits:
        deposit_counts[deposit.deposit_class] = (
            deposit_counts.get(deposit.deposit_class, 0) + 1
        )
    meta = {
        "method": "deeptime-spherical-v2",
        "generator_version": GENERATOR_VERSION,
        "seed": world.config.seed,
        "era": world.config.era,
        "grid": {
            "kind": "cubed-sphere",
            "face_n": world.config.grid_n,
            "cells": world.grid.size,
        },
        "ticks": world.config.ticks,
        "ma_per_tick": world.config.dt_ma,
        "sea_level_m": world.sea_level_m,
        "land_fraction": world.land_fraction,
        "land_fraction_emergent": True,
        "plate_count": len(world.plate_model.seed_xyz),
        "continent_count": len(
            np.unique(world.geology.continent_id[world.geology.continent_id >= 0])
        ),
        "landmass_count": len(
            np.unique(world.geology.landmass_id[world.geology.landmass_id >= 0])
        ),
        "resource_deposit_count": len(world.deposits),
        "resource_counts": deposit_counts,
        "settlement": {
            "ac_changes_habitability": True,
            "habitability_separate_from_incentives": True,
            "site_count": len(settlement_geojson["features"]),
        },
        "semantics": {
            "plate": "instantaneous rigid kinematic domain",
            "continent": "continental crust lineage / terrane",
            "landmass": "connected dry land",
        },
        "viewer_tiles": {
            "scheme": "xyz",
            "path": "tiles/color/{z}/{x}/{y}.png",
            "max_zoom": 3,
            "mercator_max_lat": MERCATOR_MAX_LAT,
            "note": "MapLibre globe extends raster tiles to poles; image sources do not",
        },
        "config": asdict(world.config),
    }

    for destination in destinations:
        destination.mkdir(parents=True, exist_ok=True)
        _save_rgb(destination / f"world-color{suffix}.png", base)
        _save_rgb(destination / f"world-plates{suffix}.png", plates)
        _save_rgb(destination / f"world-continents{suffix}.png", continents)
        _save_rgb(destination / f"world-landmasses{suffix}.png", landmasses)
        _save_rgb(destination / f"world-climate{suffix}.png", climate)
        _save_rgb(destination / f"world-rivers{suffix}.png", rivers_raster)
        _save_rgb(destination / f"world-resources{suffix}.png", resources)
        _save_rgb(destination / f"world-settlement{suffix}.png", settlement)
        if world.config.era == "present":
            tile_meta = write_mercator_tiles(
                base, destination / "tiles" / "color", max_zoom=3
            )
            meta["viewer_tiles"].update(tile_meta)
        (destination / f"world-resources{suffix}.geojson").write_text(
            json.dumps(resource_geojson, indent=2) + "\n"
        )
        (destination / f"world-rivers{suffix}.geojson").write_text(
            json.dumps(river_geojson, indent=2) + "\n"
        )
        (destination / f"world-settlement{suffix}.geojson").write_text(
            json.dumps(settlement_geojson, indent=2) + "\n"
        )
        (destination / f"world-meta{suffix}.json").write_text(
            json.dumps(meta, indent=2) + "\n"
        )
    return meta
