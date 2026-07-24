"""Deep-time plate tectonics simulator (v1).

Continents form by rift / subduction / collision over Ma ticks.
Canon: docs/superpowers/specs/2026-07-24-world-generation-design.md
       world/05-planetary-formation.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .resources import RESOURCE_CATALOG, build_resources, deposits_geojson

ROOT = Path(__file__).resolve().parent
GENERATOR = ROOT.parent
EXPORTS = GENERATOR.parent / "exports"
VIEWER_WORLD = GENERATOR.parent / "viewer" / "public" / "world"

TARGET_LAND = 0.29
LAND_TOL = 0.03


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def lonlat_grids(h: int, w: int) -> tuple[np.ndarray, np.ndarray]:
    lon = np.linspace(-180.0, 180.0, w, endpoint=False)
    lat = np.linspace(90.0, -90.0, h)
    return np.meshgrid(lon, lat)


def area_weights(lat: np.ndarray) -> np.ndarray:
    """Relative cell area on a sphere (cos latitude)."""
    return np.clip(np.cos(np.deg2rad(lat)), 0.05, None)


@dataclass
class SimConfig:
    width: int = 1024
    height: int = 512
    seed: int = 42
    ticks: int = 80
    ma_per_tick: float = 8.0  # ~640 Ma spanned
    n_continental_seeds: int = 7
    n_oceanic_plates: int = 5
    target_land: float = TARGET_LAND
    era: str = "present"  # present | lgm


@dataclass
class SimResult:
    elev: np.ndarray
    sea: float
    continental: np.ndarray
    plate_id: np.ndarray
    orogeny: np.ndarray
    land_fraction: float
    color: np.ndarray
    height_u8: np.ndarray
    meta: dict = field(default_factory=dict)
    resources_overlay: np.ndarray | None = None
    resources_geojson: dict | None = None


def _seed_cratons(
    h: int, w: int, lat: np.ndarray, lon: np.ndarray, rng: np.random.Generator, n: int
) -> np.ndarray:
    """Boolean continental crust from scattered craton ellipses (initial only)."""
    cont = np.zeros((h, w), dtype=np.float64)
    # Bias seeds away from poles for usable mid-latitude boards
    for _ in range(n):
        clon = float(rng.uniform(-180, 180))
        clat = float(rng.uniform(-50, 55))
        rlon = float(rng.uniform(18, 42))
        rlat = float(rng.uniform(12, 28))
        dlon = (lon - clon + 180.0) % 360.0 - 180.0
        u = (dlon / rlon) ** 2 + ((lat - clat) / rlat) ** 2
        cont = np.maximum(cont, smoothstep(1.2, 0.45, np.sqrt(u)))
    return np.clip(cont, 0, 1)


def _assign_plates(
    cont: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    rng: np.random.Generator,
    n_cont_seeds: int,
    n_ocean_plates: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Voronoi-ish plates from seeds. Returns plate_id, vel_lon, vel_lat per plate."""
    h, w = cont.shape
    seeds: list[tuple[float, float, int]] = []
    # Continental plate seeds on high-cont cells
    ys, xs = np.where(cont > 0.55)
    if len(ys) < n_cont_seeds:
        ys, xs = np.where(cont > 0.25)
    pick = rng.choice(len(ys), size=min(n_cont_seeds, len(ys)), replace=False)
    for i, idx in enumerate(pick):
        seeds.append((float(lon[ys[idx], xs[idx]]), float(lat[ys[idx], xs[idx]]), i))

    n_c = len(seeds)
    for j in range(n_ocean_plates):
        seeds.append((float(rng.uniform(-180, 180)), float(rng.uniform(-60, 60)), n_c + j))

    n_plates = len(seeds)
    # Velocities: deg per tick (small)
    vel_lon = rng.normal(0, 1.8, size=n_plates)
    vel_lat = rng.normal(0, 1.0, size=n_plates)
    # Damp polar nonsense
    for i, (_, slat, _) in enumerate(seeds):
        vel_lat[i] *= 0.6
        if abs(slat) > 50:
            vel_lon[i] *= 0.5

    plate = np.zeros((h, w), dtype=np.int32)
    # Chunked nearest seed (wrap lon)
    seed_lon = np.array([s[0] for s in seeds])
    seed_lat = np.array([s[1] for s in seeds])
    # Process in row blocks for memory
    for y0 in range(0, h, 32):
        y1 = min(h, y0 + 32)
        block_lon = lon[y0:y1]
        block_lat = lat[y0:y1]
        best_d = np.full(block_lon.shape, np.inf)
        best_id = np.zeros(block_lon.shape, dtype=np.int32)
        for pid in range(n_plates):
            dlon = (block_lon - seed_lon[pid] + 180.0) % 360.0 - 180.0
            dlat = block_lat - seed_lat[pid]
            # crude metric scaled by cos lat
            d = (dlon * np.cos(np.deg2rad(block_lat))) ** 2 + (dlat * 1.6) ** 2
            nearer = d < best_d
            best_d = np.where(nearer, d, best_d)
            best_id = np.where(nearer, pid, best_id)
        plate[y0:y1] = best_id

    return plate, vel_lon.astype(np.float64), vel_lat.astype(np.float64)


