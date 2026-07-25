"""Wave-driven coastal evolution: fetch, longshore drift, and ragged shores."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .grid import CubedSphere

EARTH_RADIUS_KM = 6371.0


@dataclass
class CoastalResult:
    elevation_m: np.ndarray
    wave_energy: np.ndarray
    sediment_m: np.ndarray
    spit_score: np.ndarray


def _coast_mask(
    grid: CubedSphere, elevation: np.ndarray, sea_level_m: float
) -> np.ndarray:
    land = elevation >= sea_level_m
    ocean = ~land
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    return land & np.any(valid & ocean[safe], axis=1)


def _fetch_km(
    grid: CubedSphere,
    land: np.ndarray,
    wind: np.ndarray,
    max_steps: int = 48,
) -> np.ndarray:
    """Open-water distance upwind of each cell (km)."""
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    # Upstream neighbour most opposed to wind (comes from upwind).
    xyz = grid.xyz
    chosen = np.arange(grid.size, dtype=np.int64)
    for start in range(0, grid.size, 200_000):
        end = min(start + 200_000, grid.size)
        v = valid[start:end]
        s = safe[start:end]
        here = xyz[start:end]
        nb = xyz[s]
        direction = here[:, None, :] - nb
        radial = np.einsum("mki,mi->mk", direction, here)
        direction = direction - radial[:, :, None] * here[:, None, :]
        direction /= np.maximum(
            np.linalg.norm(direction, axis=2, keepdims=True), 1e-12
        )
        # Upwind neighbour: sits against the wind, so (here - nb) aligns with wind.
        alignment = np.einsum("mki,mi->mk", direction, wind[start:end])
        alignment = np.where(v, alignment, -np.inf)
        local = np.argmax(alignment, axis=1)
        chosen[start:end] = s[np.arange(end - start), local]

    dx = EARTH_RADIUS_KM * np.sqrt(np.maximum(grid.area_sr, 1e-12))
    fetch = np.zeros(grid.size, dtype=np.float64)
    ocean = ~land
    cursor = np.arange(grid.size)
    active = ocean.copy()
    for _ in range(max_steps):
        nxt = chosen[cursor]
        step = active & ocean[nxt]
        fetch = np.where(step, fetch + dx[cursor], fetch)
        cursor = np.where(step, nxt, cursor)
        active &= step
        if not np.any(active):
            break
    # Propagate fetch onto coastal land from neighbouring ocean.
    coastal_fetch = np.zeros(grid.size, dtype=np.float64)
    for slot in range(grid.neighbors.shape[1]):
        n = safe[:, slot]
        mask = valid[:, slot] & land & ocean[n]
        coastal_fetch[mask] = np.maximum(coastal_fetch[mask], fetch[n[mask]])
    return np.where(land, coastal_fetch, fetch)


def compute_wave_energy(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    wind: np.ndarray,
) -> np.ndarray:
    land = elevation_m >= sea_level_m
    fetch = _fetch_km(grid, land, wind)
    wind_speed = np.linalg.norm(wind, axis=1)
    energy = np.sqrt(np.maximum(fetch, 0.0)) * (0.35 + 0.65 * wind_speed)
    coastal = _coast_mask(grid, elevation_m, sea_level_m)
    return np.where(coastal | ~land, energy, 0.0)


def coastline_fractal_dimension(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    boxes: tuple[int, ...] = (8, 12, 16, 24, 32, 48),
) -> float:
    """Box-counting fractal dimension of the coastline in equirect space."""
    coastal = _coast_mask(grid, elevation_m, sea_level_m)
    if int(coastal.sum()) < 12:
        return 1.0
    lon = grid.lon_deg[coastal]
    lat = grid.lat_deg[coastal]
    # Normalise to unit square.
    x = (lon + 180.0) / 360.0
    y = (lat + 90.0) / 180.0
    sizes = []
    counts = []
    for b in boxes:
        ix = np.clip((x * b).astype(np.int32), 0, b - 1)
        iy = np.clip((y * b).astype(np.int32), 0, b - 1)
        occupied = len({(int(a), int(c)) for a, c in zip(ix, iy)})
        if occupied < 2:
            continue
        sizes.append(1.0 / b)
        counts.append(float(occupied))
    if len(sizes) < 3:
        return 1.0
    log_inv = np.log(1.0 / np.asarray(sizes))
    log_n = np.log(np.asarray(counts))
    # D ≈ slope of log N vs log(1/ε)
    slope = float(np.polyfit(log_inv, log_n, 1)[0])
    return float(np.clip(slope, 1.0, 1.6))


def evolve_coastline(
    grid: CubedSphere,
    elevation_m: np.ndarray,
    sea_level_m: float,
    wind: np.ndarray,
    iterations: int = 20,
    seed: int = 0,
) -> CoastalResult:
    """Erode exposed headlands, deposit in bays, and drive longshore drift."""
    elev = np.asarray(elevation_m, dtype=np.float64).copy()
    sediment = np.zeros(grid.size, dtype=np.float64)
    spit = np.zeros(grid.size, dtype=np.float64)
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    rng = np.random.default_rng(seed)

    wave = compute_wave_energy(grid, elev, sea_level_m, wind)
    for step in range(max(iterations, 0)):
        land = elev >= sea_level_m
        ocean = ~land
        coastal = land & np.any(valid & ocean[safe], axis=1)
        wave = compute_wave_energy(grid, elev, sea_level_m, wind)

        # Local shoreline curvature proxy: convex (headland) vs concave (bay).
        elev_nb = np.where(valid, elev[safe], elev[:, None])
        land_nb = valid & land[safe]
        ocean_nb = valid & ocean[safe]
        openness = ocean_nb.sum(axis=1).astype(np.float64)
        neighbor_land_mean = np.where(
            land_nb.any(axis=1),
            np.where(land_nb, elev_nb, 0.0).sum(axis=1)
            / np.maximum(land_nb.sum(axis=1), 1),
            elev,
        )
        headland = coastal & (elev > neighbor_land_mean + 5.0) & (openness >= 2)
        bay = coastal & (elev < neighbor_land_mean + 2.0) & (openness <= 3)

        # Exposure from wave energy.
        exposed = coastal & (wave > np.percentile(wave[coastal], 60) if np.any(coastal) else False)
        sheltered = coastal & (wave < np.percentile(wave[coastal], 40) if np.any(coastal) else False)

        erode = np.zeros(grid.size, dtype=np.float64)
        # Only high-energy exposure retreats; headlands without fetch are spared.
        erode[exposed] = 0.85 * wave[exposed]
        erode[headland & exposed] *= 1.35
        erode = np.minimum(erode, 20.0)
        elev -= erode
        sediment += erode

        # Longshore drift: move sediment alongshore in the wind-parallel direction.
        drifted = np.zeros_like(sediment)
        coast_cells = np.flatnonzero(coastal & (sediment > 0))
        for cell in coast_cells:
            best = -1
            best_align = -np.inf
            for nb in grid.neighbors[cell]:
                if nb < 0 or not (coastal[nb] or bay[nb] or sheltered[nb]):
                    continue
                delta = grid.xyz[nb] - grid.xyz[cell]
                radial = float(delta @ grid.xyz[cell])
                delta = delta - radial * grid.xyz[cell]
                norm = np.linalg.norm(delta)
                if norm < 1e-12:
                    continue
                delta /= norm
                align = abs(float(delta @ wind[cell]))
                # Bias drift toward lower-energy neighbours (bays).
                energy_bias = 1.0 / (1.0 + wave[nb])
                score = align * 0.7 + energy_bias * 0.3
                if score > best_align:
                    best_align = score
                    best = int(nb)
            if best >= 0:
                move = 0.55 * sediment[cell]
                sediment[cell] -= move
                drifted[best] += move
        sediment += drifted

        # Deposit in sheltered bays and low-energy pockets.
        deposit = np.zeros(grid.size, dtype=np.float64)
        budget = float(erode.sum())
        sheltered_cells = np.flatnonzero(sheltered | bay)
        if sheltered_cells.size and budget > 0:
            share = budget * 0.8 / sheltered_cells.size
            deposit[sheltered_cells] = share
        # Also lock drifted sediment in place on sheltered cells.
        deposit[sheltered | bay] += sediment[sheltered | bay] * 0.7
        deposit = np.minimum(deposit, 40.0)
        elev += deposit
        sediment = np.maximum(sediment - deposit, 0.0)

        # Spits / barriers: deposit just offshore of sheltered coasts.
        if np.any(coastal):
            low_q = float(np.percentile(wave[coastal], 55))
        else:
            low_q = 0.0
        nearshore = ocean & np.any(valid & coastal[safe], axis=1) & (wave <= low_q)
        spit_deposit = np.minimum(sediment, 10.0) * nearshore.astype(float) * 0.4
        elev += spit_deposit
        sediment = np.maximum(sediment - spit_deposit, 0.0)
        spit = np.maximum(spit, spit_deposit)

        # Barrier / lagoon hint: raise shallow nearshore bars.
        shallow = ocean & (elev > sea_level_m - 40.0) & nearshore
        elev[shallow] += 0.15 * spit[shallow]

        # Rias: deepen drowned river valleys (low land corridors into the sea).
        drowned = ocean & (elev > sea_level_m - 120.0)
        valley = drowned & (elev <= np.where(valid, elev_nb, np.inf).min(axis=1) + 15.0)
        elev[valley] -= 1.5

        # Keep a little noise so coasts do not re-smooth to a circle.
        jitter = rng.normal(0.0, 0.25, size=grid.size)
        elev = np.where(coastal, elev + jitter, elev)
        sediment *= 0.7

        # Mild Laplacian on the shoreline using land neighbours only.
        if step % 4 == 3:
            coastal_now = (elev >= sea_level_m) & np.any(
                valid & (elev[safe] < sea_level_m), axis=1
            )
            land_now = elev >= sea_level_m
            land_nb = valid & land_now[safe]
            nb_elev = np.where(land_nb, elev[safe], 0.0)
            mean_nb = nb_elev.sum(axis=1) / np.maximum(land_nb.sum(axis=1), 1)
            has_land_nb = land_nb.any(axis=1)
            elev = np.where(
                coastal_now & has_land_nb, 0.9 * elev + 0.1 * mean_nb, elev
            )

    wave = compute_wave_energy(grid, elev, sea_level_m, wind)
    return CoastalResult(
        elevation_m=elev,
        wave_energy=wave,
        sediment_m=sediment,
        spit_score=spit,
    )
