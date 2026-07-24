# Veldara — Country Map Set Design Brief

> **Purpose:** after the world master map is generated and upscaled, produce **multiple themed maps of Veldara** that share one outline.
> **Country canon:** [`../world/01-our-nation.md`](../world/01-our-nation.md)
> **Depends on:** locked coastlines from [`00-world-map-brief.md`](00-world-map-brief.md)

## Workflow

1. Crop / trace **Veldara only** from the upscaled world master (same coastline forever).
2. Generate or draw each map type below on that **identical silhouette**.
3. Upscale country maps as needed (8k–16k on the long edge is plenty).
4. Fill details (cities, bases, industry) to match these briefs; if art and prose disagree, **update the prose**.

## Shared frame (every Veldara map)

| Spec | Value |
| --- | --- |
| Extent | All of Veldara + a thin strip of neighbor land (Korvath east, Doverin west, Sereth north) faded or unlabeled |
| Aspect | ~**16:10** or **3:2** landscape |
| Outline | Exact match to world master crop |
| North | Up |
| Scale bar + sparse lat/long | Yes on final labeled versions |
| Style | Same clean modern atlas family as the world map |

### Macro-regions to show on every physical-ish map

Use these region names consistently:

| Region | Character |
| --- | --- |
| **Westreach** | West Ocean coast + coastal ranges + port megacities |
| **Highspine** | North–south mountain chain inland of Westreach |
| **Heartland Plains** | Vast central agricultural / rail / armor country |
| **Northwood** | Forests, lakes, cold; Sereth border |
| **Eastmarch** | Eastern provinces facing Korvath — mixed plain and low ridges |
| **Gulf Coast** | East Gulf shore — denser cities, naval complex, older industry |
| **Southmere** | Warm south — deltas, energy terminals |

Federal capital: **Aurel City** (east-central river confluence between Heartland and Gulf Coast).

---

## Map A — Political / administrative

**Job:** provinces/states, capital, major cities, land borders.

**Show:**
- 8–12 provinces (names can be placeholder until you care)
- International borders: Korvath (east, long), Doverin (west), Sereth (north)
- Cities: Aurel City (capital star), 2 Westreach ports, 2 Gulf ports, 3 Heartland hubs
- No terrain shading beyond a whisper

**Image-gen prompt seed:**

```text
Clean political map of a large federal country, landscape 3:2, identical coastline to reference,
soft white-to-gray land, colored province fills with thin borders, capital starred,
major cities as dots, labeled international borders east west and north,
no roads, no fantasy style, modern atlas, clear typography space
```

---

## Map B — Physical / topographic

**Job:** mountains, plains, rivers, coasts — the terrain that drives warfare.

**Show:**
- Highspine mountains, Heartland flatness, Northwood lakes, Eastmarch low ridges, Southmere deltas
- 2–3 major river systems draining to West Ocean and East Gulf
- Elevation shading (hypsometric)

**Prompt seed:**

```text
Physical topographic atlas map of a large country, hypsometric tint, western coastal mountains,
vast central plains, northern forest lakes, eastern low ridges, southern river deltas,
east-facing gulf coastline, west ocean coastline, major rivers, no cities, no borders labels,
clean cartography, high detail terrain
```

---

## Map C — Climate

**Job:** what kit must survive.

**Show:** climate zones only (simple pastel fills):

| Zone | Where |
| --- | --- |
| Subarctic / cold continental | Northwood |
| Humid continental | Heartland + Eastmarch |
| Marine west coast | Westreach |
| Humid subtropical | Gulf Coast + Southmere |
| Highland | Highspine |

**Prompt seed:**

```text
Climate zones map of a large country, soft pastel fills, legend-ready regions,
cold north forests, continental center, marine western coast, humid subtropical gulf south,
mountain highland strip inland of west coast, minimal labels, clean atlas style
```

---

## Map D — Population & infrastructure

**Job:** where people and movement live.

**Show:**
- Population density wash (darker = denser): Westreach + Gulf Coast dark; Heartland medium; Northwood light
- Rail spine east–west + north–south
- Interstate-analogue highways (sparse, not spaghetti)
- Major airports (4–6 dots)

**Prompt seed:**

```text
Population density and infrastructure map, soft density heatmap, few major rail lines,
sparse highway trunk routes, major airport dots, coastal cities denser,
central plains lighter, clean modern atlas, no clutter
```

---

## Map E — Resources & industry

**Job:** what the modernization builds on.

**Show (icons or simple area fills):**
- Grain belt: Heartland
- Energy (oil/gas or terminals): Southmere + offshore gulf marks
- Shipbuilding: one Westreach cluster + one Gulf cluster
- Aerospace / advanced mfg: inland plateau or capital region
- Small arms / ammo complex: Heartland secondary city (place and name when ready)
- Mining / metals: Highspine foothills

**Prompt seed:**

```text
Economic resources map of a large country, simple industrial icons,
agriculture shading on central plains, energy markers on southern gulf,
shipyard marks on west coast and gulf, aerospace cluster near capital region,
mountain foothills mining marks, clean legend space, atlas style
```

---

## Map F — Military / strategic (the useful one for the series)

**Job:** threat axes, basing, vital ground — what design docs cite.

**Show:**
- Korvath threat arrows across Eastmarch into Heartland
- Secondary Sereth pressure marks in Northwood (small)
- Friendly Doverin border (no threat arrows)
- Naval bases: Westreach + Gulf (stars)
- Air bases: dispersed set (6–10) with denser cluster opposite Korvath
- Training range / proving ground in sparse Heartland or Highspine rain shadow
- Vital ground callouts: Aurel City, both port complexes, energy terminals
- Optional: 72-hour / mobilization depot regions as shaded soft boxes (keep abstract)

**Do not show:** exact ORBATs, classified-looking grids, or pretend satellite targeting overlays.

**Prompt seed:**

```text
Strategic military overview map, clean and restrained, eastern threat axis arrows,
northern secondary pressure marks, naval base stars on west coast and gulf,
dispersed airbase symbols, capital and ports highlighted as vital ground,
no blood, no propaganda posters, professional defense atlas style, muted colors
```

---

## Suggested generation order

1. **B Physical** (locks terrain language)
2. **A Political** (locks provinces/cities on that terrain)
3. **C Climate**
4. **D Population & infrastructure**
5. **E Resources & industry**
6. **F Military / strategic** (last — needs cities + terrain + borders)

## Acceptance checklist (whole set)

- [ ] Every map shares the same Veldara coastline (pixel-trace from world master)
- [ ] Two-ocean / gulf access is obvious on A, B, and F
- [ ] Eastmarch clearly faces Korvath; Northwood faces Sereth; Doverin on the west
- [ ] Aurel City consistent location across A/D/F
- [ ] Map F is usable as a cold-open still for Episode A0-01 / threat videos
- [ ] Exports saved under `maps/exports/veldara-*.png` (add when generated)

## Filling details after images exist

When the maps are good, promote concrete names into canon:

1. Province list → `world/01-our-nation.md`
2. City + base names → decisions-log + Map F callouts
3. Industry sites → `world/03` and light `industry/README.md` notes
4. Threat axes → confirm `threat-analysis/scenarios/01-eastern-invasion.md` still matches Eastmarch geography
