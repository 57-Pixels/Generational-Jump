"""Canon anchoring: score generated worlds against Veldara geography constraints."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .contract import GENERATOR_VERSION
from .grid import CubedSphere
from .model import WorldConfig, generate_world
from .topology import component_labels

EARTH_RADIUS_KM = 6371.0
KM2_PER_SR = EARTH_RADIUS_KM**2
PASS_THRESHOLD = 0.5
CONSTRAINTS = (
    "continent_scale",
    "veldara_claim",
    "west_cordillera",
    "gulf",
    "highspine",
    "eastmarch",
    "farreach",
    "harbours",
)


@dataclass(frozen=True)
class AnchorScore:
    continent_scale: float
    veldara_claim: float
    west_cordillera: float
    gulf: float
    highspine: float
    eastmarch: float
    farreach: float
    harbours: float
    region_cells: np.ndarray = field(repr=False)

    @property
    def total(self) -> float:
        parts = tuple(getattr(self, name) for name in CONSTRAINTS)
        return float(sum(parts) / len(parts))

    def as_dict(self) -> dict[str, float]:
        out = {name: float(getattr(self, name)) for name in CONSTRAINTS}
        out["total"] = self.total
        return out

    def passes(self, threshold: float = PASS_THRESHOLD) -> bool:
        return all(float(getattr(self, name)) >= threshold for name in CONSTRAINTS)

    def failing(self, threshold: float = PASS_THRESHOLD) -> list[str]:
        return [
            name
            for name in CONSTRAINTS
            if float(getattr(self, name)) < threshold
        ]


def _cell_area_km2(grid: CubedSphere) -> np.ndarray:
    return grid.area_sr * KM2_PER_SR


def _largest_landmass(
    grid: CubedSphere, land: np.ndarray
) -> tuple[int, np.ndarray, float]:
    labels = component_labels(grid, land)
    best_id = -1
    best_area = 0.0
    area = _cell_area_km2(grid)
    for lid in np.unique(labels):
        if lid < 0:
            continue
        mask = labels == lid
        a = float(area[mask].sum())
        if a > best_area:
            best_area = a
            best_id = int(lid)
    mask = labels == best_id if best_id >= 0 else np.zeros(grid.size, dtype=bool)
    return best_id, mask, best_area


def _size_score_20_35(area_km2: float) -> float:
    if area_km2 <= 0:
        return 0.0
    if 20.0e6 <= area_km2 <= 35.0e6:
        return 1.0
    if 12.0e6 <= area_km2 < 20.0e6:
        return (area_km2 - 12.0e6) / 8.0e6
    if 35.0e6 < area_km2 <= 55.0e6:
        return max(0.0, 1.0 - (area_km2 - 35.0e6) / 20.0e6)
    return 0.0


def _score_continent_scale(
    grid: CubedSphere, land: np.ndarray, plate_ids: np.ndarray
) -> float:
    """Aurelian-scale mass: a landmass or plate domain in the 20–35M km² band."""
    area = _cell_area_km2(grid)
    labels = component_labels(grid, land)
    best = 0.0
    for lid in np.unique(labels):
        if lid < 0:
            continue
        mask = labels == lid
        best = max(best, _size_score_20_35(float(area[mask].sum())))
        for pid in np.unique(plate_ids[mask]):
            plate_mask = mask & (plate_ids == pid)
            best = max(best, _size_score_20_35(float(area[plate_mask].sum())))
    return float(np.clip(best, 0.0, 1.0))


def _grow_region(
    grid: CubedSphere,
    landmass: np.ndarray,
    seed: int,
    elevation: np.ndarray | None = None,
    target_km2: float = 3.2e6,
) -> np.ndarray:
    area = _cell_area_km2(grid)
    chosen = np.zeros(grid.size, dtype=bool)
    if seed < 0 or not landmass[seed]:
        return chosen
    # Prefer near-seed cells; slight bias toward lower inland elevations (plains).
    dots = grid.xyz @ grid.xyz[seed]
    if elevation is None:
        order = np.argsort(-dots)
    else:
        elev = np.asarray(elevation, dtype=np.float64)
        score = dots - 0.00015 * np.clip(elev, 0.0, 5000.0)
        score = np.where(landmass, score, -np.inf)
        order = np.argsort(-score)
    running = 0.0
    for cell in order:
        if not landmass[cell]:
            continue
        chosen[cell] = True
        running += float(area[cell])
        if running >= target_km2:
            break
    return chosen


def _pick_veldara_region(
    grid: CubedSphere,
    landmass: np.ndarray,
    elevation: np.ndarray,
    plate_id: np.ndarray,
    glacial_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Pick a ~3.2M km² claim maximizing cordillera + gulf + Eastmarch fit."""
    if not np.any(landmass):
        return np.zeros(grid.size, dtype=bool)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    land = elevation >= 0.0
    ocean = ~land
    coastal = landmass & (np.abs(grid.lat_deg) < 55.0) & np.any(
        valid & ocean[safe], axis=1
    )
    if not np.any(coastal):
        coastal = landmass & np.any(valid & ocean[safe], axis=1)
    seeds = np.flatnonzero(coastal)
    if seeds.size == 0:
        seeds = np.flatnonzero(landmass)
    # Subsample coastal seeds for speed.
    rng = np.random.default_rng(0)
    if seeds.size > 48:
        seeds = rng.choice(seeds, size=48, replace=False)
    best = np.zeros(grid.size, dtype=bool)
    best_score = -1.0
    for seed in seeds:
        region = _grow_region(grid, landmass, int(seed), elevation=elevation)
        if not np.any(region):
            continue
        score = (
            _score_veldara_claim(grid, region, elevation)
            + _score_west_cordillera(grid, region, elevation)
            + _score_gulf(grid, region, elevation)
            + score_eastmarch(
                grid, elevation, plate_id, region, glacial_mask=glacial_mask
            )
            + _score_highspine(grid, region, elevation)
            + _score_harbours(grid, region, elevation)
            + 1.5 * _score_farreach(grid, region, elevation)
        )
        if score > best_score:
            best_score = score
            best = region
    return best


