# Resources from Geology

> **Rule:** deposits are **earned by deep-time process**, not painted where a story wants a mine.  
> Principles: [`12-worldbuilding-principles.md`](12-worldbuilding-principles.md) · Formation: [`05-planetary-formation.md`](05-planetary-formation.md) · Sim: [`../maps/generator/deeptime/`](../maps/generator/deeptime/)

## Why this sits on plates

Industry, arms plants, and wartime shortages only feel fair if **steel, copper, oil, rare earths, coal, uranium** sit where geology put them. Same stack that builds continents builds the resource map.

Detail still scales with need: coarse province-level for most episodes; fine deposits when a design doc or scenario cares.

## Deposit logic (Earth roles → this world)

| Resource family | Typical geologic cause | Where to expect (process words) |
| --- | --- | --- |
| **Coal** | Carboniferous-analogue basins, swampy shelves | Stable continental interiors / old foreland basins |
| **Oil & gas** | Source rock + trap + seal; often passive-margin / gulf sediments | East Gulf–type embayments, wide shelves, foreland basins |
| **Iron** | Banded iron / craton + lateritic / sedimentary iron | Old craton margins; some cordillera skarns |
| **Copper / porphyry** | Magmatic arcs above subduction | Highspine / Solmar arc belts |
| **Tin / tungsten / etc.** | Granitic belts, accretionary margins | Outer accretionary belts, suture flanks |
| **Precious metals** | Hydrothermal along faults/arcs; placers downstream | Arc/suture highlands → river placers on plains |
| **Rare earths / specialty** | Alkaline complexes, heavy-mineral sands, specific igneous | Craton intrusions; select coastal sands |
| **Uranium** | Roll-fronts in sediments; some igneous | Interior basins; named only when a program needs it |
| **Timber / hydro / fish** | Climate + relief + coast (not “ore,” still strategic) | Windward coasts, highspine rivers, shelves |

**Forbid:** a strategic mine with no plate/basin/arc story; “every country has everything”; oil under a random mountain with no sediment basin.

## Pipeline slot

```
deep-time plates → elevation / orogeny / crust age / basins
  → resource prospect map (coarse)
  → who can industrialize / who imports
  → arms-market and wartime surge constraints
```

v1 deeptime exports height + plates; **resource layer is next** (derive from `orogeny`, continental crust, passive-margin shelves, suture). Reference campaign can hand-annotate from `05` until the layer ships.

## Series use

- Design docs: “why we import X” should point at geology or a named trade patron.
- Odd-ones-out: some free cities exist *because* of a deposit or the port that ships it.
- Maravic / Eastmarch: local ore/fuel scarcity is a logistics beat, not a surprise cheat.
