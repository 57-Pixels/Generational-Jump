"""Nested window refinement for T2–T4 detail."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .climate import ClimateFields
from .grid import CubedSphere

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class WindowSpec:
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float
    target_km: float
    margin: float = 0.1

    def expanded(self) -> tuple[float, float, float, float]:
        dlon = (self.lon_max - self.lon_min) * self.margin
        dlat = (self.lat_max - self.lat_min) * self.margin
        return (
            self.lon_min - dlon,
            self.lon_max + dlon,
            self.lat_min - dlat,
            self.lat_max + dlat,
        )


@dataclass
class WindowField:
    lon_deg: np.ndarray
    lat_deg: np.ndarray
    elevation_m: np.ndarray
    parent_elevation_m: np.ndarray
    parent_slope: np.ndarray
    temperature_c: np.ndarray
    precipitation_mm_yr: np.ndarray
    nx: int
    ny: int
    spec: WindowSpec
    seed: int

    @property
    def size(self) -> int:
        return int(self.elevation_m.size)


def _lonlat_to_xyz(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lon = np.deg2rad(lon_deg)
    lat = np.deg2rad(lat_deg)
    cl = np.cos(lat)
    return np.column_stack([cl * np.cos(lon), cl * np.sin(lon), np.sin(lat)])


def _sample_parent(
    grid: CubedSphere, values: np.ndarray, lon: np.ndarray, lat: np.ndarray
) -> np.ndarray:
    xyz = _lonlat_to_xyz(lon, lat)
    # Nearest parent cell on the sphere.
    # For modest windows this is fine; chunk if needed later.
    out = np.empty(lon.shape[0], dtype=np.float64)
    chunk = 4000
    for start in range(0, lon.shape[0], chunk):
        end = min(start + chunk, lon.shape[0])
        dots = xyz[start:end] @ grid.xyz.T
        out[start:end] = values[np.argmax(dots, axis=1)]
    return out


def _parent_slope(grid: CubedSphere, elevation: np.ndarray) -> np.ndarray:
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    dx = EARTH_RADIUS_KM * 1000.0 * np.sqrt(np.maximum(grid.area_sr, 1e-12))
    elev_nb = np.where(valid, elevation[safe], elevation[:, None])
    drop = np.where(valid, np.abs(elevation[:, None] - elev_nb), 0.0).max(axis=1)
    return drop / np.maximum(dx, 1.0)


def extract_window(
    parent: CubedSphere,
    elevation_m: np.ndarray,
    climate: ClimateFields,
    spec: WindowSpec,
    seed: int = 0,
) -> WindowField:
    """Resample a lat/lon window (+ margin) onto a local equal-angle grid."""
    lon0, lon1, lat0, lat1 = spec.expanded()
    # Equal-angle spacing ≈ target_km at mid-latitude.
    mid_lat = 0.5 * (lat0 + lat1)
    km_per_deg_lat = 111.0
    km_per_deg_lon = max(111.0 * np.cos(np.deg2rad(mid_lat)), 20.0)
    dlat = spec.target_km / km_per_deg_lat
    dlon = spec.target_km / km_per_deg_lon
    ny = max(int(np.ceil((lat1 - lat0) / dlat)) + 1, 4)
    nx = max(int(np.ceil((lon1 - lon0) / dlon)) + 1, 4)
    lons = np.linspace(lon0, lon1, nx)
    lats = np.linspace(lat0, lat1, ny)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    lon = lon_grid.ravel()
    lat = lat_grid.ravel()
    parent_elev = _sample_parent(parent, elevation_m, lon, lat)
    slope = _sample_parent(parent, _parent_slope(parent, elevation_m), lon, lat)
    temp = _sample_parent(parent, climate.temperature_c, lon, lat)
    precip = _sample_parent(parent, climate.precipitation_mm_yr, lon, lat)
    return WindowField(
        lon_deg=lon,
        lat_deg=lat,
        elevation_m=parent_elev.copy(),
        parent_elevation_m=parent_elev,
        parent_slope=slope,
        temperature_c=temp,
        precipitation_mm_yr=precip,
        nx=nx,
        ny=ny,
        spec=spec,
        seed=seed,
    )


def _window_neighbors(nx: int, ny: int) -> np.ndarray:
    """4-connected neighbours on the window mesh; shape (N, 4), -1 = none."""
    n = nx * ny
    neighbors = np.full((n, 4), -1, dtype=np.int32)
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            if i > 0:
                neighbors[idx, 0] = idx - 1
            if i + 1 < nx:
                neighbors[idx, 1] = idx + 1
            if j > 0:
                neighbors[idx, 2] = idx - nx
            if j + 1 < ny:
                neighbors[idx, 3] = idx + nx
    return neighbors


def _conditioned_detail(window: WindowField) -> np.ndarray:
    """High-frequency relief from parent slope — no free fractal noise."""
    rng = np.random.default_rng(window.seed + 17)
    # Structured field: low-order Fourier-like pattern in local UV, amplitude
    # gated by parent slope so flat plains stay flat.
    u = (window.lon_deg - window.lon_deg.min()) / max(
        float(window.lon_deg.max() - window.lon_deg.min()), 1e-6
    )
    v = (window.lat_deg - window.lat_deg.min()) / max(
        float(window.lat_deg.max() - window.lat_deg.min()), 1e-6
    )
    phase = rng.uniform(0, 2 * np.pi, size=4)
    pattern = (
        np.sin(2 * np.pi * (3 * u + 1 * v) + phase[0])
        + 0.6 * np.sin(2 * np.pi * (5 * u - 2 * v) + phase[1])
        + 0.35 * np.sin(2 * np.pi * (8 * u + 5 * v) + phase[2])
        + 0.2 * np.sin(2 * np.pi * (11 * v - 4 * u) + phase[3])
    )
    amp = 35.0 * np.clip(window.parent_slope / 0.05, 0.0, 1.0)
    # Climate gating: arid → sharper canyons (more incision amplitude).
    arid = np.clip(1.0 - window.precipitation_mm_yr / 1200.0, 0.2, 1.0)
    detail = pattern * amp * arid
    # Zero-mean so the parent hypsometry is preserved.
    return detail - float(detail.mean())


def _stream_power_window(
    elev: np.ndarray,
    neighbors: np.ndarray,
    precip: np.ndarray,
    iterations: int,
    dx_m: float,
) -> np.ndarray:
    """Tiny detachment-limited step on the window mesh."""
    out = elev.copy()
    n = out.size
    for _ in range(max(iterations, 0)):
        recv = np.full(n, -1, dtype=np.int32)
        for i in range(n):
            best = -1
            best_z = out[i]
            for nb in neighbors[i]:
                if nb >= 0 and out[nb] < best_z:
                    best_z = out[nb]
                    best = int(nb)
            recv[i] = best
        # Accumulation proxy.
        drain = np.maximum(precip, 50.0) * (dx_m / 1000.0) ** 2
        order = np.argsort(-out)
        for i in order:
            j = recv[i]
            if j >= 0:
                drain[j] += drain[i]
        for i in range(n):
            j = recv[i]
            if j < 0:
                continue
            drop = out[i] - out[j]
            if drop <= 0:
                continue
            slope = drop / dx_m
            cut = 2.0e-6 * (drain[i] ** 0.5) * slope * 200.0
            cut = min(cut, 0.25 * drop, 8.0)
            out[i] -= cut
            out[j] += 0.35 * cut
    return out


def refine_window(
    window: WindowField,
    iterations: int = 12,
    seed: int | None = None,
) -> WindowField:
    """Add conditioned detail and a short fluvial pass; re-anchor to parent."""
    if seed is not None:
        window = WindowField(**{**window.__dict__, "seed": int(seed)})
    detail = _conditioned_detail(window)
    elev = window.parent_elevation_m + detail
    neighbors = _window_neighbors(window.nx, window.ny)
    dx_m = max(window.spec.target_km * 1000.0, 1000.0)
    elev = _stream_power_window(
        elev, neighbors, window.precipitation_mm_yr, iterations=iterations, dx_m=dx_m
    )
    # Re-anchor: preserve parent mean locally so downsampling stays within RMS.
    residual = elev - window.parent_elevation_m
    # Subtract a smoothed residual so only high-frequency structure remains.
    ny, nx = window.ny, window.nx
    res = residual.reshape(ny, nx)
    kernel = np.array([1, 2, 1], dtype=np.float64)
    kernel = kernel / kernel.sum()
    smooth = res.copy()
    for _ in range(2):
        # Separable box-ish smooth with edge clamp.
        pad = np.pad(smooth, ((0, 0), (1, 1)), mode="edge")
        smooth = kernel[0] * pad[:, :-2] + kernel[1] * pad[:, 1:-1] + kernel[2] * pad[:, 2:]
        pad = np.pad(smooth, ((1, 1), (0, 0)), mode="edge")
        smooth = kernel[0] * pad[:-2, :] + kernel[1] * pad[1:-1, :] + kernel[2] * pad[2:, :]
    highfreq = res - smooth
    elev = window.parent_elevation_m + np.clip(highfreq.ravel(), -45.0, 45.0)
    return WindowField(
        lon_deg=window.lon_deg.copy(),
        lat_deg=window.lat_deg.copy(),
        elevation_m=elev,
        parent_elevation_m=window.parent_elevation_m.copy(),
        parent_slope=window.parent_slope.copy(),
        temperature_c=window.temperature_c.copy(),
        precipitation_mm_yr=window.precipitation_mm_yr.copy(),
        nx=window.nx,
        ny=window.ny,
        spec=window.spec,
        seed=window.seed,
    )


def _edge_weight(window: WindowField) -> np.ndarray:
    """1 in core, tapers to 0 across the margin band."""
    lon0, lon1, lat0, lat1 = window.spec.expanded()
    core = window.spec
    # Distance outside core as fraction of margin width.
    dlon = max((lon1 - lon0) * window.spec.margin, 1e-6)
    dlat = max((lat1 - lat0) * window.spec.margin, 1e-6)
    wx = np.ones(window.size)
    wy = np.ones(window.size)
    left = window.lon_deg < core.lon_min
    right = window.lon_deg > core.lon_max
    below = window.lat_deg < core.lat_min
    above = window.lat_deg > core.lat_max
    wx[left] = np.clip(1.0 - (core.lon_min - window.lon_deg[left]) / dlon, 0.0, 1.0)
    wx[right] = np.clip(1.0 - (window.lon_deg[right] - core.lon_max) / dlon, 0.0, 1.0)
    wy[below] = np.clip(1.0 - (core.lat_min - window.lat_deg[below]) / dlat, 0.0, 1.0)
    wy[above] = np.clip(1.0 - (window.lat_deg[above] - core.lat_max) / dlat, 0.0, 1.0)
    return wx * wy


def blend_windows(windows: list[WindowField]) -> WindowField:
    """Merge overlapping windows with margin fade; order-independent."""
    if not windows:
        raise ValueError("no windows to blend")
    if len(windows) == 1:
        return windows[0]
    # Quantize lon/lat so identical sample sites merge regardless of order.
    scale = 1e4
    buckets: dict[tuple[int, int], list[tuple[float, float, float, float]]] = {}
    for win in windows:
        w = _edge_weight(win)
        for i in range(win.size):
            key = (int(round(win.lon_deg[i] * scale)), int(round(win.lat_deg[i] * scale)))
            buckets.setdefault(key, []).append(
                (
                    float(win.lon_deg[i]),
                    float(win.lat_deg[i]),
                    float(win.elevation_m[i]),
                    float(w[i]),
                )
            )
    keys = sorted(buckets)
    lon = np.empty(len(keys))
    lat = np.empty(len(keys))
    elev = np.empty(len(keys))
    for i, key in enumerate(keys):
        samples = buckets[key]
        weights = np.array([s[3] for s in samples], dtype=np.float64)
        if float(weights.sum()) <= 1e-12:
            weights = np.ones(len(samples))
        weights = weights / weights.sum()
        lon[i] = sum(s[0] * w for s, w in zip(samples, weights))
        lat[i] = sum(s[1] * w for s, w in zip(samples, weights))
        elev[i] = sum(s[2] * w for s, w in zip(samples, weights))
    # Synthetic rectangular metadata from the union.
    spec = WindowSpec(
        lon_min=float(min(w.spec.lon_min for w in windows)),
        lon_max=float(max(w.spec.lon_max for w in windows)),
        lat_min=float(min(w.spec.lat_min for w in windows)),
        lat_max=float(max(w.spec.lat_max for w in windows)),
        target_km=float(np.mean([w.spec.target_km for w in windows])),
        margin=float(np.mean([w.spec.margin for w in windows])),
    )
    return WindowField(
        lon_deg=lon,
        lat_deg=lat,
        elevation_m=elev,
        parent_elevation_m=elev.copy(),
        parent_slope=np.zeros_like(elev),
        temperature_c=np.zeros_like(elev),
        precipitation_mm_yr=np.zeros_like(elev),
        nx=len(keys),
        ny=1,
        spec=spec,
        seed=windows[0].seed,
    )


def write_tile(path: Path, window: WindowField) -> None:
    """Disk-backed tile for T3/T4 streaming."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        lon_deg=window.lon_deg,
        lat_deg=window.lat_deg,
        elevation_m=window.elevation_m,
        parent_elevation_m=window.parent_elevation_m,
        nx=window.nx,
        ny=window.ny,
        seed=window.seed,
        lon_min=window.spec.lon_min,
        lon_max=window.spec.lon_max,
        lat_min=window.spec.lat_min,
        lat_max=window.spec.lat_max,
        target_km=window.spec.target_km,
        margin=window.spec.margin,
    )


def read_tile(path: Path) -> WindowField:
    data = np.load(path)
    spec = WindowSpec(
        lon_min=float(data["lon_min"]),
        lon_max=float(data["lon_max"]),
        lat_min=float(data["lat_min"]),
        lat_max=float(data["lat_max"]),
        target_km=float(data["target_km"]),
        margin=float(data["margin"]),
    )
    return WindowField(
        lon_deg=data["lon_deg"],
        lat_deg=data["lat_deg"],
        elevation_m=data["elevation_m"],
        parent_elevation_m=data["parent_elevation_m"],
        parent_slope=np.zeros_like(data["elevation_m"]),
        temperature_c=np.zeros_like(data["elevation_m"]),
        precipitation_mm_yr=np.zeros_like(data["elevation_m"]),
        nx=int(data["nx"]),
        ny=int(data["ny"]),
        spec=spec,
        seed=int(data["seed"]),
    )
