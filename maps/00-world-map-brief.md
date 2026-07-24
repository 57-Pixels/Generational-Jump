# World Map — Image Generation Brief

> **Purpose:** generate a clean **base world map**, then upscale (~16k) and use it as the canvas for labels and detail.
> **Canon geography:** [`../world/00-world-overview.md`](../world/00-world-overview.md)
> **Next step after upscale:** country detail maps in [`01-country-maps-brief.md`](01-country-maps-brief.md)

## Workflow

1. Generate a **low-label / no-label** world map from the prompt below (high composition quality matters more than tiny text).
2. Upscale to ~16k with your upscaler (preserve coastlines; avoid inventing new continents).
3. Add labels, borders, and city dots in a second pass (editor or a second image-gen inpainting pass using the **Label pass** notes).
4. Lock the upscaled unlabeled (or lightly labeled) map as the **master reference**; all later country maps must match its coastlines.

## Map specs

| Spec | Value |
| --- | --- |
| Projection | **Equirectangular** (plate carrée) — easiest to upscale and crop |
| Aspect | **2:1** (e.g. 4096×2048 gen → upscale toward 16384×8192) |
| Style | Clean modern atlas: muted oceans, subtle relief shading on land, thin coastlines, **no fantasy parchment**, no ornate compass roses dominating the frame |
| Labels on first pass | **None** (preferred) or only continent names in large sparse type |
| Grid | Optional very faint lat/long; omit if it fights the upscaler |
| Ice | Visible north and south polar caps |

## Continents to draw (shape language)

Describe shapes so the model stays consistent. These are **design targets**, not sacred coastlines — once you generate a good map, **that** map becomes canon and these prose shapes defer to it.

### 1. Aurelian (home continent) — center-west of the frame

- Large irregular continent, roughly **North America–meets–Eurasia** silhouette energy without copying either.
- **Wider east–west than north–south**, with a big western ocean coast and a large eastern gulf that almost pinches a peninsula.
- Northern third = broad forests/lakes; central belt = plains; western edge = mountain spine just inland of the coast; south = warmer lowlands.
- Room for: **Veldara** (large western-central chunk with two coasts), **Korvath** (east of Veldara), **Doverin** (west/southwest neighbor), **Sereth** (north highland).

### 2. Solmar (Solara's homeland) — far west / west-ocean

- Large **island-continent** plus a trailing archipelago to the south/east.
- Compact mountainous west, gentler eastern shelves.
- Reads as a maritime power's home: lots of coast relative to area.

### 3. Kharzhan landmass — far east

- Huge **continental block**, deeper interior than Aurelian.
- Long north–south span; few deep oceanic gulfs; big river plains in the center.
- Feels land-power heavy: fewer islands, more frontier depth.

### 4. Farreach — lower third / south-east of center

- Separate southern continent where the Maravic War burns.
- Two large sub-regions divided by a mountain spine or inland sea: **Nerath** side vs **Tesen** side (do not draw front lines on the base map).
- Warmer color palette (savanna/subtropical/desert belts OK).

### Oceans & seas

- **West Ocean** between Solmar and Aurelian's west coast.
- **East Ocean** between Aurelian's gulf side and Kharzhan.
- A **narrower equatorial belt of islands** is fine for visual interest — keep them secondary so they don't steal focus from the four landmasses.

## Color & relief (keep simple for upscaling)

- Ocean: flat blue-gray, slightly darker in trenches if subtle.
- Land: soft hypsometric tint (green lowlands → tan high plains → gray-white peaks).
- No national fill colors on the **first** pass (borders come later).
- No city glow, no roads, no icons.

## Image-gen prompt (copy/paste)

Use as a base; adjust for your model.

```text
Equirectangular world map, 2:1 aspect, clean modern atlas style, muted blue-gray oceans,
subtle hypsometric land relief, thin precise coastlines, four major continents:
(1) large central-west continent with a long western ocean coast, inland western mountains,
central plains, northern forests and lakes, and a large eastern gulf;
(2) far-west island-continent with a southern archipelago;
(3) far-east huge continental landmass with deep interior plains and few gulfs;
(4) southern separate continent with a central mountain spine,
plus north and south polar ice caps,
no country borders, no city labels, no roads, no fantasy parchment,
no ornate decorations, no watermarks, high detail coastlines, cartographic, neutral lighting
```

### Negative prompt (if your tool supports it)

```text
text, labels, country names, cities, roads, flags, fantasy map, parchment, compass rose,
sea monsters, clouds covering land, satellite photo, blurry coasts, extra continents,
UI, watermark, collage
```

## Label pass (after upscale)

Add in a graphics editor (recommended) or careful inpaint:

**Continent names (large):** Aurelian, Solmar, Kharzhan, Farreach  
**Oceans:** West Ocean, East Ocean  
**Countries (medium, only once coasts are locked):**

| Label | Where on Aurelian |
| --- | --- |
| Veldara | Western-central mass with west coast + east gulf access |
| Korvath | East of Veldara, inland + some gulf/east coast if it fits |
| Doverin | West/southwest of Veldara |
| Sereth | North of Veldara, highland |

| Label | Elsewhere |
| --- | --- |
| Solara | Solmar island-continent |
| Kharzhan State | Kharzhan landmass |
| Nerath Compact | Farreach, one side of the spine |
| Tesen League | Farreach, other side of the spine |

Optional small caption: "Maravic War theater" under Farreach — no front line art on the master map.

## Acceptance checklist

- [ ] Exactly four primary landmasses readable at a glance
- [ ] Aurelian clearly has **two major maritime fronts** (west ocean + east gulf)
- [ ] Solmar reads as island-continent; Kharzhan reads as deep continental
- [ ] Farreach is visually separate (wake-up war can be "elsewhere")
- [ ] First pass has little/no text so upscale doesn't destroy lettering
- [ ] Upscaled master saved as `maps/exports/world-master.png` (or similar — add when you generate)

## After the master exists

1. Log coastline lock in `decisions-log.md` ("world master map locked").
2. Trace Veldara's border from the master into the country map set ([`01-country-maps-brief.md`](01-country-maps-brief.md)).
3. Update any prose in `world/` that disagrees with the locked coastlines (map wins).
