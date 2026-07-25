"""Build nested theater overlays for deep Mercator tiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .climate import ClimateFields
from .grid import CubedSphere
from .refine import WindowSpec, extract_window, refine_window
from .tiles import DEFAULT_DEEP_WINDOWS, DeepWindow


@dataclass(frozen=True)
class TheaterOverlay:
    """Local equirect patch of refined atlas color over a deep window."""

    name: str
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float
    lons: np.ndarray
    lats: np.ndarray
    rgb: np.ndarray  # (ny, nx, 3) float 0..1
    elevation_m: np.ndarray  # (ny, nx)

    @property
    def nx(self) -> int:
        return int(self.lons.size)

    @property
    def ny(self) -> int:
        return int(self.lats.size)


def _colorize_elevation(elevation_m: np.ndarray, sea_level_m: float) -> np.ndarray:
    """Simple hypsometric colors matching the coarse atlas look."""
    elev = np.asarray(elevation_m, dtype=np.float64)
    land = elev >= sea_level_m
    rgb = np.zeros(elev.shape + (3,), dtype=np.float64)
    depth = np.clip((sea_level_m - elev) / 6000.0, 0.0, 1.0)
    rgb[~land] = np.stack(
        [
            0.02 + 0.05 * depth[~land],
            0.08 + 0.18 * depth[~land],
            0.22 + 0.35 * (1.0 - depth[~land]),
        ],
        axis=-1,
    )
    above = np.clip((elev - sea_level_m) / 3500.0, 0.0, 1.0)
    rgb[land] = np.stack(
        [
            0.18 + 0.42 * above[land],
            0.32 + 0.28 * above[land],
            0.16 + 0.18 * above[land],
        ],
        axis=-1,
    )
    snow = land & (elev > sea_level_m + 2800.0)
    rgb[snow] = (0.92, 0.94, 0.96)
    return rgb


def build_theater_overlays(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    climate: ClimateFields,
    *,
    sea_level_m: float,
    windows: Sequence[DeepWindow] | None = None,
    target_km: float = 1.0,
    seed: int = 0,
    iterations: int = 12,
) -> list[TheaterOverlay]:
    """Extract + refine each deep window and colorize the local mesh."""
    wins = tuple(windows) if windows is not None else DEFAULT_DEEP_WINDOWS
    overlays: list[TheaterOverlay] = []
    for index, window in enumerate(wins):
        spec = WindowSpec(
            lon_min=window.lon_min,
            lon_max=window.lon_max,
            lat_min=window.lat_min,
            lat_max=window.lat_max,
            target_km=float(target_km),
            margin=0.08,
        )
        extracted = extract_window(
            grid, elevation_m, climate, spec, seed=seed + 31 * index
        )
        refined = refine_window(
            extracted, iterations=iterations, seed=seed + 31 * index
        )
        elev2d = refined.elevation_m.reshape(refined.ny, refined.nx)
        rgb = _colorize_elevation(elev2d, sea_level_m)
        lon0, lon1, lat0, lat1 = spec.expanded()
        lons = np.linspace(lon0, lon1, refined.nx)
        lats = np.linspace(lat0, lat1, refined.ny)
        overlays.append(
            TheaterOverlay(
                name=window.name,
                lon_min=lon0,
                lon_max=lon1,
                lat_min=lat0,
                lat_max=lat1,
                lons=lons,
                lats=lats,
                rgb=rgb,
                elevation_m=elev2d,
            )
        )
    return overlays


def sample_overlays(
    overlays: Sequence[TheaterOverlay],
    lon: np.ndarray,
    lat: np.ndarray,
    base_rgb: np.ndarray,
) -> np.ndarray:
    """Replace ``base_rgb`` samples that fall inside theater overlays."""
    out = np.asarray(base_rgb, dtype=np.float64).copy()
    flat_lon = np.asarray(lon, dtype=np.float64).ravel()
    flat_lat = np.asarray(lat, dtype=np.float64).ravel()
    flat_out = out.reshape(-1, 3)
    for overlay in overlays:
        inside = (
            (flat_lon >= overlay.lon_min)
            & (flat_lon <= overlay.lon_max)
            & (flat_lat >= overlay.lat_min)
            & (flat_lat <= overlay.lat_max)
        )
        if not np.any(inside):
            continue
        # Bilinear sample in the local patch.
        x = (flat_lon[inside] - overlay.lon_min) / max(
            overlay.lon_max - overlay.lon_min, 1e-9
        ) * (overlay.nx - 1)
        y = (overlay.lat_max - flat_lat[inside]) / max(
            overlay.lat_max - overlay.lat_min, 1e-9
        ) * (overlay.ny - 1)
        x0 = np.floor(x).astype(np.int64)
        y0 = np.floor(y).astype(np.int64)
        x1 = np.clip(x0 + 1, 0, overlay.nx - 1)
        y1 = np.clip(y0 + 1, 0, overlay.ny - 1)
        x0 = np.clip(x0, 0, overlay.nx - 1)
        y0 = np.clip(y0, 0, overlay.ny - 1)
        fx = (x - x0)[:, None]
        fy = (y - y0)[:, None]
        c00 = overlay.rgb[y0, x0]
        c10 = overlay.rgb[y0, x1]
        c01 = overlay.rgb[y1, x0]
        c11 = overlay.rgb[y1, x1]
        flat_out[inside] = (
            (1 - fy) * ((1 - fx) * c00 + fx * c10)
            + fy * ((1 - fx) * c01 + fx * c11)
        )
    return out.reshape(base_rgb.shape)
