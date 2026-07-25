# World Map — Image Generation Brief

> **Purpose:** constraints for the **algorithmic** world map (and optional art passes).
> **Canon generator:** [`generator/`](generator/) — run this; do **not** use autoregressive image-gen as the source of truth.
> **Foundation:** [`../world/05-planetary-formation.md`](../world/05-planetary-formation.md)
> **Next:** [`01-country-maps-brief.md`](01-country-maps-brief.md)

## Workflow

1. Skim `05-planetary-formation.md`.
2. Run the **promoted** deep-time seed (canon):  
   `cd maps/generator && python3 -m deeptime --engine v2 --seed 150 --tier t0`
3. Inspect `maps/exports/world-color.png` / tiles / GeoJSON against the acceptance checklist and `tests/test_v2_morphology_validation.py`.
4. Commit exports + `viewer/public/world/` copies; Pages viewer picks them up on deploy.
5. Optional: upscale the color PNG for print — **do not** redraw continents in an image model.
6. Label pass / political overlays later as GeoJSON on the same sphere.

**Canon:** seed **150**, `GENERATOR_VERSION` **2.2.0**, Veldara claim ≈ lon **144°** / lat **31°** on the algorithmic sphere (see `generator/promoted-seed.json`, decisions-log **D-0028**).

## Map specs

| Spec | Value |
| --- | --- |
| Projection | **Equirectangular** 2:1 |
| Gen → upscale | e.g. 4096×2048 → toward 16384×8192 |
| Style | Modern physical atlas / hypsometric + subtle bathymetry — **Earthlike realism**, not parchment fantasy |
| Labels (pass 1) | **None** |
| Show | Coastlines, shelves, cordillera, glacial north, suture orogeny, island arc, polar ice |
| Hide | Borders, cities, roads, flags, ornate compasses |

## Continents / landmasses to draw

**Definitions:** plate = current rigid motion; continent = continental-crust lineage; landmass = continuous dry land. Present land fraction is **emergent** (promoted seed 150 ≈ 44%).

**Reference campaign speech:** plates **Aurelian**, **Kharzhan**, **Solmar**, **Nerath**, **Tesen**; landmass **Farreach** = Nerath+Tesen suture. Prefer regenerating via [`generator/deeptime`](generator/deeptime/) with **seed 150** for new stories.

### Aurelian (home) — mid-frame, northern hemisphere heavy

| Feature | Cause | Visual |
| --- | --- | --- |
| West coast + inland mountains | Oceanic plate subducting east under the continent | Tight coastal plain → steep **cordillera** (Highspine) parallel to coast; possible offshore trench darker blue |
| Interior plains | Stable interior + glacial/outwash cover | Broad low relief heartland east of the cordillera |
| Northern lakes/shield | Ice-age scour on old crust | Irregular lakes, mottled coastline in the north — not smooth |
| East / southeast gulf | Passive-margin embayment + big river sediment | Wide **gulf** with broad shelf, deltaic coast, few cliffs |
| Facing East Ocean coast outside the gulf | Passive rift margin | Gentler, sedimented, **no** young volcanic chain |

Veldara will later claim: west cordillera coast + plains + gulf. Korvath continues east on the **same** continent (no oceanic suture between them).

### Solmar — island-continent (Australia-scale) in the West Ocean

| Feature | Cause | Visual |
| --- | --- | --- |
| Island-continent | Continental fragment above the West Ocean subduction system | Large island landmass — smaller than the three continents, still major |
| Mountainous west | Arc / cordillera above the slab | High west side |
| Gentler east | Back-arc / remnant shelf | Lower east coast |
| Southern island chain | Volcanic island arc from slab rollback | Curved **arc** of islands — curved, not random spray |

### Kharzhan — far east

| Feature | Cause | Visual |
| --- | --- | --- |
| Huge block | Thick craton from the old megacontinent | Vast interior, long N–S |
| West coast (faces East Ocean) | Other side of the old rift = **passive margin** | Broad plains to the sea, big rivers, **no** Andes on this shore |
| Far east / south margins | Older accretionary belts | Mountains on the *outer* rim away from Aurelian, not mirroring Aurelian's west cordillera |

