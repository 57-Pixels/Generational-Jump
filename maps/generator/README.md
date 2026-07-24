# Algorithmic world generator

Two paths:

| Path | What | Use |
| --- | --- | --- |
| **`deeptime/v2/`** | Cubed-sphere rigid plates → geology → climate/hydrology → resources → settlement | **Default for new stories** |
| `deeptime/simulate.py` | Legacy raster-advection prototype | Explicit `--engine v1` comparison only |
| **`generate_world.py`** | Hand-authored ellipse tectonics for the Veldara reference campaign | Reproduce today's Generational-Jump board |

Canon: [`../../world/05-planetary-formation.md`](../../world/05-planetary-formation.md) · [`../../world/12-worldbuilding-principles.md`](../../world/12-worldbuilding-principles.md) · [`../../docs/superpowers/specs/2026-07-24-world-generation-design.md`](../../docs/superpowers/specs/2026-07-24-world-generation-design.md)

## Deep-time (preferred)

```bash
cd maps/generator
pip install -r requirements.txt
python3 -m deeptime --engine v2 --seed 42 --grid-n 64 --width 1024 --height 512
python3 -m deeptime --engine v2 --seed 42 --grid-n 64 --era lgm
```

Targets **emergent** present land fraction from crust history (no 29% clamp). LGM reuses identical bedrock at **−120 m** sea level. Writes `maps/exports/world-*` and copies into `maps/viewer/public/world/`.

V2 separates:

- plate (rigid kinematic domain)
- continent (continental-crust / terrane lineage)
- landmass (connected dry land)
- physical habitability by era
- incentives that can override poor habitability

Continents evolve as a **crust-thickness field** (collision thickens, rift thins, anisotropic seeds) — not circular caps. A/C uplift requires grid/capital/energy and reports cooling burdens.

## Reference campaign (ellipses)

```bash
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era present
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era lgm
```

## Outputs

| File | Purpose |
| --- | --- |
| `../exports/world-color.png` | Atlas color (viewer basemap) |
| `../exports/world-plates.png` | Rigid plate IDs |
| `../exports/world-continents.png` | Continental terrane lineages |
| `../exports/world-landmasses.png` | Connected dry land |
| `../exports/world-climate.png` | Temperature / precipitation / humidity diagnostic |
| `../exports/world-rivers.png` / `.geojson` | Drainage network |
| `../exports/world-resources.png` / `.geojson` | Geology-derived deposits and economic properties |
| `../exports/world-settlement.png` / `.geojson` | A/C-era attraction and candidate mechanisms |
| `../exports/world-*-lgm.png` | LGM snapshot |
| `../exports/world-meta*.json` | Seed, semantics, counts and assumptions |
| `../viewer/public/world/*` | Pages copies |

## Viewer

`maps/viewer` loads the atlas plus Resources, Rivers, Settlement and War toggles.

## Verification

```bash
PYTHONPATH=maps/generator \
python3 -m unittest discover -s maps/generator/tests -p 'test_v2_*.py' -v
```

Tests cover spherical area/neighbors, connected plates, signed boundaries, present/LGM bedrock identity, climate/hydrology, variable resource provinces, A/C uplift, and incentive-driven settlement.