def _score_veldara_claim(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    if not np.any(region):
        return 0.0
    area = float(_cell_area_km2(grid)[region].sum())
    size = float(np.exp(-0.5 * ((area - 3.2e6) / 1.2e6) ** 2))
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coastal):
        return 0.0
    lon_span = float(grid.lon_deg[coastal].max() - grid.lon_deg[coastal].min())
    access = np.clip(lon_span / 40.0, 0.0, 1.0)
    return float(np.clip(0.55 * size + 0.45 * access, 0.0, 1.0))


def _score_west_cordillera(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    if not np.any(region):
        return 0.0
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coastal):
        return 0.0
    west_lon = float(np.percentile(grid.lon_deg[coastal], 15))
    near_west = region & (grid.lon_deg < west_lon + 12.0)
    high = near_west & (elevation > 1200.0)
    if not np.any(high):
        return 0.0
    dlat = float(grid.lat_deg[high].max() - grid.lat_deg[high].min())
    dlon = float(grid.lon_deg[high].max() - grid.lon_deg[high].min())
    parallel = np.clip(dlat / max(dlon, 1.0) / 2.0, 0.0, 1.0)
    presence = np.clip(float(high.sum()) / max(float(near_west.sum()), 1.0) * 4.0, 0.0, 1.0)
    return float(np.clip(0.5 * presence + 0.5 * parallel, 0.0, 1.0))


def _score_gulf(grid: CubedSphere, region: np.ndarray, elevation: np.ndarray) -> float:
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    near_region = ocean & np.any(valid & region[safe], axis=1)
    if not np.any(near_region):
        return 0.0
    enclosure = np.zeros(grid.size, dtype=np.float64)
    enclosure[near_region] = (
        np.where(valid[near_region], land[safe[near_region]], False).sum(axis=1)
        / np.maximum(valid[near_region].sum(axis=1), 1)
    )
    embayment = near_region & (enclosure > 0.45)
    if not np.any(embayment):
        return 0.0
    area = float(_cell_area_km2(grid)[embayment].sum())
    return float(np.clip(area / 150_000.0, 0.0, 1.0))


