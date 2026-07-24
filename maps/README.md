# maps/

Cartography briefs + interactive viewer. **Geology first** — see [`../world/05-planetary-formation.md`](../world/05-planetary-formation.md).

| Path | Use |
| --- | --- |
| [`00-world-map-brief.md`](00-world-map-brief.md) | World map design / image-gen → upscale |
| [`01-country-maps-brief.md`](01-country-maps-brief.md) | Veldara multi-map set |
| [`viewer/`](viewer/) | **MapLibre app** — 2D in-theater, globe when zoomed out; war-layer hooks |
| `exports/` | Generated PNGs (`world-master.png`, `veldara-*.png`) |

**Rule:** locked master coastlines beat prose. Features without a cause in the formation doc do not belong on the map.

## Interactive viewer

**Hosted (preferred):** https://57-pixels.github.io/FantasyMilitaryProject/  
(GitHub Pages — enable Source: GitHub Actions once; see [`viewer/README.md`](viewer/README.md))

```bash
cd maps/viewer && npm install && npm run dev   # optional local
```

Basemap is a placeholder Earth style until custom Veldara tiles exist. GeoJSON war layers (`control` / `front` / `events`) are wired for a future Ukraine-style time scrubber.