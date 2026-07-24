"""Warp equirectangular atlas PNGs into Web Mercator XYZ tiles.

MapLibre globe extends *raster tiles* to the poles (edge stretch). Image
sources pass allowPoles=false, so the basemap must be tiles to match
MapLibre's normal Earth/satellite behavior.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

# Same limit MapLibre / EPSG:3857 use.
MERCATOR_MAX_LAT = 85.0511287798066


def _sample_equirect(
    image: np.ndarray, lon: np.ndarray, lat: np.ndarray
) -> np.ndarray:
    height, width = image.shape[:2]
    x = (lon + 180.0) / 360.0 * width
    y = (90.0 - lat) / 180.0 * height
    x0 = np.floor(x).astype(np.int64) % width
    y0 = np.clip(np.floor(y).astype(np.int64), 0, height - 1)
    return image[y0, x0]


def write_mercator_tiles(
    equirect_rgb: np.ndarray,
    destination: Path,
    *,
    max_zoom: int = 3,
    tile_size: int = 256,
) -> dict:
    """Write XYZ PNG tiles covering the Web Mercator world.

    ``equirect_rgb`` is HxWx3 float 0..1 or uint8.
    """
    if equirect_rgb.dtype != np.uint8:
        pixels = (np.clip(equirect_rgb, 0, 1) * 255).astype(np.uint8)
    else:
        pixels = equirect_rgb

    destination.mkdir(parents=True, exist_ok=True)
    written = 0
    for zoom in range(0, max_zoom + 1):
        n = 1 << zoom
        for tile_x in range(n):
            for tile_y in range(n):
                u = (np.arange(tile_size) + 0.5) / tile_size
                v = (np.arange(tile_size) + 0.5) / tile_size
                uu, vv = np.meshgrid(u, v)
                lon = (tile_x + uu) / n * 360.0 - 180.0
                lat = np.degrees(
                    np.arctan(np.sinh(math.pi * (1.0 - 2.0 * (tile_y + vv) / n)))
                )
                lat = np.clip(lat, -MERCATOR_MAX_LAT, MERCATOR_MAX_LAT)
                tile = _sample_equirect(pixels, lon, lat)
                path = destination / str(zoom) / str(tile_x) / f"{tile_y}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(tile, mode="RGB").save(path)
                written += 1

    return {
        "tile_count": written,
        "max_zoom": max_zoom,
        "tile_size": tile_size,
        "mercator_max_lat": MERCATOR_MAX_LAT,
    }
