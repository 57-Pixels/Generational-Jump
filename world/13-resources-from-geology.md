# Resources from Geology

> **Rule:** deposits are **earned by deep-time process**, not painted where a story wants a mine.  
> **On the map:** every important geological resource type below must appear as deposit markers for each seed.  
> Principles: [`12-worldbuilding-principles.md`](12-worldbuilding-principles.md) · Formation: [`05-planetary-formation.md`](05-planetary-formation.md) · Sim: [`../maps/generator/deeptime/`](../maps/generator/deeptime/)

## Why this sits on plates

Industry, arms plants, chips, and wartime shortages only feel fair if **fuels, metals, and strategic minerals** sit where geology put them. Same stack that builds continents builds the resource map.

## Important geological catalog (must map)

| Families | Included resources | Geologic cause (process) |
| --- | --- | --- |
| Fuels | Coal, petroleum systems, helium-bearing gas | Wetland/source-rock history + burial, maturity, reservoir, seal and trap |
| Ferrous/alloy | BIF iron, manganese, Ti–V magnetite, chromium/PGM | Ancient cratons, shelves, mafic/ultramafic intrusions |
| Base metals | Porphyry Cu–Mo, sediment Cu–Co, VMS Cu–Zn, Sedex/MVT Zn–Pb, Ni–Cu | Arcs, rifts, brine flow, carbonate and magmatic systems |
| Precious/specialty | **Gold**, silver/byproducts, antimony, Sn/W | Hydrothermal arc/suture, evolved granite and exhumation |
| Nuclear/critical | Uranium, **REE/Nb carbonatite**, ionic-clay HREE | Stable craton, redox systems, alkaline intrusions and weathering |
| Battery | Lithium brine, LCT pegmatite, nickel laterite, graphite | Closed arid basins, collision granite, tropical weathering, metamorphism |
| Agriculture/chemical | Phosphorite, potash, fluorspar | Upwelling shelves, restricted evaporite basins, rift/alkaline hydrothermal |
| Electronics | **High-purity quartz** | Rare hydrothermal/pegmatite/high-grade quartz with ppm impurity qualification |
| Heavy minerals | Titanium, zirconium/hafnium, monazite/REE sands | Source rock + coastal reworking |

Timber / hydro / fish remain strategic but are **climate/coast** layers, not this ore catalog.

Common aggregate, sand/gravel, limestone, brick clay, ordinary silica sand, gypsum, salt, and dimension stone are **availability rasters**, not arbitrarily capped point deposits. High-purity quartz is not ordinary beach sand.

**Forbid:** a strategic mine with no plate/basin/arc story; “every country has everything”; oil under a random mountain with no sediment basin.

## Map outputs

| File | Content |
| --- | --- |
| `world-resources.png` | Atlas color + deposit markers |
| `world-resources.geojson` | Provinces with grade, resource, 2025 reserve, depth, accessibility, processing and byproducts |
| `world-meta.json` → `resource_counts` | Variable counts by deposit class |

Viewer toggle: **Resources** (default on).

```bash
cd maps/generator && python3 -m deeptime --seed 42
```

## Pipeline slot

```
deep-time plates → elevation / orogeny / crust age / basins
  → resource prospect intensities
  → discrete deposits (all catalog types on map)
  → who can industrialize / who imports
  → arms-market and wartime surge constraints
```

## Series use

- Design docs: “why we import X” should point at geology or a named trade patron.
- Odd-ones-out: some free cities exist *because* of a deposit or the port that ships it.
- Chip / glass / solar supply → **high-purity silica**; magnets / sensors → **REE**; bullion / electronics → **gold**.
