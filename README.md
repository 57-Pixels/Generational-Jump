# Fantasy Military Design Project

A long-form **defense industrial design** project set in a fictional world at **2025 technology, no magic**. The country starts with an **1980s–1990s military**. A major conventional war **elsewhere** is the wake-up call. The mandate: a **full generational jump across every domain** — land, air, sea, C4ISR, soldier systems, logistics — designing not only the equipment but the **materials, assembly lines, and costs**.

This repository is the source of truth for a deep video series. Markdown holds reasoning; **CSV holds numbers** a future website can load directly.

## How the documents connect

```
world/  →  threat-analysis/  →  doctrine/  →  industry/ + data/*.csv  →  designs/  →  episodes/
(constraints)   (scenarios)     (jump plan)   (factories & costs)      (programs)   (videos)
```

## Reading order

1. [`world/00-world-overview.md`](world/00-world-overview.md) — wake-up war, tech baseline, jump mandate
2. [`world/01-our-nation.md`](world/01-our-nation.md) — geography (all domains), people, **legacy 80s–90s force**
3. [`world/02-neighbors-and-threats.md`](world/02-neighbors-and-threats.md)
4. [`world/03-economy-and-industrial-base.md`](world/03-economy-and-industrial-base.md)
5. [`world/04-alliances-and-diplomacy.md`](world/04-alliances-and-diplomacy.md)
6. [`industry/00-overview.md`](industry/00-overview.md) + [`data/README.md`](data/README.md)
7. [`threat-analysis/00-threat-overview.md`](threat-analysis/00-threat-overview.md)
8. [`doctrine/00-national-defense-strategy.md`](doctrine/00-national-defense-strategy.md)
9. `designs/` — one deep design doc per program (ops + industrial halves)
10. [`episodes/00-series-outline.md`](episodes/00-series-outline.md)

## Directory guide

| Path | Contents |
| --- | --- |
| `world/` | World bible and legacy-force baseline |
| `industry/` | Plants, costing method, materials strategy |
| `data/` | **Website-ready CSVs**: programs, costs, BOM, production lines |
| `threat-analysis/` | Ranked threats and scenarios |
| `doctrine/` | Generational-jump strategy |
| `designs/logistics/` | Trucks, fuel, ammo, maintenance |
| `designs/soldier-systems/` | Rifles, optics, armor, kit |
| `designs/c4isr/` | Comms, networks, ISR |
| `designs/land/` | Artillery, armor, AT |
| `designs/air/` | Air defense and air force |
| `designs/sea/` | Navy |
| `episodes/` | Long-form series outline and arcs |
| `templates/` | Design doc, manufacturing appendix, episode, scenario |
| `decisions-log.md` | Canon log |

## Series order (boring → exciting)

Industry/costing → logistics → soldier systems → C4ISR → land → air defense → air force → navy → stress tests.

Each domain is a **multi-episode arc** (requirement → mechanism → materials → line → cost → fielding).

## Workflow for a new program

1. Trace the requirement to a scenario (or to the jump mandate).
2. Add a row to [`data/programs.csv`](data/programs.csv).
3. Copy [`templates/design-doc.md`](templates/design-doc.md); fill operational **and** industrial halves.
4. Fill `bom.csv`, `production-lines.csv`, `cost-estimates.csv`.
5. Optional deep industrial writeup via [`templates/manufacturing-appendix.md`](templates/manufacturing-appendix.md).
6. Log the decision in [`decisions-log.md`](decisions-log.md).
7. Outline the episode arc under `episodes/`.

## Status labels

- **[STARTER SUGGESTION]** — proposed world defaults; not canon until logged.
- **[WORKED EXAMPLE]** — demonstrates depth (rifle program + CSV + multi-part arc); replaceable.

## Worked example

- Design: [`designs/soldier-systems/infantry-rifle.md`](designs/soldier-systems/infantry-rifle.md)
- Data: `rifle-std-1` rows in `data/*.csv`
- Episodes: [`episodes/ep-soldier-rifle-arc.md`](episodes/ep-soldier-rifle-arc.md)