def _score_highspine(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    if not np.any(region):
        return 0.0
    interior = region.copy()
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    land = elevation >= 0.0
    ocean = ~land
    coastal = region & np.any(valid & ocean[safe], axis=1)
    interior[coastal] = False
    high = interior & (elevation > 1500.0)
    if not np.any(high):
        return 0.0
    lon_min = float(grid.lon_deg[high].min())
    lon_max = float(grid.lon_deg[high].max())
    mid_lat = float(np.median(grid.lat_deg[high]))
    band = (
        region
        & (np.abs(grid.lat_deg - mid_lat) < 8.0)
        & (grid.lon_deg >= lon_min - 2.0)
        & (grid.lon_deg <= lon_max + 2.0)
    )
    if not np.any(band):
        return 0.0
    passable = band & (elevation < 2000.0)
    has_pass = np.any(passable) and float(passable.sum()) >= 3
    range_score = np.clip(float(high.sum()) / 8.0, 0.0, 1.0)
    return float(np.clip(0.5 * range_score + (0.5 if has_pass else 0.0), 0.0, 1.0))


def score_eastmarch(
    grid: CubedSphere,
    elevation: np.ndarray,
    plate_id: np.ndarray,
    region: np.ndarray,
    *,
    glacial_mask: np.ndarray | None = None,
) -> float:
    """Eastmarch plain: long, low relief, no plate boundary, unglaciated.

    Scored on the eastern fringe of the claim (east of the 65th lon percentile)
    so the Highspine cordillera further west does not false-fail the plain.
    """
    if not np.any(region):
        return 0.0
    lon = grid.lon_deg
    east_lo = float(np.percentile(lon[region], 65))
    zone = region & (lon >= east_lo) & (elevation >= 0.0)
    # Continuous orogenic wall across the fringe → hard fail.
    high = zone & (elevation > 1500.0)
    if np.any(high) and int(high.sum()) >= 4:
        lat_span_high = float(grid.lat_deg[high].max() - grid.lat_deg[high].min())
        lat_span_zone = float(grid.lat_deg[zone].max() - grid.lat_deg[zone].min())
        if lat_span_zone > 1e-6 and lat_span_high / lat_span_zone >= 0.55:
            return 0.0
    plain = zone & (elevation < 600.0)
    if int(plain.sum()) < 5:
        return 0.0
    plates = plate_id[plain]
    vals, counts = np.unique(plates, return_counts=True)
    if len(vals) > 1 and float(counts.max()) / float(counts.sum()) < 0.98:
        return 0.0
    dlon = float(lon[plain].max() - lon[plain].min())
    dlat = float(grid.lat_deg[plain].max() - grid.lat_deg[plain].min())
    length_km = max(dlon, dlat) * 111.0
    length_score = np.clip(length_km / 800.0, 0.0, 1.0)
    relief = float(elevation[plain].max() - elevation[plain].min())
    relief_score = (
        1.0
        if relief < 300.0
        else float(np.clip(1.0 - (relief - 300.0) / 700.0, 0.0, 1.0))
    )
    glacial_score = (
        0.0
        if glacial_mask is not None and np.any(glacial_mask[plain])
        else 1.0
    )
    return float(
        np.clip(
            0.4 * length_score + 0.4 * relief_score + 0.2 * glacial_score,
            0.0,
            1.0,
        )
    )


def _score_farreach(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    land = elevation >= 0.0
    if not np.any(region):
        return 0.0
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    ocean = ~land
    coast = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coast):
        # Fall back to any claim cell as a distance origin.
        coast = region
    coast_xyz = grid.xyz[coast]
    labels = component_labels(grid, land)
    # Main continent id(s) covered by the claim.
    claim_ids = set(int(x) for x in np.unique(labels[region]) if x >= 0)
    best = 0.0
    group_near = 0
    for lid in np.unique(labels):
        if lid < 0 or int(lid) in claim_ids:
            continue
        mask = labels == lid
        size = int(mask.sum())
        # Offshore fragments / island arcs — exclude second continents.
        if size < 1 or size > 200:
            continue
        center = grid.xyz[mask].mean(axis=0)
        norm = float(np.linalg.norm(center))
        if norm < 1e-12:
            continue
        center = center / norm
        dots = coast_xyz @ center
        ang = float(np.arccos(np.clip(float(dots.max()), -1.0, 1.0)))
        dist_km = ang * EARTH_RADIUS_KM
        if dist_km <= 1500.0:
            best = max(best, 1.0 - dist_km / 1500.0)
            group_near += 1
    # Bonus when several offshore fragments form an island group.
    if group_near >= 3:
        best = min(1.0, best + 0.25)
    elif group_near >= 2:
        best = min(1.0, best + 0.1)
    return float(best)


def _score_harbours(
    grid: CubedSphere, region: np.ndarray, elevation: np.ndarray
) -> float:
    land = elevation >= 0.0
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    coastal = region & np.any(valid & ocean[safe], axis=1)
    if not np.any(coastal):
        return 0.0
    deep = np.any(valid & (elevation[safe] < -40.0), axis=1)
    embayed = np.where(valid, ocean[safe], False).sum(axis=1) >= 2
    harbours = coastal & deep & embayed
    n = int(harbours.sum())
    return float(np.clip(n / 2.0, 0.0, 1.0))


def score_world(world: Any) -> AnchorScore:
    """Score a generated world against the eight Veldara canon constraints."""
    grid = world.grid
    elevation = world.geology.elevation_m
    land = elevation >= world.sea_level_m
    glacial = None
    if getattr(world, "climate", None) is not None:
        glacial = (world.climate.coldest_month_c < -15.0) & (
            world.climate.snow_fraction > 0.55
        )
    continent = _score_continent_scale(grid, land, world.geology.plate_id)
    _, landmass, _ = _largest_landmass(grid, land)
    region = _pick_veldara_region(
        grid, landmass, elevation, world.geology.plate_id, glacial_mask=glacial
    )
    return AnchorScore(
        continent_scale=continent,
        veldara_claim=_score_veldara_claim(grid, region, elevation),
        west_cordillera=_score_west_cordillera(grid, region, elevation),
        gulf=_score_gulf(grid, region, elevation),
        highspine=_score_highspine(grid, region, elevation),
        eastmarch=score_eastmarch(
            grid, elevation, world.geology.plate_id, region, glacial_mask=glacial
        ),
        farreach=_score_farreach(grid, region, elevation),
        harbours=_score_harbours(grid, region, elevation),
        region_cells=np.flatnonzero(region),
    )


@dataclass
class SweepResult:
    seed: int
    score: AnchorScore
    land_fraction: float
    grid_n: int
    ticks: int
    tier: str


def sweep_seeds(
    seeds: Iterable[int],
    *,
    grid_n: int = 64,
    ticks: int = 40,
    tier: str = "dev",
    use_cache: bool = True,
) -> list[SweepResult]:
    """Generate and score each seed; sorted best-total first, then lower seed."""
    results: list[SweepResult] = []
    for seed in seeds:
        world = generate_world(
            WorldConfig(
                seed=int(seed),
                grid_n=grid_n,
                ticks=ticks,
                tier=tier,
                use_cache=use_cache,
                validate=False,
            )
        )
        score = score_world(world)
        results.append(
            SweepResult(
                seed=int(seed),
                score=score,
                land_fraction=float(world.land_fraction),
                grid_n=int(world.config.grid_n),
                ticks=ticks,
                tier=tier,
            )
        )
    results.sort(key=lambda r: (-r.score.total, r.seed))
    return results


def promote_best(
    results: list[SweepResult],
    destination: Path,
    *,
    threshold: float = PASS_THRESHOLD,
) -> dict[str, Any]:
    """Write promoted-seed.json from the best passing result, or report failure."""
    destination = Path(destination)
    passing = [r for r in results if r.score.passes(threshold)]
    payload: dict[str, Any]
    if passing:
        best = passing[0]
        payload = {
            "status": "promoted",
            "seed": best.seed,
            "generator_version": GENERATOR_VERSION,
            "tier": best.tier,
            "grid_n": best.grid_n,
            "ticks": best.ticks,
            "land_fraction": best.land_fraction,
            "threshold": threshold,
            "scores": best.score.as_dict(),
            "region_cell_count": int(best.score.region_cells.size),
            "candidates_scored": len(results),
            "candidates_passing": len(passing),
        }
    else:
        # Aggregate which constraints never cleared the threshold.
        fail_counts = {name: 0 for name in CONSTRAINTS}
        for r in results:
            for name in r.score.failing(threshold):
                fail_counts[name] += 1
        best = results[0] if results else None
        payload = {
            "status": "unreachable",
            "generator_version": GENERATOR_VERSION,
            "threshold": threshold,
            "candidates_scored": len(results),
            "candidates_passing": 0,
            "failure_counts": fail_counts,
            "best_seed": None if best is None else best.seed,
            "best_scores": None if best is None else best.score.as_dict(),
            "note": (
                "No seed passed all eight constraints. Do not loosen thresholds; "
                "inspect failure_counts for phase-2 physics gaps."
            ),
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n")
    return payload
