# Nested morphology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise the generator from ~144 km cells to a nested 4.5 km global / 100 m local ladder, add the surface-process systems needed for Earth-like geography, then re-anchor Veldara canon to the generated world.

**Spec:** [`../specs/2026-07-24-nested-morphology-design.md`](../specs/2026-07-24-nested-morphology-design.md)

**Architecture:** Five tiers (T0 tectonics ~35 km → T1 global surface ~4.5 km → T2 continent 1 km → T3 national board 250 m → T4 operational windows 100 m). Each tier checkpoints to disk. Sub-T1 detail is deterministic process-based downscaling, not simulation.

**Tech Stack:** Python 3 + NumPy (generator), MapLibre GL + Vite (viewer), unittest.

## Global Constraints

- No magic; fictional geography; real physics metaphors.
- v2 only; v1 legacy untouched.
- No land-fraction target. Sea level fixed: 0 m present, −120 m LGM.
- Seed + generator version ⇒ byte-identical output.
- Build host is 4 vCPU / 15 GB RAM / 230 GB disk. Memory budgets in the spec are hard limits; use disk-backed arrays rather than exceeding them.
- Where canon and generated geography disagree, generated output wins.
- Branch: `cursor/fantasy-military-repo-c216`.

---

### Task 1: Field contract, versioning, checkpoints

**Files:**
- Create: `maps/generator/deeptime/v2/contract.py`
- Create: `maps/generator/deeptime/v2/checkpoint.py`
- Modify: `maps/generator/deeptime/v2/model.py`
- Create: `maps/generator/tests/test_v2_contract.py`

- [ ] Declare the field set each downstream consumer (`resources.py`, `export.py`) reads, with dtype and units.
- [ ] Add `GENERATOR_VERSION`; stamp seed + version into `meta` for every artifact.
- [ ] Implement save/load of per-tier checkpoints keyed by `(seed, version, tier)`.
- [ ] Test: same seed twice ⇒ identical bytes; resuming a tier skips prior tiers.
- [ ] Commit.

### Task 2: Scale T0/T1

**Files:**
- Modify: `maps/generator/deeptime/v2/grid.py`, `geology.py`, `model.py`
- Create: `maps/generator/tests/test_v2_scale.py`

- [ ] Make `grid_n` viable at 256 (T0) and 2048 (T1); profile and remove per-cell Python loops.
- [ ] Run tectonics at T0, then interpolate crust fields onto T1 once.
- [ ] Keep peak RSS under budget; switch to `memmap` where a field exceeds it.
- [ ] Test: T1 builds within the memory ceiling; T0→T1 interpolation conserves land mask area within tolerance.
- [ ] Commit.

### Task 3: Ocean floor and global relief

**Files:**
- Modify: `maps/generator/deeptime/v2/geology.py`
- Create: `maps/generator/deeptime/v2/seafloor.py`

- [ ] Build bathymetry from seafloor age (ridge → abyssal plain subsidence), not a flat ocean default.
- [ ] Add trenches at convergent boundaries, back-arc basins, hotspot swells, fracture zones.
- [ ] Variable shelf width from margin type (passive wide, active narrow).
- [ ] Test: age–depth relation is monotonic; trenches deeper than adjacent abyssal plain.
- [ ] Commit.

### Task 4: Climate and ocean circulation

**Files:**
- Modify: `maps/generator/deeptime/v2/climate.py`
- Create: `maps/generator/tests/test_v2_climate_bands.py`

- [ ] Zonal circulation with orographic uplift and explicit rain shadow behind linear ranges.
- [ ] Simplified gyre / boundary-current transport for coastal temperature asymmetry.
- [ ] Continentality and monsoon response to land distribution.
- [ ] Test: windward wetter than leeward across a ridge fixture; west/east coast temperature asymmetry has the right sign.
- [ ] Commit.

### Task 5: Erosion, lakes, glaciation

**Files:**
- Create: `maps/generator/deeptime/v2/surface.py`
- Create: `maps/generator/tests/test_v2_drainage.py`

- [ ] Iterative stream-power erosion + hillslope diffusion + sediment deposition to convergence.
- [ ] Flow routing with depression filling that **keeps** lakes rather than removing them; endorheic basins where outflow < evaporation.
- [ ] Glacial erosion: U-valleys, cirques, fjords on high-relief coasts; present-day polar ice caps included in the sea-level budget.
- [ ] Canyon incision where uplift races base-level fall; deltas at river mouths.
- [ ] Test: drainage is acyclic and reaches base level; lakes survive routing; bearing histogram has no D8 spike.
- [ ] Commit.

