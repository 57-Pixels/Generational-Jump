"""Ocean-floor age, bathymetry, trenches, and variable shelves."""

from __future__ import annotations

from typing import Any

import numpy as np

from .grid import CubedSphere

EARTH_RADIUS_KM = 6371.0


def age_depth_m(age_ma: np.ndarray) -> np.ndarray:
    """Half-space cooling depth (metres below sea level), flattened after 80 Ma."""
    age = np.asarray(age_ma, dtype=np.float64)
    return np.where(
        age < 80.0,
        2600.0 + 345.0 * np.sqrt(np.maximum(age, 0.0)),
        5650.0 - 2470.0 * np.exp(-0.0278 * age),
    )


def advance_seafloor_age(
    age_ma: np.ndarray,
    continental: np.ndarray,
    ridge: np.ndarray,
    dt_ma: float,
) -> np.ndarray:
    """Age oceanic crust; reset at ridges; keep continents at 0."""
    age = np.asarray(age_ma, dtype=np.float64).copy()
    ocean = continental < 0.28
    age[ocean] = age[ocean] + dt_ma
    born = ocean & (ridge > 0.12)
    age[born] = 0.0
    age[~ocean] = 0.0
    return np.clip(age, 0.0, 220.0)


def build_seafloor_elevation(
    grid: CubedSphere,
    seafloor_age_ma: np.ndarray,
    continental: np.ndarray,
    memory: dict[str, np.ndarray],
    *,
    seed: int = 0,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return ocean elevation (m) and feature masks (trench, back_arc, swell)."""
    rng = np.random.default_rng(seed + 17)
    age = np.asarray(seafloor_age_ma, dtype=np.float64)
    ocean = continental < 0.28
    depth = age_depth_m(age)
    elevation = -depth

    # Fracture-zone scarps: transform memory creates age-offset lineations.
    transform = np.asarray(memory.get("transform", np.zeros(grid.size)), dtype=np.float64)
    elevation -= 180.0 * transform * ocean.astype(float)

    # Trenches at subduction with oceanic downgoing plate.
    subduction = np.asarray(memory.get("subduction", np.zeros(grid.size)), dtype=np.float64)
    trench = (subduction > 0.25) & ocean
    trench_strength = np.clip(subduction, 0, 1) * trench.astype(float)
    trench_strength = grid.smooth(trench_strength, iterations=1, self_weight=3.0)
    elevation -= 4000.0 * trench_strength
    # Outer rise on the seaward fringe of the trench.
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    near_trench = ocean & ~trench & np.any(valid & trench[safe], axis=1)
    elevation[near_trench] += 200.0

    # Back-arc basins behind arcs: raised floor ~3000 m.
    arc = np.asarray(memory.get("arc", np.zeros(grid.size)), dtype=np.float64)
    back_arc = ocean & (arc > 0.15) & (subduction < 0.2)
    back_arc_soft = grid.smooth(back_arc.astype(float), iterations=2)
    target = -3000.0
    elevation = np.where(
        back_arc_soft > 0.2,
        elevation * (1.0 - 0.65 * back_arc_soft) + target * 0.65 * back_arc_soft,
        elevation,
    )

    # Hotspot swells: a few broad Gaussians.
    n_hotspots = 4
    candidates = np.flatnonzero(ocean)
    swells = np.zeros(grid.size)
    if len(candidates):
        picks = rng.choice(candidates, size=min(n_hotspots, len(candidates)), replace=False)
        for cell in picks:
            center = grid.xyz[int(cell)]
            # Angular radius ~1000 km / R_earth ≈ 0.157 rad.
            cosang = np.clip(grid.xyz @ center, -1.0, 1.0)
            ang = np.arccos(cosang)
            sigma = 1000.0 / EARTH_RADIUS_KM
            bump = 800.0 * np.exp(-0.5 * (ang / sigma) ** 2)
            swells = np.maximum(swells, bump)
        elevation += swells * ocean.astype(float)

    # Ridges sit high.
    ridge = np.asarray(memory.get("ridge", np.zeros(grid.size)), dtype=np.float64)
    elevation += 450.0 * ridge * ocean.astype(float)

    extras = {
        "trench": trench_strength,
        "back_arc": back_arc_soft,
        "swell": swells * ocean.astype(float),
    }
    return elevation, extras


def shelf_mask(geology: Any, grid: CubedSphere) -> tuple[np.ndarray, np.ndarray]:
    """Return (passive_shelf, active_shelf) boolean masks."""
    continental = geology.continental
    elev = geology.elevation_m
    passive_m = geology.history.get("passive_margin", np.zeros(grid.size))
    subduction = geology.history.get("subduction", np.zeros(grid.size))
    arc = geology.history.get("arc", np.zeros(grid.size))
    shelf_band = (elev < 0.0) & (elev > -250.0) & (continental > 0.08) & (continental < 0.7)
    passive = shelf_band & (passive_m > 0.15) & (subduction < 0.2) & (arc < 0.2)
    active = shelf_band & ((subduction > 0.15) | (arc > 0.2))
    return passive, active


def apply_variable_shelves(
    elevation: np.ndarray,
    continental_soft: np.ndarray,
    continental: np.ndarray,
    memory: dict[str, np.ndarray],
    grid: CubedSphere,
) -> np.ndarray:
    """Overwrite shelf elevations with margin-type-dependent widths."""
    elev = elevation.copy()
    passive_m = memory.get("passive_margin", np.zeros(grid.size))
    active_m = np.maximum(
        memory.get("subduction", np.zeros(grid.size)),
        memory.get("arc", np.zeros(grid.size)),
    )
    # Passive: wide band (softer continental occupancy → deeper).
    passive_zone = (
        (continental_soft > 0.08)
        & (continental_soft < 0.62)
        & (continental < 0.58)
        & (passive_m > 0.12)
        & (active_m < 0.18)
    )
    elev[passive_zone] = -80.0 + 380.0 * (
        (continental_soft[passive_zone] - 0.08) / 0.54
    ) - 200.0
    # Active: narrow steep shelf.
    active_zone = (
        (continental_soft > 0.18)
        & (continental_soft < 0.48)
        & (continental < 0.55)
        & (active_m > 0.15)
    )
    elev[active_zone] = -40.0 + 280.0 * (
        (continental_soft[active_zone] - 0.18) / 0.30
    ) - 180.0
    return elev
