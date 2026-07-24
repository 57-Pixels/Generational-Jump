# maps/

Cartography: **algorithmic world first**, briefs + interactive viewer.

| Path | Use |
| --- | --- |
| [`generator/`](generator/) | **Canonical map creation** (Python tectonics → PNG) |
| [`exports/`](exports/) | `world-color.png`, `world-height.png`, meta |
| [`viewer/`](viewer/) | MapLibre app (2D↔globe) on GitHub Pages |
| [`00-world-map-brief.md`](00-world-map-brief.md) | Design constraints (still useful; generator implements them) |
| [`01-country-maps-brief.md`](01-country-maps-brief.md) | Veldara multi-map set (derive from exports later) |

**Rule:** locked generator outputs (+ formation doc) beat vibes. No autoregressive image-gen as canon.

## Generate the world

```bash
cd maps/generator && pip install -r requirements.txt && python3 generate_world.py
```

## Interactive viewer

**Hosted:** https://57-pixels.github.io/Generational-Jump/  
```bash
cd maps/viewer && npm install && npm run dev   # optional local
```
