# Veldara — Country Map Set Design Brief

> **Purpose:** multi-map set of Veldara that **inherits geology** from the world master — no decorative terrain.
> **Foundation:** [`../world/05-planetary-formation.md`](../world/05-planetary-formation.md)
> **World map:** [`00-world-map-brief.md`](00-world-map-brief.md) (lock coastlines first)
> **Country canon:** [`../world/01-our-nation.md`](../world/01-our-nation.md)

## Workflow

1. Crop/trace Veldara from the upscaled **world master** (same coastline forever).
2. Derive every landform from the formation doc (table below) — if you can't cite a cause, delete the feature.
3. Generate themed maps on that silhouette.
4. Upscale as needed; fill names later.

## Shared frame

| Spec | Value |
| --- | --- |
| Extent | Veldara + faded slivers of Korvath (E), Doverin (W/SW), Sereth (N) |
| Outline | Exact world-master crop |
| North | Up |
| Style | Same Earthlike atlas family as the world physical map |

## Region = process (not vibe)

| Region | Geologic / climatic cause | What maps must show |
| --- | --- | --- |
| **Westreach** | Coastal strip west of subduction cordillera; orographic rain | Narrow wet coastal lowland, deep rocky inlets/harbors, dense settlement later |
| **Highspine** | Active West Ocean subduction orogeny + volcanic arc | Continuous N–S mountain belt parallel to west coast; volcanoes OK *on the arc*; trench offshore on physical maps |
| **Western lee / High Plains steppe** | Rain shadow immediately east of Highspine | Drier belt before true Heartland humidity returns |
| **Heartland Plains** | Stable interior + glacial till/outwash/loess | Flat-to-rolling, thick soils, big consequent rivers toward East Gulf |
| **Northwood** | Ice-scoured old crust / highland flank | Lakes, disordered drainage, thin soils, cold climate |
| **Eastmarch** | Same Aurelian crust as Korvath; mild Cenozoic warping only | Open approaches, low ridges — **not** a plate boundary; threat axis for Map F |
| **Gulf Coast** | Passive-margin embayment + warm gulf climate | Broad shelf, deltas, lagoons, humid subtropical; dredging-dependent ports |
| **Southmere** | Southern warm passive/gulf margin | Deltas, wetlands, energy geology (sedimentary basins) |

**Aurel City:** east-central **river confluence** where Heartland drainages gather toward the Gulf — a classic capital-on-navigation site, not a mountain fortress.

**Drainage law:** rivers rise in Highspine / Sereth highland / Eastmarch and run to West Ocean (short steep) or East Gulf (long). No river crosses Highspine westward.

---

## Map A — Political / administrative

**Job:** provinces, capital, cities, borders — draped on real terrain (coast/river logic for cities).

**City placement rules:**
- Westreach ports = natural rocky harbors behind the cordillera gaps/rivers
- Gulf ports = hard points / dredged delta mouths (fewer than west, and call that out)
- Heartland hubs = rail/river junctions
- Do not put the capital on the Highspine crest

**Prompt seed:**

```text
Political map of a large federal country matching reference coastline,
provinces follow rivers and mountain divides where possible,
capital at major river confluence toward a southeastern gulf,
major ports on western rocky coast and gulf hard points,
thin international borders east west north, clean modern atlas, no fantasy
```

---

## Map B — Physical / topographic (do this first)

**Job:** show the asymmetric continent slice correctly.

**Must-have landforms:**
1. West Ocean + offshore trench line
2. Highspine cordillera parallel to west coast
3. Rain-shadow steppe just east of mountains
4. Broad Heartland plains
5. Northwood glacial lakes
6. East Gulf with deltaic shelf (wide bathymetry)
7. Long rivers to the gulf; short steep west-coast rivers

**Prompt seed:**

```text
Physical topographic map, Earthlike realism, western subduction cordillera parallel to coast
with offshore trench, rain shadow plains just east of mountains, vast glacial-covered interior plains,
northern ice-scoured lake shield, southeastern passive-margin gulf with large river deltas and wide shelf,
hypsometric tint, major rivers draining to gulf, no cities, scientific atlas
```

---

## Map C — Climate

**Job:** Hadley / storm-track / rain-shadow truth.

