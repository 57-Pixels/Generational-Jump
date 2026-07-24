# World Generator v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the artifact-prone raster-advection prototype with a tested spherical geology → climate/hydrology → resources → settlement pipeline.

**Architecture:** Simulation uses a cubed-sphere grid, rigid plate Euler rotations, spherical Voronoi plate labels, signed boundary kinematics, separate crust/terrane/landmass identities, and persistent geologic event fields. Surface and human layers consume those outputs without mutating geology. Equirectangular data exists only as an export/view format.

**Tech Stack:** Python 3.12, NumPy, Pillow, standard-library `unittest`, MapLibre/Vite viewer.

## Global Constraints

- No magic; Earthlike physics and approximately 29% present land.
- Plate, continental crust/terrane, continent lineage, and landmass are separate concepts.
- Same seed is reproducible.
- Geological resources are earned from event/lithology/basin history.
- Physical habitability is separate from settlement incentives.
- A/C uplift requires grid reliability, capital, and energy headroom and reports energy/water burdens.
- Incentives can produce settlements in marginal terrain; impossible cells remain impossible.
- Imports remain at module tops.

---

### Task 1: Spherical grid and rigid plate kinematics

**Files:**
- Create: `maps/generator/deeptime/v2/grid.py`
- Create: `maps/generator/deeptime/v2/plates.py`
- Test: `maps/generator/tests/test_v2_plates.py`

**Interfaces:**
- Produces `CubedSphere`, `PlateModel`, `BoundaryFields`.
- All downstream rasters are flat arrays over `CubedSphere.xyz`.

- [ ] Write failing tests for total spherical area, reciprocal neighbors, Rodrigues distance preservation, connected Voronoi plates, and signed convergence/divergence/shear.
- [ ] Run `PYTHONPATH=maps/generator python3 -m unittest maps.generator.tests.test_v2_plates -v`; confirm failures are missing APIs.
- [ ] Implement cubed-sphere coordinates/areas/neighbors and Euler-pole rigid velocities.
- [ ] Recompute plate IDs from spherical Voronoi generators each tick; never advect IDs.
- [ ] Implement signed edge opening/shear and boundary classification.
- [ ] Run tests and commit.

### Task 2: Crust, continents, landmasses, and history

**Files:**
- Create: `maps/generator/deeptime/v2/geology.py`
- Create: `maps/generator/deeptime/v2/topology.py`
- Test: `maps/generator/tests/test_v2_geology.py`

**Interfaces:**
- Consumes `CubedSphere`, `PlateModel`, `BoundaryFields`.
- Produces `GeologyFields` with crust kind/age/thickness, terrane/continent IDs, elevation metres, basin/sediment fields, event history, and landmass IDs.

- [ ] Write failing tests that plate IDs remain connected, continent IDs survive plate ownership changes, continental collision never silently deletes continental crust, event memory decays, and one landmass may contain multiple continent IDs.
- [ ] Implement compact spherical cratons independent of plate labels.
- [ ] Implement ridge/rift/subduction/collision/transform/passive-margin event accumulation.
- [ ] Derive elevation from crust type/age/thickness plus event memory.
- [ ] Fit present water inventory once to 29% land; LGM reuses bedrock with a 120 m sea-level drop.
- [ ] Run tests and commit.

### Task 3: Climate, hydrology, and environment

**Files:**
- Create: `maps/generator/deeptime/v2/climate.py`
- Create: `maps/generator/deeptime/v2/hydrology.py`
- Create: `maps/generator/deeptime/v2/environment.py`
- Test: `maps/generator/tests/test_v2_surface.py`

**Interfaces:**
- Produces temperature/precipitation/winds/continentality/monsoon/snow/sea ice; receivers/drainage/discharge/rivers/lakes/deltas; fertility/aquifers/fisheries/harbors/passes.

