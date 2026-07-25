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
from .features import extract_features, features_to_geojson
from .model import WorldResult
from .navigation import chokepoint_geometry, navigation_to_geojson
from .theater import build_theater_overlays
from .tiles import MERCATOR_MAX_LAT, write_mercator_tiles
from .tiers import get_tier


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


def _split_antimeridian(coords: list[list[float]]) -> list[list[list[float]]]:
    """Split a polyline wherever consecutive longitudes jump more than 180°."""
    if len(coords) < 2:
        return []
    parts: list[list[list[float]]] = []
    current = [coords[0]]
    for previous, point in zip(coords, coords[1:]):
        if abs(point[0] - previous[0]) > 180.0:
            if len(current) >= 2:
                parts.append(current)
            current = [point]
        else:
            current.append(point)
    if len(current) >= 2:
        parts.append(current)
    return parts


def _ocean_endpoint(
    grid, land: np.ndarray, cell: int
) -> list[float]:
    """Lon/lat of the nearest ocean neighbour, else the cell itself."""
    neighbors = grid.neighbors[cell]
    neighbors = neighbors[neighbors >= 0]
    wet = neighbors[~land[neighbors]]
    if len(wet):
        target = int(wet[0])
        return [float(grid.lon_deg[target]), float(grid.lat_deg[target])]
    return [float(grid.lon_deg[cell]), float(grid.lat_deg[cell])]


