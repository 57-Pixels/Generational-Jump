"""Warp equirectangular atlas PNGs into Web Mercator XYZ tiles.

MapLibre globe extends *raster tiles* to the poles (edge stretch). Image
sources pass allowPoles=false, so the basemap must be tiles to match
MapLibre's normal Earth/satellite behavior.

Coverage is sparse by default: global pyramid through ``global_max_zoom``,
then deep zoom only over configured Aurelian / Veldara windows.
"""

from __future__ import annotations

import json
import math
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from PIL import Image

# Same limit MapLibre / EPSG:3857 use.
MERCATOR_MAX_LAT = 85.0511287798066

# Defaults match the nested-morphology sparse pyramid plan.
DEFAULT_GLOBAL_MAX_ZOOM = 6
DEFAULT_DEEP_MAX_ZOOM = 11


@dataclass(frozen=True)
class DeepWindow:
    """Lon/lat AABB (degrees) where deep zoom tiles are written."""

    name: str
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    def clamp_lat(self) -> DeepWindow:
        return DeepWindow(
            name=self.name,
            lon_min=self.lon_min,
            lon_max=self.lon_max,
            lat_min=max(self.lat_min, -MERCATOR_MAX_LAT),
            lat_max=min(self.lat_max, MERCATOR_MAX_LAT),
        )


# Promoted seed 150 Veldara claim (~144°E, 31°N) + Aurelian theatre.
# Sized so z7–z11 coverage stays tens of thousands of tiles, not millions.
DEFAULT_DEEP_WINDOWS: tuple[DeepWindow, ...] = (
    DeepWindow("aurelian", 125.0, 160.0, 5.0, 50.0),
    DeepWindow("veldara", 132.0, 155.0, 18.0, 45.0),
)


def _sample_equirect(
    image: np.ndarray, lon: np.ndarray, lat: np.ndarray
) -> np.ndarray:
    height, width = image.shape[:2]
    x = (lon + 180.0) / 360.0 * width
    y = (90.0 - lat) / 180.0 * height
    x0 = np.floor(x).astype(np.int64) % width
    y0 = np.clip(np.floor(y).astype(np.int64), 0, height - 1)
    return image[y0, x0]


def _lon_to_tile_x(lon_deg: float, zoom: int) -> int:
    n = 1 << zoom
    x = int(math.floor((lon_deg + 180.0) / 360.0 * n))
    return int(np.clip(x, 0, n - 1))


def _lat_to_tile_y(lat_deg: float, zoom: int) -> int:
    lat = float(np.clip(lat_deg, -MERCATOR_MAX_LAT, MERCATOR_MAX_LAT))
    siny = math.sin(math.radians(lat))
    y = 0.5 - math.log((1.0 + siny) / (1.0 - siny)) / (4.0 * math.pi)
    n = 1 << zoom
    return int(np.clip(math.floor(y * n), 0, n - 1))


def tile_lon_lat_bounds(zoom: int, tile_x: int, tile_y: int) -> tuple[float, float, float, float]:
    """Return (lon_min, lon_max, lat_min, lat_max) for a Web Mercator tile."""
    n = float(1 << zoom)
    lon_min = tile_x / n * 360.0 - 180.0
    lon_max = (tile_x + 1) / n * 360.0 - 180.0

    def y_to_lat(ty: float) -> float:
        return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * ty / n))))

    lat_max = y_to_lat(tile_y)
    lat_min = y_to_lat(tile_y + 1)
    return lon_min, lon_max, lat_min, lat_max