### Farreach — southern hemisphere continent

| Feature | Cause | Visual |
| --- | --- | --- |
| Central high range | Active **continental collision suture** | Serious orogeny down the middle or slightly offset |
| Flank arid belts | Rain shadows + subtropical subsidence | Tan interiors on one or both flanks |
| Wet windward coasts | Orographic lift where winds hit the suture | Green strips on the wet side only |
| Separate from northern continents | Never fully sutured north | Clear oceanic separation — wake-up war is geographically "elsewhere" |

### Oceans

- **West Ocean:** active — trench hints along Aurelian west + Solmar west; island arc south of Solmar.
- **East Ocean:** younger basin from megacontinent breakup — wider shelves on Aurelian east and Kharzhan west.

## Climate coloring (subtle, physics-true)

Do **not** paint biomes at random. If the model supports soft biome tint:

- Wet mid-latitude marine strip **west** of Highspine only
- Drier lee just east of Highspine
- Humid subtropical around the East Gulf
- Cold mottled north (glacial)
- Farreach: wet coasts vs dry suture flanks
- Subtropical arid bands near ~20–30° latitude on west coasts of continents where applicable

## Image-gen prompt (copy/paste)

```text
Equirectangular Earthlike physical world map, 2:1, realistic plate-tectonics geography,
hypsometric land tint, subtle ocean bathymetry, no borders no cities no labels,

western ocean with a subduction trench and a large island-continent that has a high volcanic
cordillera on its oceanward west side and a curved volcanic island arc trailing south,

central continent in the northern hemisphere with: (1) an Andean-style cordillera parallel to
its western ocean coast from eastward subduction, (2) broad interior plains east of those mountains,
(3) glacial lake-strewn shield terrain in the far north, (4) a large passive-margin gulf and deltaic
shelf on the southeast coast, (5) no young mountains on the passive eastern ocean margin,

eastern huge craton continent across a wide younger ocean with passive western coasts and big rivers,
mountains only on its far outer east and south margins,

southern separate continent split by a high collisional suture orogeny with rain-shadow arid flanks
and wetter windward coasts,

north and south polar ice, realistic coastlines, natural Earth-analog landforms,
scientific atlas style, photoreal cartography, not fantasy
```

### Negative prompt

```text
fantasy map, parchment, compass rose, sea monsters, country borders, city lights, text, labels,
perfectly symmetric continents, random volcanoes inland, mountains on both opposite coasts of the
same continent without cause, circular supercontinent, roads, flags, watermark, UI, satellite HUD
```

## Acceptance checklist (geology first)

- [ ] Aurelian west = cordillera + trench logic; Aurelian east/gulf = passive / deltaic — **asymmetric**
- [ ] Solmar = arc/island-continent + **curved** volcanic island chain (not confetti islands)
- [ ] Kharzhan west coast facing East Ocean is **not** a mirror of Aurelian's Andes
- [ ] Farreach has a believable **collision** range, not a decorative stripe
- [ ] Northern Aurelian shows glacial lake chaos
- [ ] No mountain belt without a plate story in `05-planetary-formation.md`
- [ ] First pass unlabeled; upscale doesn't invent a fifth continent

## Label pass (after upscale)

**Continents / landmasses:** Aurelian, Kharzhan, Farreach; Solmar *(island-continent)*  
**Oceans:** West Ocean, East Ocean  
**Optional process labels (small):** Highspine Cordillera, East Gulf, Solmar Arc, Farreach Suture  

On-stage countries after coastlines lock. Footnote improbables (Mirrin, Three-Passes, Lateran Quarter, Neutral Bend, …) only on detailed political zooms — see `07-pseudo-histories.md`.

## Exports

Save master as `maps/exports/world-master.png`. Map coastlines then beat prose; update formation doc only if you consciously revise geology.
