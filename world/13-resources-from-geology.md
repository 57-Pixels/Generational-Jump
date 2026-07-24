# Resources from Geology

> **Rule:** deposits are **earned by deep-time process**, not painted where a story wants a mine.  
> **On the map:** every important geological resource type below must appear as deposit markers for each seed.  
> Principles: [`12-worldbuilding-principles.md`](12-worldbuilding-principles.md) · Formation: [`05-planetary-formation.md`](05-planetary-formation.md) · Sim: [`../maps/generator/deeptime/`](../maps/generator/deeptime/)

## Why this sits on plates

Industry, arms plants, chips, and wartime shortages only feel fair if **fuels, metals, and strategic minerals** sit where geology put them. Same stack that builds continents builds the resource map.

## Important geological catalog (must map)

| ID | Resource | Geologic cause (process) |
| --- | --- | --- |
| `coal` | Coal | Interior / foreland basins, wet-enough paleo settings |
| `oil_gas` | Oil & gas | Passive shelves, passive margins, foreland traps |
| `iron` | Iron | Craton cores / BIF-analogue; some arc skarns |
| `copper` | Copper (porphyry) | Magmatic arcs above subduction |
| `tin_tungsten` | Tin / tungsten | Suture flanks, granitic / accretionary belts |
| `gold` | **Gold** | Hydrothermal arc/suture + placer-ish lowlands |
| `silver_base` | Silver / base-metal | Arc and suture hydrothermal |
| `rare_earths` | **Rare earths** | Craton alkaline intrusions + heavy-mineral sands |
| `uranium` | Uranium | Sedimentary basins + some igneous |
| `silica_hp` | **High-purity silica** | Clean quartz sands (passive coasts) + quartzite on quiet craton |
| `bauxite` | Bauxite (aluminum) | Wet tropical weathering on continental crust |
| `nickel_pgm` | Nickel / PGM | Craton-margin mafic–ultramafic / greenstone analogue |
| `lithium` | Lithium | Arid brine basins + pegmatite belts on sutures |
| `phosphates` | Phosphates | Shelf / passive-margin phosphorites |
| `potash` | Potash | Evaporitic interior basins |

Timber / hydro / fish remain strategic but are **climate/coast** layers, not this ore catalog.

**Forbid:** a strategic mine with no plate/basin/arc story; “every country has everything”; oil under a random mountain with no sediment basin.

## Map outputs

| File | Content |
| --- | --- |
| `world-resources.png` | Atlas color + deposit markers |
| `world-resources.geojson` | Point features (`resource`, `grade`, `intensity`) |
| `world-meta.json` → `resources` | Catalog, legend, counts |

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