def _aabb_intersects(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> bool:
    a_lon0, a_lon1, a_lat0, a_lat1 = a
    b_lon0, b_lon1, b_lat0, b_lat1 = b
    return not (
        a_lon1 < b_lon0 or a_lon0 > b_lon1 or a_lat1 < b_lat0 or a_lat0 > b_lat1
    )


def tiles_covering_window(window: DeepWindow, zoom: int) -> list[tuple[int, int]]:
    """Inclusive (x, y) tile indices that intersect ``window`` at ``zoom``."""
    w = window.clamp_lat()
    if w.lon_max <= w.lon_min or w.lat_max <= w.lat_min:
        return []
    x0 = _lon_to_tile_x(w.lon_min, zoom)
    x1 = _lon_to_tile_x(w.lon_max, zoom)
    # Mercator y increases southward.
    y0 = _lat_to_tile_y(w.lat_max, zoom)
    y1 = _lat_to_tile_y(w.lat_min, zoom)
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    out: list[tuple[int, int]] = []
    win_box = (w.lon_min, w.lon_max, w.lat_min, w.lat_max)
    for tx in range(x0, x1 + 1):
        for ty in range(y0, y1 + 1):
            if _aabb_intersects(tile_lon_lat_bounds(zoom, tx, ty), win_box):
                out.append((tx, ty))
    return out


def dense_tile_count(max_zoom: int) -> int:
    """Tiles in a complete XYZ pyramid from z0 through ``max_zoom``."""
    return sum(1 << (2 * z) for z in range(0, max_zoom + 1))


def sparse_tile_count(
    *,
    global_max_zoom: int,
    deep_max_zoom: int,
    deep_windows: Sequence[DeepWindow],
) -> int:
    """Expected tile count for the sparse global+deep layout."""
    total = dense_tile_count(global_max_zoom)
    if deep_max_zoom <= global_max_zoom:
        return total
    for zoom in range(global_max_zoom + 1, deep_max_zoom + 1):
        seen: set[tuple[int, int]] = set()
        for window in deep_windows:
            seen.update(tiles_covering_window(window, zoom))
        total += len(seen)
    return total


def _write_one_tile(
    pixels: np.ndarray,
    destination: Path,
    zoom: int,
    tile_x: int,
    tile_y: int,
    tile_size: int,
) -> None:
    n = 1 << zoom
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


def write_mercator_tiles(
    equirect_rgb: np.ndarray,
    destination: Path,
    *,
    max_zoom: int | None = None,
    global_max_zoom: int = DEFAULT_GLOBAL_MAX_ZOOM,
    deep_max_zoom: int = DEFAULT_DEEP_MAX_ZOOM,
    deep_windows: Sequence[DeepWindow] | None = None,
    tile_size: int = 256,
    write_manifest: bool = True,
) -> dict:
    """Write XYZ PNG tiles covering the Web Mercator world.

    ``equirect_rgb`` is HxWx3 float 0..1 or uint8.

    Modes:
    - Dense: pass ``max_zoom`` (used by unit tests / legacy callers).
    - Sparse (default when ``max_zoom`` is None): write every tile through
      ``global_max_zoom``, then only tiles intersecting ``deep_windows``
      through ``deep_max_zoom``.
    """
    if equirect_rgb.dtype != np.uint8:
        pixels = (np.clip(equirect_rgb, 0, 1) * 255).astype(np.uint8)
    else:
        pixels = equirect_rgb

    destination.mkdir(parents=True, exist_ok=True)
    # Wipe prior zoom dirs so sparse exports cannot leave stale tiles from an
    # older seed/world (MapLibre will happily stitch the Frankenstein pyramid).
    for child in list(destination.iterdir()):
        if child.is_dir() and child.name.isdigit():
            shutil.rmtree(child)
        elif child.name == "coverage.json":
            child.unlink(missing_ok=True)

    windows = tuple(deep_windows) if deep_windows is not None else DEFAULT_DEEP_WINDOWS
    written = 0
    deep_written = 0
    coverage: dict[str, list[dict]] = {w.name: [] for w in windows}

    if max_zoom is not None:
        # Dense pyramid (tests / explicit override).
        for zoom in range(0, max_zoom + 1):
            n = 1 << zoom
            for tile_x in range(n):
                for tile_y in range(n):
                    _write_one_tile(
                        pixels, destination, zoom, tile_x, tile_y, tile_size
                    )
                    written += 1
        meta = {
            "scheme": "xyz",
            "path": "tiles/color/{z}/{x}/{y}.png",
            "tile_count": written,
            "max_zoom": max_zoom,
            "global_max_zoom": max_zoom,
            "deep_max_zoom": max_zoom,
            "tile_size": tile_size,
            "mercator_max_lat": MERCATOR_MAX_LAT,
            "sparse": False,
            "deep_windows": [],
        }
        if write_manifest:
            (destination / "coverage.json").write_text(
                json.dumps(meta, indent=2) + "\n"
            )
        return meta

    # Sparse: global then deep windows only.
    for zoom in range(0, global_max_zoom + 1):
        n = 1 << zoom
        for tile_x in range(n):
            for tile_y in range(n):
                _write_one_tile(
                    pixels, destination, zoom, tile_x, tile_y, tile_size
                )
                written += 1

    for zoom in range(global_max_zoom + 1, deep_max_zoom + 1):
        seen: set[tuple[int, int]] = set()
        for window in windows:
            coords = tiles_covering_window(window, zoom)
            coverage[window.name].append(
                {"zoom": zoom, "tile_count": len(coords)}
            )
            for tile_x, tile_y in coords:
                if (tile_x, tile_y) in seen:
                    continue
                seen.add((tile_x, tile_y))
                _write_one_tile(
                    pixels, destination, zoom, tile_x, tile_y, tile_size
                )
                written += 1
                deep_written += 1

    meta = {
        "scheme": "xyz",
        "path": "tiles/color/{z}/{x}/{y}.png",
        "tile_count": written,
        "deep_tile_count": deep_written,
        "max_zoom": deep_max_zoom,
        "global_max_zoom": global_max_zoom,
        "deep_max_zoom": deep_max_zoom,
        "tile_size": tile_size,
        "mercator_max_lat": MERCATOR_MAX_LAT,
        "sparse": True,
        "expected_dense_tile_count": dense_tile_count(deep_max_zoom),
        "deep_windows": [asdict(w) for w in windows],
        "coverage": coverage,
    }
    if write_manifest:
        (destination / "coverage.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def iter_deep_window_names(windows: Iterable[DeepWindow] | None = None) -> list[str]:
    wins = DEFAULT_DEEP_WINDOWS if windows is None else windows
    return [w.name for w in wins]
