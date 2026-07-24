"""
Algorithmic world map generator for Generational Jump / Veldara.

Canon rules: world/05-planetary-formation.md
NOT image-gen — deterministic heightfield + climate color from tectonics parameters.

Usage:
  python3 generate_world.py
  python3 generate_world.py --width 4096 --seed 42

Outputs (also copied into maps/viewer/public/world/ for Pages):
  ../exports/world-height.png   — greyscale elevation
  ../exports/world-color.png    — atlas-style color
  ../exports/world-meta.json    — parameters used
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
EXPORTS = ROOT.parent / "exports"
VIEWER_WORLD = ROOT.parent / "viewer" / "public" / "world"


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def value_noise(h: int, w: int, grid_y: int, grid_x: int, rng: np.random.Generator) -> np.ndarray:
    """Cheap value noise upsampled to h×w with wrap in X (longitude)."""
    gy, gx = max(2, grid_y), max(2, grid_x)
    grid = rng.random((gy + 1, gx + 1), dtype=np.float64)
    grid[:, -1] = grid[:, 0]
    grid[-1, :] = grid[0, :]
    ys = np.linspace(0, gy - 1e-6, h)
    xs = np.linspace(0, gx - 1e-6, w)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    y1 = y0 + 1
    x1 = x0 + 1
    yy = y0[:, None]
    xx = x0[None, :]
    yy1 = y1[:, None]
    xx1 = x1[None, :]
    n00 = grid[yy, xx]
    n10 = grid[yy1, xx]
    n01 = grid[yy, xx1]
    n11 = grid[yy1, xx1]
    wa = n00 * (1 - fx) + n01 * fx
    wb = n10 * (1 - fx) + n11 * fx
    return wa * (1 - fy) + wb * fy


def fbm(h: int, w: int, rng: np.random.Generator, octaves: int = 5, base: int = 4) -> np.ndarray:
    total = np.zeros((h, w), dtype=np.float64)
    amp = 1.0
    norm = 0.0
    freq = base
    for _ in range(octaves):
        total += amp * value_noise(h, w, freq, freq * 2, rng)
        norm += amp
        amp *= 0.5
        freq = int(freq * 2)
    return total / norm


def lonlat_grids(h: int, w: int) -> tuple[np.ndarray, np.ndarray]:
    # lon [-180, 180), lat [90, -90]
    lon = np.linspace(-180.0, 180.0, w, endpoint=False)
    lat = np.linspace(90.0, -90.0, h)
    return np.meshgrid(lon, lat)


def ellipse_mask(lon: np.ndarray, lat: np.ndarray, clon: float, clat: float, rlon: float, rlat: float) -> np.ndarray:
    dlon = (lon - clon + 180.0) % 360.0 - 180.0
    u = (dlon / rlon) ** 2 + ((lat - clat) / rlat) ** 2
    return smoothstep(1.15, 0.55, np.sqrt(u))


def ridge(lon: np.ndarray, lat: np.ndarray, lon0: float, lat0: float, lat1: float, width: float) -> np.ndarray:
    """N-S mountain ridge along lon0 between lat0..lat1."""
    dlon = np.abs((lon - lon0 + 180.0) % 360.0 - 180.0)
    along = smoothstep(lat0 - 3, lat0, lat) * smoothstep(lat1 + 3, lat1, lat)
    # lat decreases north→south in our grid but values are still geographic
    along = np.where((lat <= lat0) & (lat >= lat1), 1.0, along)
    profile = np.exp(-((dlon / width) ** 2))
    return profile * along


def generate(width: int, height: int, seed: int, era: str = "present") -> dict:
    if era not in ("present", "lgm"):
        raise ValueError("era must be 'present' or 'lgm'")

    rng = np.random.default_rng(seed)
    lon, lat = lonlat_grids(height, width)
    noise = fbm(height, width, rng, octaves=6, base=5)
    noise2 = fbm(height, width, rng, octaves=4, base=8)

    elev = np.full((height, width), -0.55, dtype=np.float64)  # deep ocean baseline

    # --- Continents (masks 0..1) ---
    aurelian_core = ellipse_mask(lon, lat, clon=-35, clat=32, rlon=52, rlat=38)
    gulf = ellipse_mask(lon, lat, clon=-5, clat=22, rlon=18, rlat=12)

    if era == "present":
        # East Gulf embayment carved (passive-margin flooding)
        aurelian = np.clip(aurelian_core - 0.85 * gulf, 0, 1)
    else:
        # LGM: gulf is low exposed shelf/plain, still part of the land mask
        aurelian = np.clip(aurelian_core + 0.55 * gulf, 0, 1)

    kharzhan = ellipse_mask(lon, lat, clon=105, clat=35, rlon=55, rlat=42)
    farreach = ellipse_mask(lon, lat, clon=40, clat=-35, rlon=58, rlat=30)
    solmar = ellipse_mask(lon, lat, clon=-145, clat=10, rlon=22, rlat=16)

    arc_lat = -8 + 6 * np.sin(np.deg2rad((lon + 145) * 3.2))
    arc = np.exp(-(((lat - arc_lat) / 2.8) ** 2)) * np.exp(-((((lon + 145) / 28) ** 2)))
    arc = np.clip(arc, 0, 1)

    elev += aurelian * (0.95 + 0.12 * noise)
    elev += kharzhan * (1.00 + 0.10 * noise2)
    elev += farreach * (0.90 + 0.14 * noise)
    elev += solmar * (0.85 + 0.12 * noise2)
    elev += arc * 0.55

    if era == "lgm":
        # Exposed shelves (Earth ~−120 m): lift nearshore bathymetry
        elev = np.where(elev > -0.45, elev + 0.22, elev + 0.12)
        # Gulf plain stays low but above LGM sea
        elev += gulf * 0.18

    shelf = smoothstep(0.05, 0.35, aurelian + kharzhan) * (
        1.0 - smoothstep(0.4, 0.9, aurelian + kharzhan)
    )
    elev += shelf * (0.12 if era == "lgm" else 0.08)

    highspine = ridge(lon, lat, lon0=-68, lat0=58, lat1=5, width=4.5)
    elev += highspine * aurelian * (0.55 + 0.2 * noise)

    trench = ridge(lon, lat, lon0=-78, lat0=55, lat1=8, width=3.0) * (1.0 - aurelian)
    elev -= trench * 0.35

    north_high = ellipse_mask(lon, lat, clon=-30, clat=58, rlon=28, rlat=10) * aurelian
    elev += north_high * 0.22

    suture = ridge(lon, lat, lon0=38, lat0=-12, lat1=-55, width=5.5) * farreach
    elev += suture * (0.65 + 0.15 * noise2)

    kh_east = ridge(lon, lat, lon0=145, lat0=55, lat1=5, width=7.0) * kharzhan
    elev += kh_east * 0.35

    sol_west = ridge(lon, lat, lon0=-158, lat0=22, lat1=-2, width=4.0) * solmar
    elev += sol_west * 0.45

    landish = smoothstep(-0.05, 0.15, elev)
    elev += (noise - 0.5) * 0.12 * landish
    elev += smoothstep(60, 75, np.abs(lat)) * 0.05

    # Sea level: present = 0; LGM ≈ −120 m → lower threshold in elev units
    sea = -0.28 if era == "lgm" else 0.0

    # Ice sheets (LGM): northern Aurelian + Kharzhan
    ice = np.zeros_like(elev)
    if era == "lgm":
        northern_land = (aurelian + kharzhan) > 0.2
        ice = northern_land * smoothstep(45, 55, lat)
        ice = np.clip(ice + smoothstep(60, 70, np.abs(lat)), 0, 1)
        elev += ice * 0.35

    dlon_hs = (lon + 68 + 180) % 360 - 180
    rain_shadow = aurelian * smoothstep(2, 8, dlon_hs) * smoothstep(25, 12, dlon_hs)
    west_wet = aurelian * np.exp(-(((lon + 72) / 6) ** 2)) * smoothstep(-0.05, 0.2, elev)
    abs_lat = np.abs(lat)
    hadley_dry = smoothstep(12, 18, abs_lat) * smoothstep(35, 28, abs_lat)

    moisture = (
        0.55
        + 0.35 * west_wet
        - 0.45 * rain_shadow
        - 0.35 * hadley_dry * (1.0 - 0.5 * gulf)
        + 0.25 * gulf * aurelian * (0.3 if era == "lgm" else 1.0)
        + 0.2 * farreach * (1.0 - suture) * smoothstep(0.2, 0.0, np.abs((lon - 38) / 20))
    )
    if era == "lgm":
        moisture -= 0.2 * smoothstep(30, 50, abs_lat)  # colder/drier mid-high lats
        moisture -= 0.35 * ice
    moisture = np.clip(moisture + (noise2 - 0.5) * 0.08, 0, 1)

    color = colorize(elev, sea, lat, moisture, ice if era == "lgm" else None)

    height_u8 = to_height_png(elev, sea)
    return {
        "elev": elev,
        "sea": sea,
        "color": color,
        "height_u8": height_u8,
        "era": era,
        "meta": {
            "seed": seed,
            "width": width,
            "height": height,
            "era": era,
            "sea_level": sea,
            "method": "algorithmic-tectonics-v1",
            "canon": [
                "world/05-planetary-formation.md",
                "world/08-last-20ka.md",
            ],
            "features": [
                "aurelian+east-gulf",
                "highspine-subduction",
                "west-trench",
                "kharzhan-craton",
                "farreach-suture",
                "solmar-island-continent+arc",
                "climate-rainshadow-hadley",
                f"era:{era}",
            ],
        },
    }


def to_height_png(elev: np.ndarray, sea: float) -> np.ndarray:
    # Map elev to 0..255 with sea at ~90
    lo, hi = -1.2, 1.6
    t = np.clip((elev - lo) / (hi - lo), 0, 1)
    return (t * 255).astype(np.uint8)


def colorize(
    elev: np.ndarray,
    sea: float,
    lat: np.ndarray,
    moisture: np.ndarray,
    ice_mask: np.ndarray | None = None,
) -> np.ndarray:
    rgb = np.zeros(elev.shape + (3,), dtype=np.float64)

    ocean = elev < sea
    depth = np.clip((sea - elev) / 1.0, 0, 1)
    deep_col = np.array([0.04, 0.10, 0.26])
    shelf_col = np.array([0.18, 0.42, 0.55])
    rgb[ocean] = shelf_col + (deep_col - shelf_col) * depth[ocean, None]

    land = ~ocean
    abs_lat = np.abs(lat)
    desert_c = np.array([0.76, 0.66, 0.45])
    grass_c = np.array([0.48, 0.60, 0.34])
    forest_c = np.array([0.20, 0.46, 0.27])
    steppe_c = np.array([0.62, 0.58, 0.40])

    w_desert = np.clip(1.0 - moisture * 1.4, 0, 1)
    w_forest = np.clip((moisture - 0.4) * 1.6, 0, 1)
    w_grass = np.clip(1.0 - w_desert - w_forest, 0, 1)
    land_col = (
        w_desert[:, :, None] * desert_c.reshape(1, 1, 3)
        + w_grass[:, :, None] * grass_c.reshape(1, 1, 3)
        + w_forest[:, :, None] * forest_c.reshape(1, 1, 3)
    )
    # Mid-moisture cold → steppe wash
    steppe_w = np.clip((0.55 - moisture) * smoothstep(35, 50, abs_lat), 0, 1)
    land_col = land_col * (1 - 0.5 * steppe_w)[:, :, None] + steppe_c.reshape(1, 1, 3) * (
        0.5 * steppe_w
    )[:, :, None]

    shade = np.clip(0.75 + 0.45 * (elev - sea), 0.45, 1.25)
    land_col *= shade[:, :, None]
    cold = smoothstep(48, 68, abs_lat)
    ice_c = np.array([0.85, 0.88, 0.90]).reshape(1, 1, 3)
    land_col = land_col * (1.0 - 0.55 * cold)[:, :, None] + ice_c * (0.55 * cold)[:, :, None]
    rgb[land] = land_col[land]

    peak = land & (elev > 0.8)
    rgb[peak] = np.clip(rgb[peak] * 0.5 + np.array([0.93, 0.93, 0.95]) * 0.5, 0, 1)

    ice = (abs_lat > 72) | ((abs_lat > 62) & (elev > sea + 0.15))
    if ice_mask is not None:
        ice = ice | ((ice_mask > 0.35) & land)
    rgb[ice] = (0.93, 0.95, 0.98)
    return np.clip(rgb, 0, 1)


def save_outputs(result: dict) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    VIEWER_WORLD.mkdir(parents=True, exist_ok=True)

    era = result.get("era", "present")
    suffix = "" if era == "present" else f"-{era}"

    height_img = Image.fromarray(result["height_u8"], mode="L")
    color_u8 = (result["color"] * 255).astype(np.uint8)
    color_img = Image.fromarray(color_u8, mode="RGB")

    for dest_dir in (EXPORTS, VIEWER_WORLD):
        height_img.save(dest_dir / f"world-height{suffix}.png")
        color_img.save(dest_dir / f"world-color{suffix}.png")
        (dest_dir / f"world-meta{suffix}.json").write_text(
            json.dumps(result["meta"], indent=2) + "\n"
        )

    print(f"Wrote {EXPORTS / f'world-color{suffix}.png'} (era={era})")
    if era == "present":
        print(f"Copied into {VIEWER_WORLD} for Pages viewer")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--width", type=int, default=2048)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--era",
        choices=("present", "lgm"),
        default="present",
        help="Climate/map snapshot: present (default) or LGM (~20ka Earth-analogue)",
    )
    args = p.parse_args()
    if args.width % 2:
        raise SystemExit("width should be even for equirectangular")
    result = generate(args.width, args.height, args.seed, era=args.era)
    save_outputs(result)


if __name__ == "__main__":
    main()
