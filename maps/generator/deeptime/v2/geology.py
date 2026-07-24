"""Deep-time crust, terranes, geologic events, and bedrock relief."""

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


def _smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    t = np.clip((values - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


@dataclass(frozen=True)
class GeologyConfig:
    seed: int = 42
    ticks: int = 80
    dt_ma: float = 8.0
    n_plates: int = 12
    n_continents: int = 7


@dataclass
class TerraneModel:
    centers: np.ndarray
    radii_rad: np.ndarray
    continent_id: np.ndarray
    attached_plate: np.ndarray
    basement_age_ma: np.ndarray

    def rotate(self, plate_model: PlateModel, dt_ma: float) -> None:
        for plate in np.unique(self.attached_plate):
            mask = self.attached_plate == plate
            omega = plate_model.omega_xyz[int(plate)]
            rate = float(np.linalg.norm(omega))
            self.centers[mask] = rodrigues_rotate(
                self.centers[mask], omega, rate * dt_ma
            )

    def rasterize(
        self, grid: CubedSphere
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n_continents = int(self.continent_id.max()) + 1
        scores = np.zeros((n_continents, grid.size), dtype=np.float64)
        age = np.zeros(grid.size, dtype=np.float64)
        for index, center in enumerate(self.centers):
            angular = np.arccos(np.clip(grid.xyz @ center, -1.0, 1.0))
            radius = self.radii_rad[index]
            lobe = 1.0 - _smoothstep(radius * 0.72, radius, angular)
            cid = int(self.continent_id[index])
            scores[cid] = np.maximum(scores[cid], lobe)
            age = np.maximum(age, lobe * self.basement_age_ma[index])
        continent_id = np.argmax(scores, axis=0).astype(np.int32)
        continental = np.max(scores, axis=0)
        continent_id[continental < 0.18] = -1
        return continental, continent_id, age


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


def _initialize_terranes(
    plate_model: PlateModel, config: GeologyConfig, rng: np.random.Generator
) -> TerraneModel:
    centers: list[np.ndarray] = []
    radii: list[float] = []
    continent_ids: list[int] = []
    attached: list[int] = []
    ages: list[float] = []
    n_plates = len(plate_model.seed_xyz)
    selected_plates = rng.choice(
        n_plates, size=min(config.n_continents, n_plates), replace=False
    )
    for continent, plate in enumerate(selected_plates):
        main = plate_model.seed_xyz[int(plate)]
        age = float(rng.uniform(900.0, 3500.0))
        lobe_count = int(rng.integers(3, 7))
        for lobe in range(lobe_count):
            if lobe == 0:
                center = main.copy()
            else:
                axis = np.cross(main, rng.normal(size=3))
                if np.linalg.norm(axis) < 1e-8:
                    axis = np.cross(main, np.array([0.0, 0.0, 1.0]))
                center = rodrigues_rotate(
                    main[None, :], axis, float(rng.uniform(0.08, 0.38))
                )[0]
            centers.append(center)
            radii.append(float(rng.uniform(0.22, 0.48)))
            continent_ids.append(continent)
            attached.append(int(plate))
            ages.append(age + float(rng.uniform(-150.0, 150.0)))
    return TerraneModel(
        centers=np.asarray(centers),
        radii_rad=np.asarray(radii),
        continent_id=np.asarray(continent_ids, dtype=np.int32),
        attached_plate=np.asarray(attached, dtype=np.int32),
        basement_age_ma=np.asarray(ages),
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


def simulate_geology(
    grid: CubedSphere, config: GeologyConfig
) -> tuple[GeologyFields, PlateModel]:
    rng = np.random.default_rng(config.seed)
    plates = PlateModel.initialize(grid, config.n_plates, config.seed)
    terranes = _initialize_terranes(plates, config, rng)
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

    continental = np.zeros(grid.size)
    continent_id = np.full(grid.size, -1, dtype=np.int32)
    basement_age = np.zeros(grid.size)
    for _ in range(config.ticks):
        continental, continent_id, basement_age = terranes.rasterize(grid)
        boundary = plates.boundaries(grid)
        edges = boundary.edge_cells
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

            current = {name: np.zeros(grid.size, dtype=np.float64) for name in EVENT_NAMES}
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
                current["mafic"], edges, divergent | (convergent & both_ocean), speed * 0.5
            )

            for name in EVENT_NAMES:
                memory[name] *= np.exp(-config.dt_ma / decay_ma[name])
                memory[name] += current[name]
                cumulative[name] += current[name] * config.dt_ma

        terranes.rotate(plates, config.dt_ma)
        plates.advance(grid, config.dt_ma)

    continental, continent_id, basement_age = terranes.rasterize(grid)
    for name in EVENT_NAMES:
        memory[name] = grid.smooth(memory[name], iterations=3)
        maximum = float(memory[name].max())
        if maximum > 1e-12:
            memory[name] /= maximum
        cumulative_max = float(cumulative[name].max())
        if cumulative_max > 1e-12:
            cumulative[name] /= cumulative_max

    # Quiet continental/ocean transition after long rifting becomes passive margin.
    cont_neighbor = np.zeros(grid.size)
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

    # Seed rare alkaline/hotspot provinces independently of current boundaries,
    # but keep them spatially coherent and deterministic.
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
    ridge = memory["ridge"]
    ocean_age = np.clip(
        180.0 * (1.0 - 0.85 * ridge) + 20.0 * (texture + 1.0), 0.0, 220.0
    )
    crust_age = np.where(continental > 0.25, basement_age, ocean_age)
    crust_thickness = np.where(
        continental > 0.25,
        28.0 + 14.0 * continental + 18.0 * memory["collision"],
        6.0 + 2.0 * ridge,
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

    ocean_elevation = -2600.0 - 250.0 * np.sqrt(np.clip(ocean_age, 0, 180))
    continental_elevation = (
        180.0
        + 550.0 * continental
        + 3600.0 * orogeny
        - 900.0 * basin_depth
        + 180.0 * texture
    )
    transition = _smoothstep(0.16, 0.48, continental)
    elevation = ocean_elevation * (1.0 - transition) + continental_elevation * transition
    elevation += 450.0 * ridge * (1.0 - transition)

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
        ),
        plates,
    )
