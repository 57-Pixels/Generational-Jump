# Veldara Map Viewer

Google-Maps-style viewer: **2D mercator while zoomed in** (theater / war map), **globe when zoomed out**.

## Hosted URL (preferred)

**https://57-pixels.github.io/Generational-Jump/**

No local install needed — open that on your phone.

Asset paths are **relative** (`base: "./"`), so renaming the GitHub repo again will not break the viewer.

### One-time GitHub setup

1. Repo **Settings → Pages**
2. **Source:** GitHub Actions
3. Re-run **Deploy map viewer** if the site looks like plain text (old deploy still pointing at `/FantasyMilitaryProject/assets/...`)

## Local (optional)

```bash
cd maps/viewer
npm install
npm run dev
```

Open `http://localhost:5173`.

## Behavior

| Zoom | Projection |
| --- | --- |
| `< 4.25` | `globe` |
| `≥ 4.25` | `mercator` (war-map / theater mode) |

Threshold: `GLOBE_MAX_ZOOM` in `src/main.js`.

The algorithmic basemap is served as **Web Mercator XYZ raster tiles**
(`public/world/tiles/color/{z}/{x}/{y}.png`). That matches MapLibre’s normal
Earth/satellite path: tile meshes cover ±85.05°, and **globe mode stretches
edge tiles to the poles**. A single full-world `image` source cannot do that
(`allowPoles` is false for ImageSource).

## War layers (ready for later)

Demo GeoJSON in `public/data/layers/`:

- `control.geojson` — control fills
- `front.geojson` — front line
- `events.geojson` — clickable events

Schema: [`data/schema.md`](data/schema.md).

Date scrubber UI is present but disabled until date filtering is implemented.

## Placeholder basemap

MapLibre **demo Earth style** until custom Veldara tiles exist. Then swap `style` in `src/main.js`, move `EASTMARCH`, replace demo GeoJSON.

## CI

Built with **Node 24** in `.github/workflows/deploy-map-viewer.yml`.
