"""Deep-time crust fields, geologic events, and bedrock relief."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .grid import CubedSphere
from .plates import (
    BOUNDARY_CONVERGENT,
    BOUNDARY_DIVERGENT,
    BOUNDARY_TRANSFORM,
    PlateModel,
    rodrigues_rotate,
)
from .seafloor import (
    advance_seafloor_age,
    apply_variable_shelves,
    build_seafloor_elevation,
)

EVENT_NAMES = (
    "ridge",
    "continental_rift",
    "subduction",
    "arc",
    "collision",
    "suture",
    "transform",
    "passive_margin",
    "hydrothermal",
    "mafic",
    "alkaline",
    "exhumation",
)

OCEAN_THICKNESS_KM = 7.0
CONTINENT_MIN_KM = 17.0
CONTINENT_CORE_KM = 38.0


def _smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    t = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.maximum(np.linalg.norm(vectors, axis=-1, keepdims=True), 1e-15)


@dataclass(frozen=True)
class GeologyConfig:
    seed: int = 42
    ticks: int = 80
    dt_ma: float = 8.0
    n_plates: int = 12
    n_continents: int = 7


@dataclass
class GeologyFields:
    plate_id: np.ndarray
    continent_id: np.ndarray
    terrane_id: np.ndarray
    continental: np.ndarray
    crust_age_ma: np.ndarray
    crust_thickness_km: np.ndarray
    elevation_m: np.ndarray
    orogeny: np.ndarray
    basin_depth: np.ndarray
    sediment: np.ndarray
    history: dict[str, np.ndarray]
    lithology: dict[str, np.ndarray]
    paleoclimate: dict[str, np.ndarray]
    landmass_id: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.int32))
    seafloor_age_ma: np.ndarray = field(
        default_factory=lambda: np.empty(0, dtype=np.float64)
    )


def _tangent_basis(center: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = _normalize(center.reshape(1, 3))[0]
    hint = np.array([0.0, 0.0, 1.0]) if abs(center[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    east = np.cross(hint, center)
    east = east / max(float(np.linalg.norm(east)), 1e-15)
    north = np.cross(center, east)
    return east, north


def _anisotropic_lobe(
    grid: CubedSphere,
    center: np.ndarray,
    axis_a: float,
    axis_b: float,
    angle: float,
    noise: np.ndarray,
) -> np.ndarray:
    """Irregular elongated occupancy in the tangent plane (not a circular cap)."""
    east, north = _tangent_basis(center)
    cosine = np.cos(angle)
    sine = np.sin(angle)
    e1 = cosine * east + sine * north
    e2 = -sine * east + cosine * north
    u = grid.xyz @ e1
    v = grid.xyz @ e2
    radial = np.sqrt((u / max(axis_a, 1e-6)) ** 2 + (v / max(axis_b, 1e-6)) ** 2)
    warped = radial + 0.28 * noise + 0.12 * np.sin(4.0 * np.arctan2(v, u + 1e-9))
    return 1.0 - _smoothstep(0.72, 1.18, warped)


def _seed_crust_fields(
    grid: CubedSphere,
    plate_model: PlateModel,
    config: GeologyConfig,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    thickness = np.full(grid.size, OCEAN_THICKNESS_KM, dtype=np.float64)
    continent_id = np.full(grid.size, -1, dtype=np.int32)
    basement_age = np.zeros(grid.size, dtype=np.float64)
    noise = grid.smooth(rng.normal(size=grid.size), iterations=6)
    noise /= max(float(np.std(noise)), 1e-9)

    n_plates = len(plate_model.seed_xyz)
    selected = rng.choice(
        n_plates, size=min(config.n_continents, n_plates), replace=False
    )
    for continent, plate in enumerate(selected):
        main = plate_model.seed_xyz[int(plate)]
        age = float(rng.uniform(900.0, 3500.0))
        lobe_count = int(rng.integers(4, 8))
        score = np.zeros(grid.size)
        for lobe in range(lobe_count):
            if lobe == 0:
                center = main.copy()
            else:
                axis = np.cross(main, rng.normal(size=3))
                if np.linalg.norm(axis) < 1e-8:
                    axis = np.cross(main, np.array([0.0, 0.0, 1.0]))
                center = rodrigues_rotate(
                    main[None, :], axis, float(rng.uniform(0.10, 0.42))
                )[0]
            # Strongly anisotropic: one axis often 2–4× the other.
            short = float(rng.uniform(0.14, 0.28))
            long = float(rng.uniform(0.36, 0.78))
            if rng.random() < 0.5:
                short, long = long, short
            angle = float(rng.uniform(0.0, np.pi))
            score = np.maximum(
                score,
                _anisotropic_lobe(grid, center, long, short, angle, noise),
            )
        mask = score > 0.20
        thickness[mask] = np.maximum(
            thickness[mask],
            CONTINENT_CORE_KM * (0.72 + 0.45 * score[mask]),
        )
        continent_id[mask] = continent
        basement_age[mask] = np.maximum(
            basement_age[mask], age + rng.normal(0.0, 80.0, size=int(mask.sum()))
        )
    return thickness, continent_id, basement_age


def _advect_scalar(
    grid: CubedSphere,
    plate_model: PlateModel,
    values: np.ndarray,
    dt_ma: float,
) -> np.ndarray:
    """Backward-remesh advection with each cell's current plate Euler pole."""
    out = values.copy()
    n_plates = len(plate_model.seed_xyz)
    for plate in range(n_plates):
        mask = plate_model.plate_id == plate
        if not np.any(mask):
            continue
        omega = plate_model.omega_xyz[plate]
        rate = float(np.linalg.norm(omega))
        if rate < 1e-15 or abs(dt_ma) < 1e-15:
            continue
        source_xyz = rodrigues_rotate(grid.xyz[mask], omega, -rate * dt_ma)
        source = grid.indices_for_xyz(source_xyz)
        out[mask] = values[source]
    return out


