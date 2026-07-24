# Veldara Map Viewer

Google-Maps-style viewer: **2D mercator while zoomed in** (theater / war map), **globe when zoomed out**.

## Hosted URL (preferred)

After GitHub Pages is enabled and the workflow runs:

**https://57-pixels.github.io/&lt;repo-name&gt;/** (after rename, use the new repo name)

No local install needed — open that on your phone.

Asset paths are **relative** (`base: "./"`), so renaming the GitHub repo does not break the viewer.

### One-time GitHub setup

1. Repo **Settings → Pages**
2. **Source:** GitHub Actions
3. Push to `main` (or this branch) / wait for the **Deploy map viewer** workflow  
   Or: Actions → Deploy map viewer → Run workflow

If the link 404s, Pages source is usually still set to “branch” instead of “GitHub Actions”.

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

## War layers (ready for later)

Demo GeoJSON in `public/data/layers/`:

- `control.geojson` — control fills
- `front.geojson` — front line
- `events.geojson` — clickable events

Schema: [`data/schema.md`](data/schema.md).

Date scrubber UI is present but disabled until date filtering is implemented.

## Placeholder basemap

MapLibre **demo Earth style** until custom Veldara tiles exist. Then swap `style` in `src/main.js`, move `EASTMARCH`, replace demo GeoJSON.
