# Veldara Map Viewer

Google-Maps-style viewer for the project: **2D mercator while zoomed in** (theater / Ukraine-style war map), **globe when zoomed out**.

## Run

```bash
cd maps/viewer
npm install
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`).

## Behavior

| Zoom | Projection |
| --- | --- |
| `< 4.25` | `globe` |
| `≥ 4.25` | `mercator` (war-map / theater mode) |

Threshold: `GLOBE_MAX_ZOOM` in `src/main.js`.

## War layers (ready for later)

Demo GeoJSON loads from `public/data/layers/`:

- `control.geojson` — control fills
- `front.geojson` — front line
- `events.geojson` — clickable events

Schema: [`data/schema.md`](data/schema.md) (mirrored under `public/data/`).

UI: war-layer toggle works now; **date scrubber is disabled** until we filter by `date` / `date_start`–`date_end`.

## Important — placeholder basemap

The basemap is MapLibre’s **demo Earth style**. It is temporary so the viewer works before custom Veldara tiles exist.

When the world master map is locked:

1. Cut raster tiles (or a single equirectangular raster source) from the canon map
2. Point `style` in `src/main.js` at that style/tiles
3. Move `EASTMARCH` center to the real Eastmarch lon/lat on that sphere
4. Replace demo control/front/events geometry

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Local viewer |
| `npm run build` | Static build to `dist/` (future site) |
| `npm run preview` | Preview production build |
