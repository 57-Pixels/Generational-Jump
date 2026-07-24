# Crust-field morphology Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace circular terrane caps with event-driven crust thickness evolution, drop the 29% land clamp, fix globe polar display, and render irregular deposit/settlement footprints.

**Architecture:** Eulerian crust fields on the cubed-sphere advect with rigid plates, update from signed boundaries, then feed the existing elevation → climate → resources → settlement stack. Viewer maps the atlas to ±90° and draws polygons instead of circles.

**Tech Stack:** Python 3 + NumPy (generator), MapLibre GL + Vite (viewer), unittest.

## Global Constraints

- No magic; fictional geography; real physics metaphors.
- v2 only; v1 legacy untouched except docs clarity.
- No post-hoc land-fraction fitting in v2.
- Present sea level fixed at 0 m on the elevation field; LGM = −120 m.
- Keep resource catalog / settlement contracts unless geometry export changes.
- Branch: `cursor/fantasy-military-repo-c216`.

---

### Task 1: Failing morphology + land tests

**Files:**
- Modify: `maps/generator/tests/test_v2_pipeline.py`
- Modify: `maps/generator/tests/test_v2_ensemble.py`
- Create: `maps/generator/tests/test_v2_crust_morphology.py`

- [ ] Remove 0.26–0.32 land assertions; assert land ∈ (0.05, 0.85) and LGM ≥ present.
- [ ] Add test: anisotropic init / post-sim landmask mean isoperimetric quotient below a circular-cap baseline, or aspect ratio spread is high.
- [ ] Add test: rift thins crust; collision thickens in a two-plate fixture.
- [ ] Run tests; confirm new expectations fail on current code where appropriate.
- [ ] Commit.

### Task 2: Crust-field geology

**Files:**
- Modify: `maps/generator/deeptime/v2/geology.py`
- Modify: `maps/generator/deeptime/v2/model.py`
- Modify: `maps/generator/README.md`
- Modify: `decisions-log.md` (D-0027)

- [ ] Replace `TerraneModel` circular rasterize with thickness/age/id fields + anisotropic init.
- [ ] Implement backward remesh advection per plate Euler step.
- [ ] Apply collision/arc/rift/transform/passive-margin thickness updates each tick.
- [ ] Derive `continental`, elevation, lithology as today but from thickness.
- [ ] Remove `target_land_fraction` usage; `sea_level_m = 0` present / `-120` LGM.
- [ ] Run `test_v2_*.py`; fix until green.
- [ ] Commit.

### Task 3: Irregular markers

**Files:**
- Modify: `maps/generator/deeptime/v2/resources.py` (footprint helper if needed)
- Modify: `maps/generator/deeptime/v2/export.py`
- Modify: `maps/viewer/src/main.js`

- [ ] Export deposit + settlement features as irregular polygons (hash-stable vertices).
- [ ] Viewer: fill + line layers; remove circle layers for resources/settlement.
- [ ] Commit.

### Task 4: Polar display

**Files:**
- Modify: `maps/viewer/src/main.js`
- Modify: `maps/viewer/README.md` (brief note)

- [ ] Set world image coordinates to ±90°.
- [ ] Smoke: Vite serves `/world/world-color.png`; document globe-pole expectation.
- [ ] Commit.

### Task 5: Regenerate, docs, ship

**Files:**
- Modify: generator/canon docs that claim algorithmic 29% targeting
- Regenerate: `maps/exports/*`, `maps/viewer/public/world/*`

- [ ] Update README / principles wording: emergent land%; Veldara reference board unchanged.
- [ ] Regenerate seed 42 present + LGM; commit artifacts.
- [ ] Push; update PR.