### Task 6: Coasts and reefs

**Files:**
- Create: `maps/generator/deeptime/v2/coastal.py`

- [ ] Wave-driven erosion and longshore drift: spits, barriers, ria and fjord coasts, peninsulas.
- [ ] Reef growth tracking sea level: fringing → barrier → atoll over subsiding volcanic edifices.
- [ ] Volcanic arcs as discrete edifices; hotspot chains with age progression.
- [ ] Test: atolls only over subsided edifices in warm shallow water; reef belt respects the temperature limit.
- [ ] Commit.

### Task 7: Seed search and canon scoring

**Files:**
- Create: `maps/generator/deeptime/v2/anchor.py`
- Create: `maps/generator/tests/test_v2_anchor.py`

- [ ] Encode the seven canon constraints from the spec as a scoring function over T1 output.
- [ ] Sweep seeds at T0/T1, rank, and promote the best; record the promoted seed in canon.
- [ ] Test: scoring rejects a world with an orogenic wall across Eastmarch and accepts one with an open plain.
- [ ] Commit.

### Task 8: Nested refinement T2–T4

**Files:**
- Create: `maps/generator/deeptime/v2/refine.py`

- [ ] Window extraction with overlap; refine relief conditioned on coarse slope, lithology, climate and base level.
- [ ] Re-run erosion, coastal and reef steps within each window at that tier's resolution.
- [ ] Tile T3/T4 through disk so memory stays bounded.
- [ ] Test: refined tier agrees with its parent at the shared scale; window seams are continuous.
- [ ] Commit.

### Task 9: Features, names, navigability

**Files:**
- Create: `maps/generator/deeptime/v2/features.py`
- Modify: `maps/generator/deeptime/v2/export.py`

- [ ] Extract seas, gulfs, straits, lakes, ranges, passes, rivers, deltas, island groups, reefs with stable IDs.
- [ ] Assign persistent names so canon references survive regeneration.
- [ ] Derive navigability: channel depth/width, chokepoint geometry, harbour rating, shelf break, coarse tidal-range proxy.
- [ ] Test: IDs and names stable across two runs of the same seed.
- [ ] Commit.

### Task 10: Sparse tiles and viewer

**Files:**
- Modify: `maps/generator/deeptime/v2/tiles.py`, `export.py`
- Modify: `maps/viewer/src/main.js`, `maps/viewer/README.md`

- [ ] Move `max_zoom` literals out of `export.py` (lines 364, 383) into config.
- [ ] Global pyramid z0–z6; deep pyramid z7–z11 over Aurelian and the Veldara board only.
- [ ] Viewer `maxzoom` follows the deep pyramid; overzoom falls back to parent tiles.
- [ ] Add feature and navigability overlays.
- [ ] Commit.

### Task 11: Validation suite

**Files:**
- Create: `maps/generator/tests/test_v2_morphology_validation.py`

- [ ] Assert T1 resolves a ≤ 20 km strait, an enclosed sea, a great lake, an ≥ 8-island archipelago.
- [ ] Cubed-sphere seam continuity on elevation and drainage.
- [ ] Polar distortion within stated tolerance.
- [ ] Coastline fractal dimension in Earth's observed band; land fraction reported not clamped.
- [ ] LGM re-derived from new bedrock with plausible land gain.
- [ ] Commit.

### Task 12: Re-anchor canon

**Files:**
- Modify: `world/00`–`world/13`, `maps/00-world-map-brief.md`, `maps/01-country-maps-brief.md`
- Modify: `threat-analysis/`, `doctrine/`, `episodes/` where geography is cited
- Modify: `decisions-log.md` (new decision superseding D-0027 on resolution)

- [ ] Rewrite Aurelian, Veldara, Highspine, Eastmarch, Farreach, Twin Harbors, Solmar, Doverin, Sereth descriptions to match the promoted world.
- [ ] Record promoted seed + generator version as canon.
- [ ] Verify every geographic claim resolves to an extracted feature.
- [ ] Commit.

### Task 13: Regenerate and ship

- [ ] Full run: promoted seed, present + LGM, all tiers.
- [ ] Regenerate `maps/exports/*` and `maps/viewer/public/world/*`; commit artifacts.
- [ ] Update `maps/generator/README.md` with the tier table and runtime expectations.
- [ ] Push; update PR.
