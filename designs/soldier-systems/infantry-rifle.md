# Standard Infantry Rifle Program

> **[WORKED EXAMPLE]** — demonstrates the design reasoning with a light industry/cost note. Fully replaceable.
>
> **Domain:** soldier-systems
> **Status:** decided (example)
> **Program id:** `rifle-std-1`
> **Drives episodes:** [`episodes/ep-soldier-rifle-arc.md`](../../episodes/ep-soldier-rifle-arc.md)
> **Decision logged:** decisions-log.md, D-0001

## 1. Requirement

The wake-up war showed infantry fights decided by optics, networking, and ammo supply — not by parade-ground rifle brands. Our active force and reserves still field mixed 80s–90s service rifles, often without a serious optic rail path. The generational jump needs **one modern standard rifle**, produced on a **domestic line**, in enough quantity to re-equip the force and keep wartime attrition filled.

- **Traces to scenario:** [`threat-analysis/scenarios/01-eastern-invasion.md`](../../threat-analysis/scenarios/01-eastern-invasion.md) requirement #2
- **Legacy baseline:** mixed late-Cold-War analogue rifles; iron sights common in reserve units; dual-caliber logistics risk
- **If we don't:** we modernize tanks and jets on top of an infantry force stuck a generation behind — hollow jump
- **Quantity / timeline:** ~250,000 rifles over ~8–10 years (active + reserve + training + attrition float), first units year 2 after tooling

## 2. Constraints

| Constraint | Value | Source |
| --- | --- | --- |
| Affordability | Must fit soldier-systems slice of Modernization Act money; tooling is front-loaded | `world/03`, `data/costs.csv` |
| Industry | Domestic plant can build small arms; license preferred over clean-sheet | `industry/README.md` |
| Climate | -25°C to hot dusty summers; must run dirty | `world/01-our-nation.md` |
| Users | Conscripts/reserves fire little annually — ergonomics and training simplicity matter | `world/01-our-nation.md` |
| Suppliers | Wartime-continuation and spare-part rights mandatory in any license | `world/04-alliances-and-diplomacy.md` |

## 3. Options considered

#### Option A — Import premium current-gen rifles

- **Analogue:** top-tier Western AR-pattern
- **Build path:** forever-import
- **Rough cost:** ~2,500 PD/unit landed; near-zero domestic tooling; spares seaborne
- **Fit:** fails the "build to own" preference and SLOC risk

#### Option B — Keep legacy + buy optics only

- **Analogue:** rail retrofit kits on 80s–90s rifles
- **Build path:** minimal
- **Rough cost:** cheap upfront
- **Fit:** not a generational jump; barrels, ergonomics, and parts age out during the Act years

#### Option C — License-build modern design on a retooled domestic line

- **Analogue:** licensed modern service rifle (BREN/FN-class deal)
- **Build path:** license + retool existing small-arms plant
- **Rough cost:** `data/costs.csv` (`rifle-std-1`); ~1,000 PD/unit at scale; ~60M PD setup
- **Fit:** matches the full-jump preference to build high-volume items at home

#### Option D — Clean-sheet domestic rifle

- **Build path:** multi-year R&D before production
- **Fit:** sovereignty theater; burns engineers needed for drones/C4ISR

## 4. Decision and rationale

**Option C — license-build, domestic line, time-boxed surplus bridge for training stocks only.**

Chain: full generational jump requires replacing the legacy rifle; wake-up war and SLOC risk forbid forever-import; we can manufacture but should not redesign; Modernization Act can fund tooling if unit cost falls to rate (~920 PD) by year 5. License must include wartime continuation and full spare-part production.

## 5. Rejected alternatives

- **"Just buy the best foreign rifle."** — Best on the range; worst as an industrial end state for this series and this country's SLOC exposure.
- **"Optics on old rifles is the modern lesson."** — Optics are mandatory *and* insufficient; the jump replaces the weapon system, not only accessories.
- **"Design our own."** — Making ≠ designing. Spend design talent where the wake-up war actually moved the frontier (drones, AD, networking).

## 6. Second-order effects

- Single caliber across the force
- Optics program can assume a stable rail standard
- Plant workforce becomes a national asset for later small-arms programs
- Follow-ons: optics, body armor, ammo (`designs/logistics/`)

## 7. Industry (rough)

- **Build path:** license a proven modern design and build it on the retooled existing small-arms plant (not greenfield). Bridge with a small surplus buy for *training stocks only* until first deliveries.
- **Key materials:** barrel steel and receiver aluminum (domestic, fine); polymer pellets for furniture and some finish chemicals (imported — worth a modest stockpile). Nothing here is a hard chokepoint.
- **Rough cost:** ~60M PD to set up the line, ~1,000 PD per rifle at scale, ~310M PD program total for 250k rifles. Confidence `rough`. The premium import path is ~2.5× the unit cost and builds no plant. Numbers live in `data/costs.csv` (`rifle-std-1`).

*Decision logged: `decisions-log.md` D-0001.*
