# Series Outline

> **Status:** living outline for a **long, in-depth** series.
> This is design work — platforms, materials, assembly lines, and costs — not surface-level "we'd buy X" listicles.
> Quantitative claims on screen must come from `data/*.csv`.

## Series in one sentence

A country with an 80s–90s military watches a modern war elsewhere, then executes a **full-domain generational jump** — and we design the equipment *and* the factories in depth, from the boring foundations to the exciting platforms.

## Shape

**Act 0 — Why jump (short):** wake-up war, legacy force, mandate, budget, industrial spine.

**Acts I→N — Domain arcs (long):** each domain is a **multi-episode arc**, boring → exciting overall:

1. Industry & costing discipline (how we estimate)
2. Logistics
3. Soldier systems
4. C4ISR
5. Land
6. Air defense
7. Air force
8. Navy
9. Stress tests / revisiting bad decisions

Inside a domain arc, typical episode pattern:

1. Requirement & legacy baseline  
2. Mechanism / architecture options  
3. Materials & BOM  
4. Production line & workforce  
5. Cost model & decision  
6. Fielding & second-order effects  

Not every item needs all six on camera — but the **design doc must contain them** before the decision episode airs.

## Episode index (starter)

Numbers will drift as arcs expand. Treat IDs as stable; order as preferred default.

| ID | Working title | Source | Status |
| --- | --- | --- | --- |
| A0-01 | The Wake-Up Call | `world/00` | Not started |
| A0-02 | The 80s–90s Force We Actually Have | `world/01` | Not started |
| A0-03 | Money, Plants, and Project-Dollars | `world/03`, `industry/*`, `data/README.md` | Not started |
| I-01 | How We Cost a Weapon | `industry/01-costing-method.md` | Not started |
| L-arc | Logistics arc (trucks, fuel, ammo, maintenance) | `designs/logistics/` | Not started |
| S-arc | Soldier systems arc | `designs/soldier-systems/` | Rifle arc outlined |
| S-rifle | Rifle deep-dive (multi-part) | [`ep-soldier-rifle-arc.md`](ep-soldier-rifle-arc.md) | **Outlined (worked example)** |
| C-arc | C4ISR arc | `designs/c4isr/` | Not started |
| G-arc | Land combat arc | `designs/land/` | Not started |
| AD-arc | Air defense arc | `designs/air/` | Not started |
| AF-arc | Air force arc | `designs/air/` | Not started |
| N-arc | Navy arc | `designs/sea/` | Not started |
| Z-arc | Stress tests against scenarios | `threat-analysis/` | Not started |

## Standing rules

- Cold open on a design problem or counterintuitive cost/line fact.
- Steelman rejected options.
- No number on screen unless it exists in `data/` (or is clearly labeled scenario fiction).
- Factory episodes are first-class, not B-roll.
- When canon changes, update CSVs first, then prose.
