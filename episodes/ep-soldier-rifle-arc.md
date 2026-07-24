# Soldier systems — Rifle arc (worked example)

> **[WORKED EXAMPLE]** — shows how one "item" becomes a multi-episode deep dive.
> **Source design doc:** [`designs/soldier-systems/infantry-rifle.md`](../designs/soldier-systems/infantry-rifle.md)
> **Program id:** `rifle-std-1`
> **Data:** `data/programs.csv`, `cost-estimates.csv`, `bom.csv`, `production-lines.csv`

This replaces the old single-episode `ep04` surface treatment. Depth is the point.

---

## Part 1 — The legacy rifle problem (~12–15 min)

**Status:** outline  
**Focus:** requirement, legacy baseline, why optics-only is not a generational jump

### Cold open
"We still issue rifles designed before most of our corporals were born. The wake-up war did not invent infantry — it made our inventory look like a museum with a logistics problem."

### Beats
- Show the mixed 80s–90s inventory and dual-caliber risk
- Wake-up war lesson: optics + ammo + training, not brand mystique
- Requirement statement from the design doc
- Preview: we will design the line, not just pick a catalog item

### Canon / data
- No CSV numbers required yet beyond program existence

---

## Part 2 — Options (import vs retrofit vs license vs clean-sheet) (~15–18 min)

**Status:** outline  
**Focus:** steelman all four options; introduce industrial path as a first-class axis

### Cold open
"The best rifle you can buy off a foreign shelf is not the best rifle for a country rebuilding its plants."

### Beats
- Option A–D from the design doc, each at its strongest
- Introduce the rule: bridges are allowed; forever-imports as end states are not
- Leave the audience unsure — decision comes after materials/line/cost

---

## Part 3 — Materials and BOM (~12–15 min)

**Status:** outline  
**Focus:** walk `data/bom.csv` for `rifle-std-1`

### Cold open
"Before we argue brands, we argue aluminum, barrel steel, and polymer pellets."

### Beats
- On-screen table from CSV: structure vs barrel vs furniture
- Domestic vs import share
- 180-day stockpile on polymer/finish chemicals
- Hook: the barrel cell will decide our annual rate

### Data on screen
- Rows from `data/bom.csv`

---

## Part 4 — The assembly line (~15–20 min)

**Status:** outline  
**Focus:** walk `data/production-lines.csv`; bottleneck forge

### Cold open
"Our entire rifle future bottlenecks on one cold-hammer forge cell."

### Beats
- Station-by-station flow (1→9)
- Cycle times → why ~40k/year is the design rate at two shifts
- Workforce and training lead for second shift
- Surge options: second forge vs live with the cap
- Retool of legacy plant vs greenfield (cost implication)

### Data on screen
- `production-lines.csv` stations; highlight `bottleneck=true`

---

## Part 5 — Cost model and decision (~15–18 min)

**Status:** outline  
**Focus:** `data/cost-estimates.csv` + final decision

### Cold open
"Sixty million project-dollars before the first rifle. Then the unit cost falls off a cliff — if we actually learn."

### Beats
- Tooling year vs ramp vs rate (table from CSV)
- Compare to premium import unit cost
- License clauses that must be true for the industrial story to work
- Decision: Option C + training-stock bridge
- Confidence tags (`study-grade`) — honesty on camera

### Data on screen
- All `rifle-std-1-*` cost rows

---

## Part 6 — Fielding and what this unlocks (~10–12 min)

**Status:** outline  
**Focus:** second-order effects; optics program hook; ammo surge hook

### Cold open
"The rifle was never the expensive half of modern infantry. It was the permission slip."

### Beats
- Fielding schedule by cohort (active → reserve)
- Optics program now has a rail standard
- Ammo and magazine logistics simplification
- Tease next soldier-systems episode (optics or armor) or return to logistics ammo surge

---

## Production notes (arc-wide)

- **Visuals:** CSV-driven tables/charts (website-ready later); plant floor diagram; bottleneck callout
- **Canon:** D-0001
- **Rule:** if a number changes, change the CSV first, then re-export graphics