def _advect(
    field: np.ndarray,
    plate: np.ndarray,
    vel_lon: np.ndarray,
    vel_lat: np.ndarray,
    lat: np.ndarray,
) -> np.ndarray:
    """Semi-Lagrangian advect scalar field with plate velocities (nearest)."""
    h, w = field.shape
    # sample from past: dest = source + vel → source = dest - vel
    yy, xx = np.indices((h, w))
    # map y to lat step
    # each pixel ~ 360/w lon, 180/h lat
    dpx = vel_lon[plate] * (w / 360.0)
    dpy = -vel_lat[plate] * (h / 180.0)  # lat decreases downward in grid? lat[0]=90, so +lat → -row
    src_x = np.mod(xx - dpx, w)
    src_y = np.clip(yy - dpy, 0, h - 1)
    sx = np.rint(src_x).astype(np.int32) % w
    sy = np.rint(src_y).astype(np.int32)
    return field[sy, sx]


def _boundary_masks(plate: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Rough plate boundary and convergence proxy."""
    # Neighbor differences
    right = np.roll(plate, -1, axis=1)
    down = np.roll(plate, -1, axis=0)
    down[-1] = plate[-1]
    boundary = (plate != right) | (plate != down)
    return boundary.astype(np.float64), boundary.astype(np.float64)


def simulate(cfg: SimConfig) -> SimResult:
    rng = np.random.default_rng(cfg.seed)
    h, w = cfg.height, cfg.width
    lon, lat = lonlat_grids(h, w)
    weights = area_weights(lat)

    cont = _seed_cratons(h, w, lat, lon, rng, cfg.n_continental_seeds)
    # Initial land-ish fraction of seeds — will evolve
    plate, vel_lon, vel_lat = _assign_plates(
        cont, lat, lon, rng, cfg.n_continental_seeds, cfg.n_oceanic_plates
    )
    orogeny = np.zeros((h, w), dtype=np.float64)
    ocean_age = (1.0 - cont) * rng.random((h, w))  # 0 young .. 1 old

    for t in range(cfg.ticks):
        # Occasionally reshuffle weak velocities (ridge push / slab pull noise)
        if t % 12 == 11:
            vel_lon += rng.normal(0, 0.35, size=vel_lon.shape)
            vel_lat += rng.normal(0, 0.2, size=vel_lat.shape)
            vel_lon *= 0.92
            vel_lat *= 0.92

        cont = _advect(cont, plate, vel_lon, vel_lat, lat)
        orogeny = _advect(orogeny, plate, vel_lon, vel_lat, lat)
        ocean_age = _advect(ocean_age, plate, vel_lon, vel_lat, lat)
        # plate ids also advect (keeps terranes coherent-ish)
        plate_f = _advect(plate.astype(np.float64), plate, vel_lon, vel_lat, lat)
        plate = np.rint(plate_f).astype(np.int32)
        plate = np.clip(plate, 0, len(vel_lon) - 1)

        boundary, _ = _boundary_masks(plate)

        # Relative velocity magnitude across E/W and N/S edges
        vlon = vel_lon[plate]
        vlat = vel_lat[plate]
        dv = np.abs(vlon - np.roll(vlon, -1, axis=1)) + np.abs(vlat - np.roll(vlat, -1, axis=0))
        dv[-1] = 0
        converging = boundary * smoothstep(0.4, 2.0, dv)
        diverging = boundary * (1.0 - smoothstep(0.2, 1.2, dv))

        # Continent-continent collision: both sides continental
        cont_r = np.roll(cont, -1, axis=1)
        cont_d = np.roll(cont, -1, axis=0)
        both_cont = (cont > 0.45) & ((cont_r > 0.45) | (cont_d > 0.45))
        suture = converging * both_cont.astype(np.float64)
        orogeny += suture * (0.08 + 0.04 * rng.random())

        # Ocean-continent subduction: raise arc on continental side
        oc_sub = converging * ((cont > 0.4) | (cont_r > 0.4)).astype(np.float64) * (
            1.0 - both_cont.astype(np.float64)
        )
        orogeny += oc_sub * 0.045
        # Consume oceanic crust near trench
        ocean_age = np.where(oc_sub > 0.3, np.minimum(ocean_age, 0.15), ocean_age)
        cont = np.where(oc_sub > 0.5, np.maximum(cont, 0.15), cont)  # accretion scrap

        # Rifts: diverge under continent → thin / oceanize
        rift = diverging * (cont > 0.5).astype(np.float64)
        cont = np.clip(cont - rift * 0.07, 0, 1)
        ocean_age = np.where(rift > 0.4, 0.0, ocean_age)  # new ocean
        orogeny *= 1.0 - 0.03 * rift

        # Mid-ocean ridges in open ocean divergence
        ridge = diverging * (cont < 0.25).astype(np.float64)
        ocean_age = np.where(ridge > 0.35, 0.0, np.clip(ocean_age + 0.012, 0, 1))

        # Diffuse noise / erosion
        orogeny *= 0.985
        orogeny = np.clip(orogeny + (rng.random((h, w)) - 0.5) * 0.002 * (cont > 0.3), 0, 2)
        cont = np.clip(cont + (rng.random((h, w)) - 0.5) * 0.01 * boundary, 0, 1)

    # Elevation model
    # Continental platform + orogeny; ocean depth from age (young crust = ridge bump)
    elev = np.where(
        cont > 0.35,
        0.15 + 0.55 * cont + 0.9 * np.clip(orogeny, 0, 1.5) + (rng.random((h, w)) - 0.5) * 0.04,
        -0.15
        - 0.7 * ocean_age
        + 0.15 * ridge_bump(ocean_age)
        + (rng.random((h, w)) - 0.5) * 0.03,
    )
    # Shelves
    elev += smoothstep(0.2, 0.45, cont) * (1 - smoothstep(0.55, 0.9, cont)) * 0.08

    if cfg.era == "lgm":
        elev = np.where(elev > -0.55, elev + 0.18, elev + 0.08)
        # northern ice bump
        elev += (cont > 0.35) * smoothstep(45, 58, lat) * 0.25

    sea, land_frac = fit_sea_level(elev, weights, cfg.target_land, cfg.era)

    moisture = climate_moisture(lon, lat, elev, sea, cont, orogeny)
    color = colorize(elev, sea, lat, moisture, cfg.era)
    height_u8 = to_height_png(elev)

    resources = build_resources(
        elev=elev,
        sea=sea,
        cont=cont,
        orogeny=orogeny,
        ocean_age=ocean_age,
        lat=lat,
        lon=lon,
        moisture=moisture,
        base_color=color,
        seed=cfg.seed,
    )
    geojson = deposits_geojson(resources.deposits)

    hooks = evaluate_hooks(elev, sea, cont, orogeny, plate, weights, lon, lat)

    meta = {
        "method": "deeptime-plates-v1",
        "seed": cfg.seed,
        "width": w,
        "height": h,
        "ticks": cfg.ticks,
        "ma_per_tick": cfg.ma_per_tick,
        "era": cfg.era,
        "sea_level": float(sea),
        "land_fraction": float(land_frac),
        "target_land": cfg.target_land,
        "n_plates": int(plate.max() + 1),
        "hooks": hooks,
        "resources": {
            "catalog": list(RESOURCE_CATALOG.keys()),
            "deposit_count": len(resources.deposits),
            "legend": resources.legend,
            "rule": "world/13-resources-from-geology.md",
        },
        "canon": [
            "docs/superpowers/specs/2026-07-24-world-generation-design.md",
            "world/05-planetary-formation.md",
            "world/12-worldbuilding-principles.md",
            "world/13-resources-from-geology.md",
        ],
    }
    return SimResult(
        elev=elev,
        sea=sea,
        continental=cont,
        plate_id=plate,
        orogeny=orogeny,
        land_fraction=land_frac,
        color=color,
        height_u8=height_u8,
        meta=meta,
        resources_overlay=resources.overlay_rgb,
        resources_geojson=geojson,
    )


def ridge_bump(ocean_age: np.ndarray) -> np.ndarray:
    return np.exp(-((ocean_age / 0.15) ** 2)) * 0.35


def fit_sea_level(
    elev: np.ndarray, weights: np.ndarray, target: float, era: str
) -> tuple[float, float]:
    """Binary search sea level for target area-weighted land fraction."""
    lo, hi = float(elev.min()), float(elev.max())
    best_sea, best_frac = 0.0, 0.0
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        land = elev >= mid
        frac = float((land * weights).sum() / weights.sum())
        best_sea, best_frac = mid, frac
        if frac > target:
            lo = mid
        else:
            hi = mid
    # LGM: lower sea a bit more (expose shelves) — nudge below fitted present-like
    if era == "lgm":
        best_sea -= 0.12
        land = elev >= best_sea
        best_frac = float((land * weights).sum() / weights.sum())
    return best_sea, best_frac


def climate_moisture(
    lon: np.ndarray,
    lat: np.ndarray,
    elev: np.ndarray,
    sea: float,
    cont: np.ndarray,
    orogeny: np.ndarray,
) -> np.ndarray:
    abs_lat = np.abs(lat)
    land = elev >= sea
    hadley = smoothstep(12, 18, abs_lat) * smoothstep(35, 28, abs_lat)
    # crude rain shadow east of high orogeny (assume westerlies mid-lat)
    high = smoothstep(0.2, 0.6, orogeny) * land
    shadow = np.roll(high, 4, axis=1) * smoothstep(25, 50, abs_lat)
    wet_coast = land.astype(np.float64) * 0.2
    m = 0.55 - 0.4 * hadley + wet_coast - 0.35 * shadow + 0.15 * (1.0 - cont) * 0
    m = np.clip(m, 0, 1)
    m = np.where(land, m, 0.8)
    return m


def evaluate_hooks(
    elev: np.ndarray,
    sea: float,
    cont: np.ndarray,
    orogeny: np.ndarray,
    plate: np.ndarray,
    weights: np.ndarray,
    lon: np.ndarray,
    lat: np.ndarray,
) -> dict:
    land = elev >= sea
    land_frac = float((land * weights).sum() / weights.sum())
    # Wide ocean: large connected ocean component spanning many longitudes
    ocean = ~land
    # Subduction-ish: high orogeny on continental margin
    margin = (cont > 0.35) & (np.roll(cont, 1, axis=1) < 0.3)
    has_cordillera = bool((orogeny * margin * land).max() > 0.35)
    # Suture: interior high orogeny with cont both sides
    interior_oro = orogeny > 0.45
    has_suture = bool((interior_oro & land & (cont > 0.4)).sum() > land.size * 0.002)
    # Passive-ish low orogeny continental coast
    quiet_margin = (cont > 0.4) & (np.roll(cont, -1, axis=1) < 0.25) & (orogeny < 0.2)
    has_passive = bool((quiet_margin & land).sum() > 50)
    ocean_frac = 1.0 - land_frac
    wide_ocean = ocean_frac > 0.55

    ok_land = abs(land_frac - TARGET_LAND) <= LAND_TOL or (
        land_frac > 0.35 and land_frac < 0.7
    )  # LGM may be high
    return {
        "land_fraction_ok": bool(abs(land_frac - TARGET_LAND) <= LAND_TOL),
        "wide_ocean": bool(wide_ocean),
        "has_cordillera": has_cordillera,
        "has_suture": has_suture,
        "has_passive_margin": has_passive,
        "all_critical": bool(wide_ocean and has_cordillera and (has_suture or has_passive)),
        "land_fraction": land_frac,
        "note": "v1 hooks are heuristic; reroll seed if all_critical is false for a campaign",
    }


def to_height_png(elev: np.ndarray) -> np.ndarray:
    lo, hi = float(np.percentile(elev, 1)), float(np.percentile(elev, 99))
    t = np.clip((elev - lo) / max(hi - lo, 1e-6), 0, 1)
    return (t * 255).astype(np.uint8)


def colorize(
    elev: np.ndarray, sea: float, lat: np.ndarray, moisture: np.ndarray, era: str
) -> np.ndarray:
    rgb = np.zeros(elev.shape + (3,), dtype=np.float64)
    ocean = elev < sea
    depth = np.clip((sea - elev) / 1.2, 0, 1)
    deep = np.array([0.04, 0.10, 0.26])
    shelf = np.array([0.18, 0.42, 0.55])
    rgb[ocean] = shelf + (deep - shelf) * depth[ocean, None]

    land = ~ocean
    desert = np.array([0.76, 0.66, 0.45])
    grass = np.array([0.48, 0.60, 0.34])
    forest = np.array([0.20, 0.46, 0.27])
    w_desert = np.clip(1.0 - moisture * 1.4, 0, 1)
    w_forest = np.clip((moisture - 0.4) * 1.6, 0, 1)
    w_grass = np.clip(1.0 - w_desert - w_forest, 0, 1)
    col = (
        w_desert[:, :, None] * desert
        + w_grass[:, :, None] * grass
        + w_forest[:, :, None] * forest
    )
    shade = np.clip(0.7 + 0.5 * (elev - sea), 0.4, 1.3)
    col *= shade[:, :, None]
    abs_lat = np.abs(lat)
    cold = smoothstep(50, 70, abs_lat)
    ice = np.array([0.88, 0.91, 0.94])
    col = col * (1 - 0.6 * cold)[:, :, None] + ice * (0.6 * cold)[:, :, None]
    rgb[land] = col[land]
    if era == "lgm":
        ice_m = land & (lat > 50)
        rgb[ice_m] = (0.93, 0.95, 0.98)
    rgb[abs_lat > 72] = (0.93, 0.95, 0.98)
    return np.clip(rgb, 0, 1)


def save_result(result: SimResult, prefix: str = "world") -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    VIEWER_WORLD.mkdir(parents=True, exist_ok=True)
    era = result.meta.get("era", "present")
    suffix = "" if era == "present" else f"-{era}"
    height_img = Image.fromarray(result.height_u8, mode="L")
    color_img = Image.fromarray((result.color * 255).astype(np.uint8), mode="RGB")
    plate_norm = (result.plate_id.astype(np.float64) / max(result.plate_id.max(), 1) * 255).astype(
        np.uint8
    )
    plate_img = Image.fromarray(plate_norm, mode="L")

    resources_img = None
    if result.resources_overlay is not None:
        resources_img = Image.fromarray(
            (result.resources_overlay * 255).astype(np.uint8), mode="RGB"
        )

    for dest in (EXPORTS, VIEWER_WORLD):
        height_img.save(dest / f"{prefix}-height{suffix}.png")
        color_img.save(dest / f"{prefix}-color{suffix}.png")
        plate_img.save(dest / f"{prefix}-plates{suffix}.png")
        if resources_img is not None:
            resources_img.save(dest / f"{prefix}-resources{suffix}.png")
        if result.resources_geojson is not None:
            (dest / f"{prefix}-resources{suffix}.geojson").write_text(
                json.dumps(result.resources_geojson, indent=2) + "\n"
            )
        (dest / f"{prefix}-meta{suffix}.json").write_text(
            json.dumps(result.meta, indent=2) + "\n"
        )
    n_dep = result.meta.get("resources", {}).get("deposit_count", 0)
    print(
        f"deeptime seed={result.meta['seed']} land={result.land_fraction:.3f} "
        f"hooks={result.meta['hooks'].get('all_critical')} deposits={n_dep} "
        f"→ {EXPORTS / f'{prefix}-color{suffix}.png'}"
    )


def run_until_hooks(
    base: SimConfig, max_tries: int = 12
) -> SimResult:
    """Try seeds until critical hooks pass (or return best effort)."""
    best: SimResult | None = None
    best_score = -1
    seed = base.seed
    for attempt in range(max_tries):
        cfg = SimConfig(**{**base.__dict__, "seed": seed})
        result = simulate(cfg)
        hooks = result.meta["hooks"]
        score = sum(
            [
                hooks["wide_ocean"],
                hooks["has_cordillera"],
                hooks["has_suture"],
                hooks["has_passive_margin"],
                hooks["land_fraction_ok"],
            ]
        )
        if score > best_score:
            best_score = score
            best = result
        if hooks["all_critical"] and hooks["land_fraction_ok"]:
            result.meta["hook_attempts"] = attempt + 1
            return result
        seed = int(seed + 1 + attempt * 17)
    assert best is not None
    best.meta["hook_attempts"] = max_tries
    best.meta["hooks"]["note"] = "best-effort after max_tries; consider another base seed"
    return best