| Zone | Where | Cause |
| --- | --- | --- |
| Marine west coast | Westreach | Storm track + orographic lift |
| Highland | Highspine | Elevation |
| Semi-arid lee | Immediate east of Highspine | Rain shadow |
| Humid continental | Heartland + Eastmarch | Interior mid-latitude |
| Subarctic | Northwood | Latitude + continentality |
| Humid subtropical | Gulf Coast + Southmere | Warm gulf + onshore flow |

**Prompt seed:**

```text
Climate zones map grounded in Earth atmospheric science,
wet marine strip only on western ocean side of cordillera,
semi-arid band in mountain rain shadow, humid continental interior,
cold north, humid subtropical around southeastern warm gulf,
pastel fills, clean legend space, no fantasy biomes
```

---

## Map D — Population & infrastructure

**Job:** people follow coasts, gaps, and rivers — not uniform fill.

**Density rules:** Westreach + Gulf urban belts dark; Heartland medium along rivers/rail; Highspine nearly empty; Northwood light; Eastmarch frontier-medium.

**Infra rules:** east–west rail through cordillera **passes** (few); main trunk across Heartland to Gulf; highways sparse trunks.

**Prompt seed:**

```text
Population density heatmap and sparse trunk rail/highway map,
dense western coastal cities and gulf cities, interior plains medium along rivers,
mountains nearly empty, northern lakes sparsely settled, clean atlas, no clutter
```

---

## Map E — Resources & industry

**Job:** resources follow geology.

| Resource | Where | Why |
| --- | --- | --- |
| Hydro / metals | Highspine foothills | Arc/orogen geology |
| Grain | Heartland | Glacial soils |
| Oil/gas / terminals | Southmere + Gulf sedimentary basins | Passive-margin sediments |
| Shipyards | Westreach rocky ports first; Gulf selected hard points | Harbor physics |
| Aerospace / advanced mfg | Capital region / Heartland secondary cities | Labor + transport, not ore |
| Small arms / ammo | Heartland secondary industrial city | Inland, rail-served |

**Prompt seed:**

```text
Resources and industry map tied to geology,
mining in western cordillera foothills, grain shading on glacial plains,
hydrocarbon markers in southern gulf sedimentary basin,
shipyards on deep western harbors, clean legend, Earthlike economic atlas
```

---

## Map F — Military / strategic

**Job:** threat geometry follows open Eastmarch crust continuity — Korvath is on the same plate.

**Show:**
- Primary threat arrows: Korvath → Eastmarch → Heartland (open approach)
- Secondary pressure: Sereth highland routes into Northwood (limited avenues)
- Friendly Doverin west (political border on continuous crust)
- Naval: Westreach (best harbors) + Gulf (contest the embayment)
- Air bases: depth in Heartland + coverage facing Eastmarch; avoid packing everything on the Westreach strip alone
- Vital ground: Aurel City, Westreach ports, Gulf complex, Southmere energy, cordillera passes (mobility chokepoints)

**Prompt seed:**

```text
Strategic military atlas map, restrained professional style,
eastern open-plain threat axis into interior, limited northern highland avenues,
naval bases on western deepwater coast and gulf, dispersed airbases with depth,
highlighted passes through western cordillera, capital and ports as vital ground,
no propaganda, muted colors
```

---

## Generation order

1. **B Physical** (locks process landforms)  
2. **C Climate** (must match B)  
3. **A Political** / **D Population** (cities follow B+C)  
4. **E Resources** (follow geology)  
5. **F Military** (follow open eastern approach + harbors)

## Acceptance checklist

- [ ] West mountains exist **because** of subduction; east gulf is passive — asymmetry obvious
- [ ] Rain shadow appears on climate + physical maps
- [ ] Rivers obey drainage law
- [ ] Northwood looks glaciated; Heartland looks farmable for glacial reasons
- [ ] Eastmarch is continuous terrain into Korvath (no fake border mountain wall unless we write a local uplift cause)
- [ ] Same coastline on every map
- [ ] Exports in `maps/exports/veldara-*.png`

## After images exist

Promote concrete province/city/base names into `world/01` and `decisions-log.md`. If art reveals a better harbor or pass layout, **update the formation-consistent prose** — don't keep a wrong story to save an old paragraph.
