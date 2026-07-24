# Algorithmic world generator

Two paths:

| Path | What | Use |
| --- | --- | --- |
| **`deeptime/`** | Plate sim over Ma ticks — continents form by rift/subduction/collision | **Default for new stories** (unique seed) |
| **`generate_world.py`** | Hand-authored ellipse tectonics for the Veldara reference campaign | Reproduce today's Generational-Jump board |

Canon: [`../../world/05-planetary-formation.md`](../../world/05-planetary-formation.md) · [`../../world/12-worldbuilding-principles.md`](../../world/12-worldbuilding-principles.md) · [`../../docs/superpowers/specs/2026-07-24-world-generation-design.md`](../../docs/superpowers/specs/2026-07-24-world-generation-design.md)

## Deep-time (preferred)

```bash
cd maps/generator
pip install -r requirements.txt
python3 -m deeptime --seed 42 --width 1024 --height 512
python3 -m deeptime --seed 42 --era lgm
python3 -m deeptime --seed 100 --reroll-hooks   # try nearby seeds until story hooks pass
```

Targets present **land ≈ 29%**. Writes `maps/exports/world-*.png` and copies into `maps/viewer/public/world/` (overwrites viewer basemap — commit deliberately).

Also writes `world-plates.png`, `world-resources.png`, and `world-resources.geojson` (gold, REE, HP silica, oil, copper, …).

## Reference campaign (ellipses)

```bash
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era present
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era lgm
```

## Outputs

| File | Purpose |
| --- | --- |
| `../exports/world-height.png` | Greyscale elevation |
| `../exports/world-color.png` | Atlas color (viewer basemap) |
| `../exports/world-plates.png` | Plate ID preview (deeptime) |
| `../exports/world-*-lgm.png` | LGM snapshot |
| `../exports/world-meta*.json` | Seed, land fraction, hooks |
| `../viewer/public/world/*` | Pages copies |

## Viewer

`maps/viewer` loads `world/world-color.png`. Re-run generator, commit PNGs, Pages updates on deploy.
