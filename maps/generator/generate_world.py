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


def generate(width: int, height: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    lon, lat = lonlat_grids(height, width)
    noise = fbm(height, width, rng, octaves=6, base=5)
    noise2 = fbm(height, width, rng, octaves=4, base=8)

    elev = np.full((height, width), -0.55, dtype=np.float64)  # deep ocean baseline

    # --- Continents (masks 0..1) ---
    # Aurelian: central-west northern continent
    aurelian = ellipse_mask(lon, lat, clon=-35, clat=32, rlon=52, rlat=38)
    # East Gulf embayment on SE Aurelian (carve passive-margin gulf)
    gulf = ellipse_mask(lon, lat, clon=-5, clat=22, rlon=18, rlat=12)
    aurelian = np.clip(aurelian - 0.85 * gulf, 0, 1)

    # Kharzhan: far east craton
    kharzhan = ellipse_mask(lon, lat, clon=105, clat=35, rlon=55, rlat=42)

    # Farreach: southern continent
    farreach = ellipse_mask(lon, lat, clon=40, clat=-35, rlon=58, rlat=30)

    # Solmar island-continent (Australia-scale) in West Ocean
    solmar = ellipse_mask(lon, lat, clon=-145, clat=10, rlon=22, rlat=16)

    # Solmar volcanic arc (curved chain south of Solmar)
    arc_lat = -8 + 6 * np.sin(np.deg2rad((lon + 145) * 3.2))
    arc = np.exp(-(((lat - arc_lat) / 2.8) ** 2)) * np.exp(-((((lon + 145) / 28) ** 2)))
    arc = np.clip(arc, 0, 1)

    # Raise continents
    elev += aurelian * (0.95 + 0.12 * noise)
    elev += kharzhan * (1.00 + 0.10 * noise2)
    elev += farreach * (0.90 + 0.14 * noise)
    elev += solmar * (0.85 + 0.12 * noise2)
    elev += arc * 0.55

    # Passive shelves on East Ocean facing coasts (Aurelian east, Kharzhan west) — gentle
    # already from ellipse falloff; add a bit of shelf uplift near sea level
    shelf = smoothstep(0.05, 0.35, aurelian + kharzhan) * (1.0 - smoothstep(0.4, 0.9, aurelian + kharzhan))
    elev += shelf * 0.08

    # --- Orogeny ---
    # Highspine: N-S cordillera on western Aurelian (~subduction)
    highspine = ridge(lon, lat, lon0=-68, lat0=58, lat1=5, width=4.5)
    elev += highspine * aurelian * (0.55 + 0.2 * noise)

    # Offshore trench west of Highspine (bathymetric low)
    trench = ridge(lon, lat, lon0=-78, lat0=55, lat1=8, width=3.0) * (1.0 - aurelian)
    elev -= trench * 0.35

    # Sereth / Northwood old highland (north Aurelian)
    north_high = ellipse_mask(lon, lat, clon=-30, clat=58, rlon=28, rlat=10) * aurelian
    elev += north_high * 0.22

    # Farreach collisional suture (central orogeny)
    suture = ridge(lon, lat, lon0=38, lat0=-12, lat1=-55, width=5.5) * farreach
    elev += suture * (0.65 + 0.15 * noise2)

    # Outer accretionary mountains on far-east Kharzhan (not on passive west)
    kh_east = ridge(lon, lat, lon0=145, lat0=55, lat1=5, width=7.0) * kharzhan
    elev += kh_east * 0.35

    # Solmar west arc mountains
    sol_west = ridge(lon, lat, lon0=-158, lat0=22, lat1=-2, width=4.0) * solmar
    elev += sol_west * 0.45

    # Detail noise on land
    landish = smoothstep(-0.05, 0.15, elev)
    elev += (noise - 0.5) * 0.12 * landish

    # Polar ice slight uplift (visual only)
    elev += smoothstep(60, 75, np.abs(lat)) * 0.05

    # Sea level at 0
    sea = 0.0

    # --- Climate / color ---
    # Moisture: wet west of Highspine, rain shadow east, humid gulf, hadley dry bands
    west_wet = aurelian * np.exp(-(((lon + 72) / 6) ** 2)) * smoothstep(-0.05, 0.2, elev)
    rain_shadow = aurelian * highspine * 0.0 + aurelian * np.exp(-(((lon + 58) / 10) ** 2)) * (1.0 - west_wet)
    # simpler rain shadow band just east of ridge
    dlon_hs = (lon + 68 + 180) % 360 - 180
    rain_shadow = aurelian * smoothstep(2, 8, dlon_hs) * smoothstep(25, 12, dlon_hs)

    abs_lat = np.abs(lat)
    hadley_dry = smoothstep(12, 18, abs_lat) * smoothstep(35, 28, abs_lat)

    moisture = (
        0.55
        + 0.35 * west_wet
        - 0.45 * rain_shadow
        - 0.35 * hadley_dry * (1.0 - 0.5 * gulf)  # gulf breaks desert a bit
        + 0.25 * gulf * aurelian
        + 0.2 * farreach * (1.0 - suture) * smoothstep(0.2, 0.0, np.abs((lon - 38) / 20))
    )
    moisture = np.clip(moisture + (noise2 - 0.5) * 0.08, 0, 1)

    color = colorize(elev, sea, lat, moisture, highspine, suture)

    height_u8 = to_height_png(elev, sea)
    return {
        "elev": elev,
        "sea": sea,
        "color": color,
        "height_u8": height_u8,
        "meta": {
            "seed": seed,
            "width": width,
            "height": height,
            "sea_level": sea,
            "method": "algorithmic-tectonics-v1",
            "canon": "world/05-planetary-formation.md",
            "features": [
                "aurelian+east-gulf",
                "highspine-subduction",
                "west-trench",
                "kharzhan-craton",
                "farreach-suture",
                "solmar-island-continent+arc",
                "climate-rainshadow-hadley",
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
    highspine: np.ndarray,
    suture: np.ndarray,
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

    w_desert = np.clip(1.0 - moisture * 1.4, 0, 1)
    w_forest = np.clip((moisture - 0.4) * 1.6, 0, 1)
    w_grass = np.clip(1.0 - w_desert - w_forest, 0, 1)
    land_col = (
        w_desert[:, :, None] * desert_c.reshape(1, 1, 3)
        + w_grass[:, :, None] * grass_c.reshape(1, 1, 3)
        + w_forest[:, :, None] * forest_c.reshape(1, 1, 3)
    )
    shade = np.clip(0.75 + 0.45 * (elev - sea), 0.45, 1.25)
    land_col *= shade[:, :, None]
    cold = smoothstep(48, 68, abs_lat)
    ice_c = np.array([0.85, 0.88, 0.90]).reshape(1, 1, 3)
    land_col = land_col * (1.0 - 0.55 * cold)[:, :, None] + ice_c * (0.55 * cold)[:, :, None]
    rgb[land] = land_col[land]

    peak = land & (elev > 0.8)
    rgb[peak] = np.clip(rgb[peak] * 0.5 + np.array([0.93, 0.93, 0.95]) * 0.5, 0, 1)

    ice = (abs_lat > 72) | ((abs_lat > 62) & (elev > sea + 0.15))
    rgb[ice] = (0.93, 0.95, 0.98)
    return np.clip(rgb, 0, 1)


def save_outputs(result: dict) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    VIEWER_WORLD.mkdir(parents=True, exist_ok=True)

    height_img = Image.fromarray(result["height_u8"], mode="L")
    color_u8 = (result["color"] * 255).astype(np.uint8)
    color_img = Image.fromarray(color_u8, mode="RGB")

    for dest_dir in (EXPORTS, VIEWER_WORLD):
        height_img.save(dest_dir / "world-height.png")
        color_img.save(dest_dir / "world-color.png")
        (dest_dir / "world-meta.json").write_text(json.dumps(result["meta"], indent=2) + "\n")

    print(f"Wrote {EXPORTS / 'world-color.png'}")
    print(f"Wrote {EXPORTS / 'world-height.png'}")
    print(f"Copied into {VIEWER_WORLD} for Pages viewer")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--width", type=int, default=2048)
    p.add_argument("--height", type=int, default=1024)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if args.width % 2:
        raise SystemExit("width should be even for equirectangular")
    result = generate(args.width, args.height, args.seed)
    save_outputs(result)


if __name__ == "__main__":
    main()
