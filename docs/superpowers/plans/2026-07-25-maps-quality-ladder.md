# Maps Quality Ladder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise published map morphology to `t1` globally and wire nested `t2`–`t4` theater refine into deep tiles so zoom bands stay sharp together.

**Architecture:** `--publish` selects `t1` + denser equirect/tiles; refine windows composite into the sparse XYZ pyramid; viewer maxzoom follows real detail. Canon seed scoring is deferred.

**Tech Stack:** Python/numpy deeptime v2, Pillow tiles, MapLibre viewer.

## Global Constraints

- Branch prefix `cursor/`, suffix `-c216`
- Prefer TDD for behavior changes
- Do not loosen existing refine RMS / seam tests
- Canon promotion optional; quality builds may use any seed (default keep 150 for continuity)
- If `t1` OOMs in this environment, ship `t0` publish first with an explicit follow-up note — do not fake detail via tile overzoom alone

---

### Task 1: Publish selects `t1` morphology

**Files:**
- Modify: `maps/generator/deeptime/__main__.py`
- Modify: `maps/generator/README.md`
- Test: `maps/generator/tests/test_v2_publish_cli.py` (create)

**Interfaces:**
- Consumes: `resolve_grid_n`, `WorldConfig`, `--publish`
- Produces: `--publish` ⇒ `tier="t1"`, `grid_n=2048`, equirect ≥4096×2048, deep tiles through z11 (unless overridden)

- [ ] **Step 1: Write failing test** that a publish-config helper (or CLI argv parse path) yields tier t1 / grid 2048 / deep z11 / width≥4096
- [ ] **Step 2: Run test — expect fail**
- [ ] **Step 3: Implement publish defaults in `__main__.py`**
- [ ] **Step 4: Run test — expect pass; update README**
- [ ] **Step 5: Commit**

---

### Task 2: Viewer zoom tracks published detail

**Files:**
- Modify: `maps/viewer/src/main.js`
- Test: lightweight assertion via existing meta load path or a small node-less comment check in generator meta contract

**Interfaces:**
- Consumes: `world-meta.json` `viewer_tiles.max_zoom` / `deep_max_zoom`
- Produces: MapLibre `maxZoom` capped to published deep zoom (no mush overzoom)

- [ ] **Step 1: Confirm current maxZoom behavior**
- [ ] **Step 2: Cap raster/map maxZoom from meta**
- [ ] **Step 3: Commit**

---

### Task 3: Wire nested refine into world generation export path

**Files:**
- Modify: `maps/generator/deeptime/v2/model.py` and/or `export.py`
- Modify: `maps/generator/deeptime/v2/refine.py` (export helpers as needed)
- Test: `maps/generator/tests/test_v2_refine_export.py` (create)

**Interfaces:**
- Consumes: `refine_window`, `WindowSpec`, `DEFAULT_DEEP_WINDOWS`, parent `WorldResult`
- Produces: optional `world.refined_windows` (or export-time windows) used when writing deep tiles / overlays

- [ ] **Step 1: Failing test — publish/export path invokes refine for deep windows at t2 target_km**
- [ ] **Step 2: Minimal wire: extract + refine + expose fields**
- [ ] **Step 3: Composite refined elevation into deep-tile color sampling for window coverage**
- [ ] **Step 4: Extend to t3/t4 where memory allows (disk-backed if required)**
- [ ] **Step 5: Commit**

---

### Task 4: Regenerate viewer package

**Files:**
- Regenerate: `maps/exports/*`, `maps/viewer/public/world/*`

- [ ] **Step 1: Run `python3 -m deeptime --engine v2 --seed 150 --publish` (or t0 interim if OOM)**
- [ ] **Step 2: Confirm meta tier/grid/tiles; spot-check coasts sharper**
- [ ] **Step 3: Run full `test_v2_*.py` suite**
- [ ] **Step 4: Commit artifacts + push + PR**