def _river_geojson(world: WorldResult) -> dict:
    """Export rivers as continuous head→mouth polylines (not single edges)."""
    grid = world.grid
    river = world.hydrology.river_mask
    receiver = world.hydrology.receiver
    discharge = world.hydrology.discharge_m3_s
    drainage = world.hydrology.drainage_area_km2
    land = world.land

    river_cells = np.flatnonzero(river)
    upstream_count = np.zeros(grid.size, dtype=np.int32)
    for cell in river_cells:
        downstream = int(receiver[cell])
        if downstream >= 0 and river[downstream]:
            upstream_count[downstream] += 1
    heads = river_cells[upstream_count[river_cells] == 0]

    features: list[dict] = []
    for head in heads:
        path = [int(head)]
        current = int(head)
        while True:
            downstream = int(receiver[current])
            if downstream < 0 or not river[downstream]:
                break
            path.append(downstream)
            current = downstream

        coords = [
            [float(grid.lon_deg[cell]), float(grid.lat_deg[cell])] for cell in path
        ]
        # One-cell hop into the ocean so mouths visibly reach the coast.
        end = _ocean_endpoint(grid, land, path[-1])
        if end != coords[-1]:
            coords.append(end)

        mouth_cell = path[-1]
        mouth_discharge = float(discharge[mouth_cell])
        mouth_drainage = float(drainage[mouth_cell])

        parts = _split_antimeridian(coords)
        for index, part in enumerate(parts):
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "discharge_m3_s": round(mouth_discharge, 2),
                        "drainage_km2": round(mouth_drainage, 2),
                        "role": "mouth" if index == len(parts) - 1 else "reach",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": part,
                    },
                }
            )
    return {
        "type": "FeatureCollection",
        "name": "rivers-v2",
        "schema_version": "2.1",
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
    # Soften hard cubed-sphere cell edges before equirect sampling.
    for channel in range(base_cells.shape[1]):
        base_cells[:, channel] = grid.smooth(
            base_cells[:, channel], iterations=1, self_weight=3.5
        )
    base = grid.to_equirect(base_cells, width, height, blend=True)
    plates = grid.to_equirect(
        _palette(world.geology.plate_id, 11), width, height, blend=True
    )
    continents = grid.to_equirect(
        _palette(world.geology.continent_id, 23), width, height, blend=True
    )
    landmasses = grid.to_equirect(
        _palette(world.geology.landmass_id, 37), width, height, blend=True
    )
    climate_cells = np.stack(
        (
            np.clip((world.climate.temperature_c + 30) / 70, 0, 1),
            np.clip(world.climate.precipitation_mm_yr / 3000, 0, 1),
            np.clip(world.climate.humidity, 0, 1),
        ),
        axis=1,
    )
    for channel in range(climate_cells.shape[1]):
        climate_cells[:, channel] = grid.smooth(
            climate_cells[:, channel], iterations=1, self_weight=3.5
        )
    climate = grid.to_equirect(climate_cells, width, height, blend=True)
    settlement = grid.to_equirect(
        _heat_color(world.settlement.settle_ac, world.land),
        width,
        height,
        blend=True,
    )
    river_cells = base_cells.copy()
    river_cells[world.hydrology.river_mask] = (0.20, 0.65, 0.95)
    rivers_raster = grid.to_equirect(river_cells, width, height, blend=True)
    resources = _resource_overlay(world, base)

    resource_geojson = _resource_geojson(world)
    river_geojson = _river_geojson(world)
    settlement_geojson = _settlement_sites(world)
    feature_list = extract_features(world)
    feature_geojson = features_to_geojson(feature_list, world)
    navigation_geojson = navigation_to_geojson(world.navigation, world.grid)
    chokepoints = chokepoint_geometry(
        world.grid,
        world.geology.elevation_m,
        world.sea_level_m,
        world.navigation.chokepoint_mask,
    )
    deposit_counts: dict[str, int] = {}
    for deposit in world.deposits:
        deposit_counts[deposit.deposit_class] = (
            deposit_counts.get(deposit.deposit_class, 0) + 1
        )
    harbour = world.navigation.harbour_rating
    top_harbour = float(np.max(harbour)) if harbour.size else 0.0
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
        "features": {
            "count": len(feature_list),
        },
        "navigation": {
            "harbour_sites": int(np.sum(harbour >= 0.55)),
            "top_harbour_rating": round(top_harbour, 3),
            "chokepoint_count": len(chokepoints),
            "shelf_break_cells": int(np.sum(world.navigation.shelf_break_mask)),
            "chokepoints": chokepoints[:12],
        },
        "semantics": {
            "plate": "instantaneous rigid kinematic domain",
            "continent": "continental crust lineage / terrane",
            "landmass": "connected dry land",
        },
        "viewer_tiles": {
            "scheme": "xyz",
            "path": "tiles/color/{z}/{x}/{y}.png",
            "max_zoom": world.config.tile_deep_max_zoom,
            "global_max_zoom": world.config.tile_global_max_zoom,
            "deep_max_zoom": world.config.tile_deep_max_zoom,
            "mercator_max_lat": MERCATOR_MAX_LAT,
            "note": "MapLibre globe extends raster tiles to poles; image sources do not",
        },
        "config": {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in asdict(world.config).items()
        },
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
            theater_overlays = None
            if world.config.tile_deep_max_zoom > world.config.tile_global_max_zoom:
                # Nested refine target: prefer tier ladder spacing, else t2 (1 km).
                tier = get_tier(world.config.tier)
                target_km = float(tier.target_km) if tier.target_km else 1.0
                # Windowed tiers (t2–t4) already express local spacing; for global
                # parents use t2 (1 km) so deep tiles gain theater detail.
                if not tier.windowed:
                    target_km = 1.0
                theater_overlays = build_theater_overlays(
                    world.grid,
                    world.geology.elevation_m,
                    world.climate,
                    sea_level_m=world.sea_level_m,
                    windows=world.config.tile_deep_windows,
                    target_km=target_km,
                    seed=world.config.seed,
                    iterations=12,
                )
            tile_meta = write_mercator_tiles(
                base,
                destination / "tiles" / "color",
                global_max_zoom=world.config.tile_global_max_zoom,
                deep_max_zoom=world.config.tile_deep_max_zoom,
                deep_windows=world.config.tile_deep_windows,
                theater_overlays=theater_overlays,
            )
            meta["viewer_tiles"].update(tile_meta)
            if theater_overlays:
                meta["viewer_tiles"]["theater_target_km"] = target_km
                meta["viewer_tiles"]["theater_windows"] = [
                    ov.name for ov in theater_overlays
                ]
        (destination / f"world-resources{suffix}.geojson").write_text(
            json.dumps(resource_geojson, indent=2) + "\n"
        )
        (destination / f"world-rivers{suffix}.geojson").write_text(
            json.dumps(river_geojson, indent=2) + "\n"
        )
        (destination / f"world-settlement{suffix}.geojson").write_text(
            json.dumps(settlement_geojson, indent=2) + "\n"
        )
        (destination / f"world-features{suffix}.geojson").write_text(
            json.dumps(feature_geojson, indent=2) + "\n"
        )
        (destination / f"world-navigation{suffix}.geojson").write_text(
            json.dumps(navigation_geojson, indent=2) + "\n"
        )
        (destination / f"world-meta{suffix}.json").write_text(
            json.dumps(meta, indent=2) + "\n"
        )
    return meta