- [ ] Write failing synthetic tests for latitude/elevation temperature, windward/lee rainfall, no blanket land-wet bonus, no white polar-ocean bar, bowl drainage, receiver acyclicity, floodplain fertility, shelf fisheries, enclosed harbors, and saddle passes.
- [ ] Implement seasonal climate and directional moisture transport.
- [ ] Implement priority-flood drainage, D8 receivers, accumulation, rivers/lakes/deltas.
- [ ] Implement environment scores from explainable components.
- [ ] Run tests and commit.

### Task 4: Resource provinces

**Files:**
- Create: `maps/generator/deeptime/v2/resources.py`
- Test: `maps/generator/tests/test_v2_resources.py`
- Modify: `world/13-resources-from-geology.md`

**Interfaces:**
- Consumes geologic history/lithology/basins/paleoclimate/accessibility.
- Produces variable-count deposit provinces and bulk-material availability rasters.

- [ ] Write failing tests for zero-host → zero deposits, nonuniform counts, arc requirement for porphyry, basin requirements for petroleum/potash/lithium brine, HP quartz rarity, deterministic grade/tonnage/depth, reserve ≤ resource, and byproducts.
- [ ] Implement strategic deposit classes, correlated prospect fields, area-scaled variable counts, and property generation.
- [ ] Keep aggregate/sand/limestone/clay/salt/gypsum as availability rasters.
- [ ] Export grade, tonnage, depth, accessibility, processing, reserve, byproducts.
- [ ] Run tests and commit.

### Task 5: Era habitability and incentive-driven settlement

**Files:**
- Create: `maps/generator/deeptime/v2/settlement.py`
- Test: `maps/generator/tests/test_v2_settlement.py`
- Modify: `world/12-worldbuilding-principles.md`

**Interfaces:**
- Produces `h_pre`, `h_ind`, `h_ac`, incentive components, no-incentive counterfactual, attraction, support capacity, mechanism, A/C demand and servicing burdens.

- [ ] Write failing tests for no-grid/no-A/C uplift, hot/humid uplift with infrastructure, no temperate bonus, demand accompanying uplift, incentives not changing habitability, incentive-driven marginal settlement, and hard gates.
- [ ] Implement weighted-geometric physical habitability.
- [ ] Implement A/C feasibility and energy/water demand.
- [ ] Implement resource/trade/strategy/policy/institutional incentive channels separately.
- [ ] Implement settlement attraction and mechanism classification.
- [ ] Run tests and commit.

### Task 6: Pipeline, exports, and viewer

**Files:**
- Create: `maps/generator/deeptime/v2/model.py`
- Create: `maps/generator/deeptime/v2/export.py`
- Modify: `maps/generator/deeptime/__main__.py`
- Modify: `maps/viewer/src/main.js`
- Modify: `maps/viewer/index.html`
- Test: `maps/generator/tests/test_v2_pipeline.py`

**Interfaces:**
- `python3 -m deeptime --engine v2 --seed 42`.
- Writes equirectangular atlas, plates/continents/landmasses, climate, rivers/lakes, resources, settlement layers, GeoJSON, and meta.

- [ ] Write failing deterministic pipeline/export tests.
- [ ] Orchestrate v2 layers and reproject cubed-sphere fields for export.
- [ ] Add layer toggles/popups to viewer.
- [ ] Keep `--engine v1` for explicit legacy comparison only.
- [ ] Run Python tests and `npm run build`; commit.

### Task 7: Multi-seed and visual validation

**Files:**
- Create: `maps/generator/tests/test_v2_ensemble.py`
- Modify: `maps/generator/README.md`
- Modify: `decisions-log.md`

- [ ] Test at least five reduced-resolution seeds for connected plates, finite fields, nontrivial landmass distribution, varied resource counts, present land 0.26–0.32, LGM below 0.36, and deterministic repeat.
- [ ] Generate reference seed 42 at production resolution.
- [ ] Inspect atlas, plates, climate, rivers, resources, and settlement outputs.
- [ ] Update docs and decisions with model limits; do not label v2 mantle CFD.
- [ ] Run complete verification, commit, push, and update PR.
