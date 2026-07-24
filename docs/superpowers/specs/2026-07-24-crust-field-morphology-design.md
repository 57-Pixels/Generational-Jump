# Crust-field morphology & polar display

## Problem

v2 continents are unions of **circular spherical caps** (`TerraneModel.rasterize`). Coasts and mountains read as soft blobs next to an Earth map. Present land is **forced to ~29%** via sea-level fitting, which further fakes the silhouette. Resource/settlement overlays use **circle markers**. The MapLibre basemap image is pinned to **±85°**, so globe poles show empty background.

## Decisions

1. **Crust-field tectonics (approach C):** continental crust is a continuous thickness/age field evolved by plate-boundary events — not painted circles.
2. **No land-fraction target:** drop `target_land_fraction` / `fit_area_fraction_level` for v2. Land% is an emergent output. (Veldara *reference campaign* prose may still describe that board as ~29%; algorithmic seeds do not.)
3. **Fixed present sea level** (0 m reference on the elevation field); LGM remains bedrock − 120 m.
4. **Viewer poles:** map the equirectangular atlas to **±90°** on the globe path so polar cells display.
5. **Non-circular markers:** deposits and settlement sites export irregular polygon footprints; viewer renders fill/outline, not circles.

## Architecture

```
plates (Euler + Voronoi labels)
  → advect crust fields with owning plate
  → signed boundaries → event intensities
  → update thickness / age / continent_id
  → elevation from thickness + orogeny − basins + ocean cooling
  → sea_level = 0 (present) or −120 (LGM)
  → climate / hydro / resources / settlement (unchanged contracts)
```

### Crust state (per cell)

| Field | Role |
| --- | --- |
| `thickness_km` | Continental crust thickness; oceanized cells sit near oceanic default |
| `continental` | Smooth occupancy derived from thickness (for existing consumers) |
| `continent_id` | Lineage label; −1 when oceanized |
| `basement_age_ma` | Ages with continental retention; resets/youngs on oceanization |
| Event `memory` / lithology / paleoclimate | Same names as v2 consumers expect |

### Init

- Choose a subset of plates; seed **anisotropic** thickness cores (elongated tangent-plane ellipses + coherent noise), not circular caps.
- Multiple lobes per lineage allowed; axes and noise differ so silhouettes are irregular from tick 0.

### Per-tick update

1. **Remesh advection:** for each cell, rotate xyz backward by its plate’s Euler step; sample thickness/age/id from the donor cell (nearest).
2. **Boundary events:** convergent arc/collision thicken and raise orogeny; sutures weld ids; divergent continental rift thins/stretches; ocean ridge only ages/thins oceanic; transform shears samples laterally; breakup oceanizes when thickness falls below threshold; post-rift margins accumulate passive-margin memory + margin-local noise.
3. **Elevation** from thickness/isostasy-ish terms + orogeny − basins + ridge; **no** land% retarget.

### Viewer

- Image source coordinates: `[-180,90]…[180,-90]`.
- Globe remains default world view; mercator theater mode still cannot show true poles (projection limit) — acceptable.
- Resource/settlement layers: polygon fill + outline; click still shows properties.

## Acceptance

- Seeded worlds are deterministic.
- Present/LGM share bedrock; LGM sea = present − 120 m.
- Land fraction is **reported**, not constrained to 0.26–0.32.
- Landmass shapes fail a “near-circle” check more often than the old cap model (isoperimetric / aspect diagnostics in tests).
- Collision/rift memories visibly affect thickness and coast embayments in unit fixtures.
- Globe view at poles shows atlas content (not void), verified by overlay bounds + smoke load.
- Resource GeoJSON features are Polygon/MultiPolygon (or have polygon geometry alongside a point); viewer has no resource/settlement `circle` layers.

## Out of scope

- True mantle CFD / full Stokes.
- True polar wander decoupling geographic vs climatic poles.
- Replacing MapLibre with a custom WebGL globe.
