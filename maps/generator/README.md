# Algorithmic world generator

Two paths:

| Path | What | Use |
| --- | --- | --- |
| **`deeptime/v2/`** | Cubed-sphere rigid plates → geology → climate/hydrology → resources → settlement | **Default for new stories** |
| `deeptime/simulate.py` | Legacy raster-advection prototype | Explicit `--engine v1` comparison only |
| **`generate_world.py`** | Hand-authored ellipse tectonics for the Veldara reference campaign | Frozen board artifact only |

**Canon seed:** **150** (`promoted-seed.json`, `GENERATOR_VERSION` 2.2.0, decisions-log **D-0028**).

Canon: [`../../world/05-planetary-formation.md`](../../world/05-planetary-formation.md) · [`../../world/12-worldbuilding-principles.md`](../../world/12-worldbuilding-principles.md) · [`../../docs/superpowers/specs/2026-07-24-world-generation-design.md`](../../docs/superpowers/specs/2026-07-24-world-generation-design.md)

## Deep-time (preferred)

```bash
cd maps/generator
pip install -r requirements.txt
python3 -m deeptime --engine v2 --seed 150 --tier t0 --width 1024 --height 512
python3 -m deeptime --engine v2 --seed 150 --tier t0 --era lgm
python3 -m deeptime --engine v2 --seed 150 --publish
python3 -m deeptime --sweep-seeds 200 --grid-n 64 --ticks 40 --tier dev
```

`--publish` writes a smoother viewer package: ≥2048×1024 equirect, blended spherical
sampling, dense global tiles through z6, and deep tiles through z8 over the
Aurelian/Veldara windows. It does **not** change `--grid-n` / seed geology.

### Resolution tiers

| Tier | `grid_n` | Target spacing | Role |
| --- | --- | --- | --- |
| `dev` | from `--grid-n` (default 64) | coarse | Fast tests / seed search |
| `t0` | 256 | ~35 km | Global tectonics |
| `t1` | 2048 | ~4.5 km | Global surface / coasts |
| `t2`–`t4` | windowed | 1 km → 100 m | Nested refine over Aurelian / Veldara |

### Sparse tiles

| Zoom | Coverage |
| --- | --- |
| z0–z6 | Global (~5,461 tiles) |
| z7–z11 | Aurelian + Veldara windows only (~tens of thousands) |

`t0`/`t1` CLI runs write the full sparse pyramid; `dev` keeps zooms cheap (z2/z3).

Targets **emergent** present land fraction from crust history (no 29% clamp). Seed 150 measures ≈ **0.444**. LGM reuses identical bedrock at **−120 m** sea level. Writes `maps/exports/world-*` and copies into `maps/viewer/public/world/`.

V2 separates:

- plate (rigid kinematic domain)
- continent (continental-crust / terrane lineage)
- landmass (connected dry land)
- physical habitability by era
- incentives that can override poor habitability
- named features + navigability (`world-features*.geojson`, `world-navigation*.geojson`)

Continents evolve as a **crust-thickness field** (collision thickens, rift thins, anisotropic seeds) — not circular caps. A/C uplift requires grid/capital/energy and reports cooling burdens.

## Reference campaign (ellipses)

```bash
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era present
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era lgm
```

## Outputs

| File | Purpose |
| --- | --- |
| `../exports/world-color.png` | Atlas color (equirect reference) |
| `../exports/tiles/color/{z}/{x}/{y}.png` | Web Mercator XYZ basemap (sparse deep zoom) |
| `../exports/tiles/color/coverage.json` | Deep-window coverage manifest |
| `../exports/world-plates.png` | Rigid plate IDs |
| `../exports/world-continents.png` | Continental terrane lineages |
| `../exports/world-landmasses.png` | Connected dry land |
| `../exports/world-climate.png` | Temperature / precipitation / humidity diagnostic |
| `../exports/world-rivers.png` / `.geojson` | Drainage network |
| `../exports/world-resources.png` / `.geojson` | Geology-derived deposits and economic properties |
| `../exports/world-settlement.png` / `.geojson` | A/C-era attraction and candidate mechanisms |
| `../exports/world-features.geojson` | Named seas, ranges, lakes, islands, … |
| `../exports/world-navigation.geojson` | Harbours, chokepoints, shelf break |
| `../exports/world-*-lgm.png` | LGM snapshot |
| `../exports/world-meta*.json` | Seed, semantics, counts and assumptions |
| `../viewer/public/world/*` | Pages copies |

## Viewer

`maps/viewer` loads the atlas plus Resources, Rivers, Settlement, Features, Navigation and War toggles. Raster `maxzoom` follows `world-meta.json` (deep pyramid); MapLibre overzooms outside sparse windows. Globe mode still stretches polar tile edges.

## Verification

```bash
cd maps/generator
python3 -m unittest discover -s tests -p 'test_v2_*.py' -v
```

Includes the consolidated morphology suite (`test_v2_morphology_validation.py`) against the promoted seed.