def _advect_labels(
    grid: CubedSphere,
    plate_model: PlateModel,
    labels: np.ndarray,
    dt_ma: float,
) -> np.ndarray:
    return _advect_scalar(grid, plate_model, labels.astype(np.float64), dt_ma).astype(
        np.int32
    )


def _add_edge_intensity(
    target: np.ndarray,
    edges: np.ndarray,
    edge_mask: np.ndarray,
    values: np.ndarray | float,
) -> None:
    chosen = edges[edge_mask]
    if len(chosen) == 0:
        return
    if np.isscalar(values):
        amount = np.full(len(chosen), float(values))
    else:
        amount = np.asarray(values)[edge_mask]
    np.add.at(target, chosen[:, 0], amount)
    np.add.at(target, chosen[:, 1], amount)


def _continental_fraction(thickness_km: np.ndarray) -> np.ndarray:
    return _smoothstep(CONTINENT_MIN_KM - 2.0, CONTINENT_CORE_KM, thickness_km)


def _apply_crust_events(
    thickness: np.ndarray,
    continent_id: np.ndarray,
    basement_age: np.ndarray,
    current: dict[str, np.ndarray],
    grid: CubedSphere,
    dt_ma: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    thickness = thickness.copy()
    continent_id = continent_id.copy()
    basement_age = basement_age.copy()

    collision = current["collision"]
    arc = current["arc"]
    rift = current["continental_rift"]
    suture = current["suture"]
    transform = current["transform"]

    # Growth must outpace boundary attrition over long runs or continents vanish.
    thickness += (3.6 * collision + 2.4 * arc + 0.8 * suture) * dt_ma
    thickness -= (0.85 * rift + 0.12 * transform) * dt_ma

    continental = _continental_fraction(thickness)
    # Stable interiors slowly relax toward typical continental thickness.
    interior = continental > 0.55
    thickness[interior] += 0.22 * (CONTINENT_CORE_KM - thickness[interior]) * (
        dt_ma / 8.0
    )

    # Margin-local noise so coasts gain embayments instead of smooth isolines.
    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    neighbor_cont = np.where(valid, continental[safe], 0.0).sum(axis=1) / np.maximum(
        valid.sum(axis=1), 1
    )
    margin = (continental > 0.15) & (continental < 0.85) & (neighbor_cont < continental)
    jitter = grid.smooth(rng.normal(size=grid.size), iterations=2)
    thickness += 0.45 * jitter * margin.astype(float) * dt_ma / 8.0

    # Hysteresis oceanization: avoid flickering coastlines.
    oceanize = thickness < (CONTINENT_MIN_KM - 3.0)
    reclaim = (thickness >= CONTINENT_MIN_KM) & (continent_id < 0)
    thickness[oceanize] = OCEAN_THICKNESS_KM + 1.5 * current["ridge"][oceanize]
    continent_id[oceanize] = -1
    basement_age[oceanize] = 0.0
    if np.any(reclaim):
        for cell in np.flatnonzero(reclaim):
            neigh = grid.neighbors[cell]
            neigh = neigh[neigh >= 0]
            ids = continent_id[neigh]
            ids = ids[ids >= 0]
            if len(ids):
                continent_id[cell] = int(ids[0])
                basement_age[cell] = max(float(basement_age[cell]), 250.0)

    # Weld only the boundary cells themselves — do not flood-merge whole continents
    # into a single global id (that collapsed lineage counts to 1).
    edges = grid.edge_cells
    if len(edges):
        left = edges[:, 0]
        right = edges[:, 1]
        weld = (
            (suture[left] + suture[right] > 0.08)
            & (continent_id[left] >= 0)
            & (continent_id[right] >= 0)
        )
        for a, b in edges[weld]:
            keep = min(int(continent_id[a]), int(continent_id[b]))
            continent_id[a] = keep
            continent_id[b] = keep

    # New crust at arcs inherits nearby continental lineage.
    growing = (arc > 0.08) & (continent_id < 0) & (thickness >= CONTINENT_MIN_KM)
    if np.any(growing):
        for cell in np.flatnonzero(growing):
            neigh = grid.neighbors[cell]
            neigh = neigh[neigh >= 0]
            ids = continent_id[neigh]
            ids = ids[ids >= 0]
            if len(ids):
                continent_id[cell] = int(ids[0])
                basement_age[cell] = max(float(basement_age[cell]), 200.0)

    thickness = np.clip(thickness, OCEAN_THICKNESS_KM, 72.0)
    return thickness, continent_id, basement_age


def simulate_geology(
    grid: CubedSphere, config: GeologyConfig
) -> tuple[GeologyFields, PlateModel]:
    rng = np.random.default_rng(config.seed)
    plates = PlateModel.initialize(grid, config.n_plates, config.seed)
    thickness, continent_id, basement_age = _seed_crust_fields(
        grid, plates, config, rng
    )
    seafloor_age = np.where(
        continent_id < 0,
        rng.uniform(5.0, 80.0, size=grid.size),
        0.0,
    )
    cumulative = {name: np.zeros(grid.size, dtype=np.float64) for name in EVENT_NAMES}
    memory = {name: np.zeros(grid.size, dtype=np.float64) for name in EVENT_NAMES}
    decay_ma = {
        "ridge": 30.0,
        "continental_rift": 180.0,
        "subduction": 100.0,
        "arc": 140.0,
        "collision": 280.0,
        "suture": 450.0,
        "transform": 50.0,
        "passive_margin": 350.0,
        "hydrothermal": 180.0,
        "mafic": 500.0,
        "alkaline": 600.0,
        "exhumation": 250.0,
    }

    for _ in range(config.ticks):
        continental = _continental_fraction(thickness)
        boundary = plates.boundaries(grid)
        edges = boundary.edge_cells
        current = {name: np.zeros(grid.size, dtype=np.float64) for name in EVENT_NAMES}
        if len(edges):
            cont_left = continental[edges[:, 0]] > 0.28
            cont_right = continental[edges[:, 1]] > 0.28
            both_cont = cont_left & cont_right
            one_cont = cont_left ^ cont_right
            both_ocean = (~cont_left) & (~cont_right)
            divergent = boundary.kind == BOUNDARY_DIVERGENT
            convergent = boundary.kind == BOUNDARY_CONVERGENT
            transform = boundary.kind == BOUNDARY_TRANSFORM
            speed = np.clip(
                (np.abs(boundary.opening_km_ma) + 0.35 * np.abs(boundary.shear_km_ma))
                / 35.0,
                0.05,
                1.5,
            )

            _add_edge_intensity(current["ridge"], edges, divergent & both_ocean, speed)
            _add_edge_intensity(
                current["continental_rift"], edges, divergent & (~both_ocean), speed
            )
            _add_edge_intensity(
                current["subduction"], edges, convergent & (~both_cont), speed
            )
            _add_edge_intensity(current["arc"], edges, convergent & one_cont, speed)
            _add_edge_intensity(
                current["collision"], edges, convergent & both_cont, speed
            )
            _add_edge_intensity(current["suture"], edges, convergent & both_cont, speed)
            _add_edge_intensity(current["transform"], edges, transform, speed)
            _add_edge_intensity(
                current["hydrothermal"],
                edges,
                (convergent & one_cont) | transform,
                speed * 0.7,
            )
            _add_edge_intensity(
                current["mafic"],
                edges,
                divergent | (convergent & both_ocean),
                speed * 0.5,
            )

            for name in EVENT_NAMES:
                memory[name] *= np.exp(-config.dt_ma / decay_ma[name])
                memory[name] += current[name]
                cumulative[name] += current[name] * config.dt_ma

        thickness, continent_id, basement_age = _apply_crust_events(
            thickness,
            continent_id,
            basement_age,
            current,
            grid,
            config.dt_ma,
            rng,
        )
        continental = _continental_fraction(thickness)
        seafloor_age = advance_seafloor_age(
            seafloor_age, continental, current["ridge"], config.dt_ma
        )
        thickness = _advect_scalar(grid, plates, thickness, config.dt_ma)
        basement_age = _advect_scalar(grid, plates, basement_age, config.dt_ma)
        seafloor_age = _advect_scalar(grid, plates, seafloor_age, config.dt_ma)
        continent_id = _advect_labels(grid, plates, continent_id, config.dt_ma)
        # Heal remesh speckles from nearest-neighbor advection.
        thickness = grid.smooth(thickness, iterations=1, self_weight=4.0)
        continent_id[thickness < CONTINENT_MIN_KM] = -1
        seafloor_age[continent_id >= 0] = 0.0
        plates.advance(grid, config.dt_ma)

    continental = _continental_fraction(thickness)
    for name in EVENT_NAMES:
        memory[name] = grid.smooth(memory[name], iterations=3)
        maximum = float(memory[name].max())
        if maximum > 1e-12:
            memory[name] /= maximum
        cumulative_max = float(cumulative[name].max())
        if cumulative_max > 1e-12:
            cumulative[name] /= cumulative_max

    valid = grid.neighbors >= 0
    safe = np.where(valid, grid.neighbors, 0)
    cont_neighbor = np.where(valid, continental[safe], 0.0).mean(axis=1)
    margin = (
        (continental > 0.22)
        & (continental < 0.82)
        & (cont_neighbor < continental)
        & (memory["collision"] < 0.2)
        & (memory["arc"] < 0.2)
    )
    memory["passive_margin"] = grid.smooth(margin.astype(float), 3)
    cumulative["passive_margin"] = memory["passive_margin"].copy()

    alkaline_noise = grid.smooth(rng.random(grid.size), iterations=8)
    alkaline_noise = np.clip(
        (alkaline_noise - np.percentile(alkaline_noise, 85))
        / max(np.ptp(alkaline_noise), 1e-9)
        * 5.0,
        0,
        1,
    )
    memory["alkaline"] = alkaline_noise * (0.3 + 0.7 * continental)
    cumulative["alkaline"] = memory["alkaline"].copy()
    memory["exhumation"] = np.clip(
        0.6 * memory["collision"] + 0.5 * memory["arc"], 0, 1
    )
    cumulative["exhumation"] = memory["exhumation"].copy()

    texture = grid.smooth(rng.normal(size=grid.size), iterations=5)
    texture /= max(float(np.std(texture)), 1e-9)
    # Soften the continental mask used for elevation so coasts are not cliffs.
    continental_soft = grid.smooth(continental, iterations=2, self_weight=2.5)
    continental_soft = np.minimum(continental_soft, continental + 0.22)
    coastal_noise = grid.smooth(rng.normal(size=grid.size), iterations=2)
    continental_soft = np.clip(
        continental_soft + 0.05 * coastal_noise * memory["passive_margin"], 0.0, 1.0
    )

    ridge = memory["ridge"]
    ocean_age = seafloor_age.copy()
    ocean_age[continental > 0.25] = 0.0
    # Fill any remaining oceanic zeros with a soft fallback so brand-new cells
    # still get a depth.
    need_age = (continental <= 0.25) & (ocean_age <= 0.0)
    ocean_age[need_age] = np.clip(
        40.0 * (1.0 - 0.85 * ridge[need_age]) + 10.0, 0.0, 180.0
    )
    crust_age = np.where(continental > 0.25, basement_age, ocean_age)
    crust_thickness = np.where(
        continental > 0.25,
        thickness,
        OCEAN_THICKNESS_KM + 2.0 * ridge,
    )

    orogeny = np.clip(
        0.85 * memory["collision"]
        + 0.65 * memory["suture"]
        + 0.5 * memory["arc"],
        0,
        1.5,
    )
    basin_depth = np.clip(
        0.65 * memory["continental_rift"]
        + 0.5 * memory["passive_margin"]
        + 0.25 * grid.smooth(memory["collision"], 2),
        0,
        1,
    )
    sediment = np.clip(
        0.65 * basin_depth + 0.25 * (continental > 0.2) * (orogeny < 0.25),
        0,
        1,
    )

    ocean_elevation, seafloor_extras = build_seafloor_elevation(
        grid, ocean_age, continental_soft, memory, seed=config.seed
    )
    memory["trench"] = seafloor_extras["trench"]
    memory["back_arc"] = seafloor_extras["back_arc"]
    continental_elevation = (
        40.0
        + 48.0 * (crust_thickness - OCEAN_THICKNESS_KM)
        + 3000.0 * orogeny
        - 850.0 * basin_depth
        + 140.0 * texture
    )
    transition = _smoothstep(0.18, 0.58, continental_soft)
    elevation = ocean_elevation * (1.0 - transition) + continental_elevation * transition
    elevation = apply_variable_shelves(
        elevation, continental_soft, continental, memory, grid
    )
    continental = continental_soft

    ancient = np.clip((crust_age - 1200.0) / 1800.0, 0, 1) * continental
    felsic = np.clip(0.45 * continental + 0.45 * memory["collision"], 0, 1)
    mafic = np.clip(0.65 * memory["mafic"] + 0.25 * memory["arc"], 0, 1)
    carbonate = np.clip(0.7 * sediment * (1.0 - memory["arc"]), 0, 1)
    organic_shale = np.clip(0.7 * sediment * (1.0 - orogeny), 0, 1)
    sandstone = np.clip(0.75 * sediment + 0.2 * memory["continental_rift"], 0, 1)
    evaporite = np.clip(0.65 * basin_depth * (1.0 - memory["arc"]), 0, 1)
    quartz = np.clip(0.5 * ancient + 0.35 * felsic + 0.2 * memory["hydrothermal"], 0, 1)
    ultramafic = np.clip(0.7 * mafic * (0.4 + memory["suture"]), 0, 1)

    latitude = np.abs(grid.lat_deg)
    paleowet = np.clip(
        (1.0 - latitude / 75.0) * sediment * (0.7 + 0.3 * texture), 0, 1
    )
    paleoarid = np.clip(
        np.exp(-((latitude - 25.0) / 13.0) ** 2) * basin_depth, 0, 1
    )
    tropical_weathering = np.clip(
        (1.0 - latitude / 35.0) * continental * (1.0 - orogeny), 0, 1
    )

    lithology = {
        "ancient_craton": ancient,
        "felsic": felsic,
        "mafic": mafic,
        "ultramafic": ultramafic,
        "carbonate": carbonate,
        "organic_shale": organic_shale,
        "sandstone": sandstone,
        "evaporite": evaporite,
        "quartz": quartz,
        "heavy_mineral_source": np.clip(0.5 * mafic + 0.4 * felsic, 0, 1),
    }
    paleoclimate = {
        "wetland": paleowet,
        "aridity": paleoarid,
        "tropical_weathering": tropical_weathering,
        "upwelling": np.clip(memory["passive_margin"] * 0.7, 0, 1),
    }
    return (
        GeologyFields(
            plate_id=plates.plate_id.copy(),
            continent_id=continent_id,
            terrane_id=continent_id.copy(),
            continental=continental,
            crust_age_ma=crust_age,
            crust_thickness_km=crust_thickness,
            elevation_m=elevation,
            orogeny=orogeny,
            basin_depth=basin_depth,
            sediment=sediment,
            history=memory,
            lithology=lithology,
            paleoclimate=paleoclimate,
            seafloor_age_ma=ocean_age,
        ),
        plates,
    )
