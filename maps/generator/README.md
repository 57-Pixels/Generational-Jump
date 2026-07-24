# Algorithmic world generator

Deterministic planet map from tectonics rules in [`../../world/05-planetary-formation.md`](../../world/05-planetary-formation.md). **Not** autoregressive image-gen.

## Run

```bash
cd maps/generator
pip install -r requirements.txt
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era present
python3 generate_world.py --width 2048 --height 1024 --seed 42 --era lgm
```

`--era lgm` applies Earth-analogue Last Glacial Maximum conditions (lower seas, northern ice, exposed East Gulf shelf) per [`../../world/08-last-20ka.md`](../../world/08-last-20ka.md).

## Outputs

| File | Purpose |
| --- | --- |
| `../exports/world-height.png` | Greyscale elevation (present) |
| `../exports/world-color.png` | Atlas color (present; viewer basemap) |
| `../exports/world-*-lgm.png` | LGM snapshot (~20 ka Earth-analogue) |
| `../exports/world-meta*.json` | Seed, era, feature list |
| `../viewer/public/world/*` | Copies for GitHub Pages |

## What v1 encodes

- Aurelian + East Gulf (flooded in `present`, exposed shelf plain in `lgm`)
- Highspine subduction cordillera + offshore trench
- Kharzhan craton (passive west)
- Farreach collisional suture
- Solmar island-continent + curved volcanic arc
- Rain shadow / Hadley moisture → land colors
- LGM northern ice + lower sea level (Earth-analogue)

Tune geometry by editing parameters in `generate_world.py` (ellipse centers, ridge longitudes). Same `--seed` ⇒ same map.

## Viewer

`maps/viewer` loads `world/world-color.png` as an equirectangular image source (2D ↔ globe). Re-run the generator, commit the PNGs, and Pages updates on deploy.
