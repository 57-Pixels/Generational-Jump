# Algorithmic world generator

Deterministic planet map from tectonics rules in [`../../world/05-planetary-formation.md`](../../world/05-planetary-formation.md). **Not** autoregressive image-gen.

## Run

```bash
cd maps/generator
pip install -r requirements.txt
python3 generate_world.py --width 2048 --height 1024 --seed 42
```

Higher detail (slower):

```bash
python3 generate_world.py --width 4096 --height 2048 --seed 42
```

## Outputs

| File | Purpose |
| --- | --- |
| `../exports/world-height.png` | Greyscale elevation |
| `../exports/world-color.png` | Atlas-style color (viewer basemap) |
| `../exports/world-meta.json` | Seed + feature list |
| `../viewer/public/world/*` | Same files copied for GitHub Pages |

## What v1 encodes

- Aurelian + East Gulf embayment
- Highspine subduction cordillera + offshore trench
- Kharzhan craton (passive west)
- Farreach collisional suture
- Solmar island-continent + curved volcanic arc
- Rain shadow / Hadley moisture → land colors

Tune geometry by editing parameters in `generate_world.py` (ellipse centers, ridge longitudes). Same `--seed` ⇒ same map.

## Viewer

`maps/viewer` loads `world/world-color.png` as an equirectangular image source (2D ↔ globe). Re-run the generator, commit the PNGs, and Pages updates on deploy.
