"""Ocean surface circulation and SST for climate coupling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import CubedSphere


@dataclass
class OceanFields:
    sst_c: np.ndarray
    upwelling: np.ndarray
    current_xyz: np.ndarray


def _streamfunction(grid: CubedSphere, wind: np.ndarray) -> np.ndarray:
    """Coarse wind-driven streamfunction: subtropical gyres with western bias."""
    lat = grid.lat_deg
    lon = grid.lon_deg
    gyre = np.sin(np.pi * np.clip(lat, -60, 60) / 60.0)
    basin = np.sin(np.deg2rad(lon) * 2.0)
    western = 0.55 + 0.45 * np.cos(np.deg2rad((lon + 60.0) % 360.0 - 180.0))
    psi = gyre * basin * western
    zonal = wind[:, 0] * (-grid.xyz[:, 1]) + wind[:, 1] * grid.xyz[:, 0]
    psi = psi * (0.6 + 0.4 * np.clip(np.abs(zonal), 0, 1))
    return grid.smooth(psi, iterations=2)


def compute_ocean(
    grid: CubedSphere,
    land: np.ndarray,
    wind: np.ndarray,
    air_temp_c: np.ndarray,
) -> OceanFields:
    """Build surface currents, SST, and eastern-margin upwelling."""
    ocean = ~land
    psi = _streamfunction(grid, wind)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)

    dpsi = np.where(valid, psi[safe] - psi[:, None], 0.0)
    strength = np.max(np.abs(dpsi), axis=1)
    slot = np.argmax(np.abs(dpsi), axis=1)
    target = safe[np.arange(grid.size), slot]
    direction = grid.xyz[target] - grid.xyz
    radial = np.einsum("ij,ij->i", direction, grid.xyz)
    direction = direction - radial[:, None] * grid.xyz
    norm = np.linalg.norm(direction, axis=1, keepdims=True)
    direction = direction / np.maximum(norm, 1e-12)
    current = direction * strength[:, None] * ocean.astype(float)[:, None]

    lon = grid.lon_deg
    lat = grid.lat_deg
    land_east = np.zeros(grid.size, dtype=bool)
    land_west = np.zeros(grid.size, dtype=bool)
    for i in range(grid.neighbors.shape[1]):
        n = safe[:, i]
        land_east |= valid[:, i] & land[n] & (grid.lon_deg[n] > lon)
        land_west |= valid[:, i] & land[n] & (grid.lon_deg[n] < lon)

    west_boundary = ocean & land_east & (np.abs(lat) > 10) & (np.abs(lat) < 50)
    east_boundary = ocean & land_west & (np.abs(lat) > 8) & (np.abs(lat) < 40)
    current[west_boundary] *= 2.2

    sst = 28.0 - 0.0060 * np.abs(lat) ** 2
    sst = np.where(ocean, sst, air_temp_c)
    upstream = target
    for _ in range(24):
        incoming = sst[upstream]
        baseline = 28.0 - 0.0060 * np.abs(lat) ** 2
        sst = np.where(ocean, 0.82 * sst + 0.18 * incoming, sst)
        sst = np.where(ocean, 0.92 * sst + 0.08 * baseline, sst)

    sst = np.where(west_boundary, sst + 5.0, sst)
    upwelling = grid.smooth(east_boundary.astype(float), iterations=2)
    sst = sst - 9.0 * upwelling

    equatorial = ocean & (np.abs(lat) < 6.0)
    upwelling = np.maximum(upwelling, 0.55 * equatorial.astype(float))
    sst = np.where(equatorial, sst - 2.5, sst)
    sst = np.clip(sst, -2.0, 32.0)
    return OceanFields(sst_c=sst, upwelling=upwelling, current_xyz=current)
