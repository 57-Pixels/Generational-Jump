# War layer schema (Ukraine-style, later)

GeoJSON in `layers/` is the source of truth for conflict overlays. The viewer loads them today; a date scrubber will filter them later.

## Common rules

- CRS: WGS84 lon/lat for now (MapLibre default). When the fictional world basemap lands, either keep lon/lat on a fake sphere textured with the world map, or document a custom tile scheme — **do not mix silently**.
- `confidence`: `placeholder` | `estimated` | `confirmed`
- IDs are stable strings; never reuse for a different feature.

## `control.geojson` (polygons)

| Property | Type | Meaning |
| --- | --- | --- |
| `id` | string | Stable id |
| `controller` | string | e.g. `veldara`, `korvath`, `contested`, `neutral` |
| `date_start` | ISO date | First day this polygon is valid |
| `date_end` | ISO date or `null` | Last day inclusive; `null` = still valid |
| `note` | string | Optional |

Time scrubbing (future): keep features where `date_start <= selected <= (date_end ?? ∞)`.

## `front.geojson` (lines)

| Property | Type | Meaning |
| --- | --- | --- |
| `id` | string | Stable id |
| `date` | ISO date | Snapshot day for this line |
| `side_left` / `side_right` | string | Controllers on each side (map-facing convention — document per theater) |
| `note` | string | Optional |

Future: either one MultiLineString per day, or many features filtered by `date == selected`.

## `events.geojson` (points)

| Property | Type | Meaning |
| --- | --- | --- |
| `id` | string | Stable id |
| `name` | string | Popup title |
| `date` | ISO date | When it happened |
| `kind` | string | `battle` \| `strike` \| `logistics` \| `other` |
| `note` | string | Popup body |

## Theater note

Demo geometry sits near a placeholder “Eastmarch” view (`src/main.js` → `EASTMARCH`). Replace with Veldara/Korvath geometry after the world master map is locked.
