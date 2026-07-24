# Standard Infantry Rifle Program

> **[WORKED EXAMPLE]** — demonstrates deep operational + industrial design with CSV-backed costs. Fully replaceable.
>
> **Domain:** soldier-systems
> **Status:** decided (example)
> **Program id:** `rifle-std-1`
> **Drives episodes:** [`episodes/ep-soldier-rifle-arc.md`](../../episodes/ep-soldier-rifle-arc.md)
> **Decision logged:** decisions-log.md, D-0001

## A. Operational design

### 1. Requirement

The wake-up war showed infantry fights decided by optics, networking, and ammo supply — not by parade-ground rifle brands. Our active force and reserves still field mixed 80s–90s service rifles, often without a serious optic rail path. The generational jump needs **one modern standard rifle**, produced on a **domestic line**, in enough quantity to re-equip the force and keep wartime attrition filled.

- **Traces to scenario:** [`threat-analysis/scenarios/01-eastern-invasion.md`](../../threat-analysis/scenarios/01-eastern-invasion.md) requirement #2
- **Legacy baseline:** mixed late-Cold-War analogue rifles; iron sights common in reserve units; dual-caliber logistics risk
- **If we don't:** we modernize tanks and jets on top of an infantry force stuck a generation behind — hollow jump
- **Quantity / timeline:** ~250,000 rifles over ~8–10 years (active + reserve + training + attrition float), first units year 2 after tooling

### 2. Constraints

| Constraint | Value | Source |
| --- | --- | --- |
| Affordability | Must fit soldier-systems slice of Modernization Act money; tooling is front-loaded | `world/03`, `data/cost-estimates.csv` |
| Industry | Domestic plant can build small arms; license preferred over clean-sheet | `industry/00-overview.md` |
| Climate | -25°C to hot dusty summers; must run dirty | `world/01-our-nation.md` |
| Users | Conscripts/reserves fire little annually — ergonomics and training simplicity matter | `world/01-our-nation.md` |
| Suppliers | Wartime-continuation and spare-part rights mandatory in any license | `world/04-alliances-and-diplomacy.md` |

### 3. Options considered

#### Option A — Import premium current-gen rifles

- **Analogue:** top-tier Western AR-pattern
- **Industrial path:** forever-import
- **Cost:** ~2,500 PD/unit landed; near-zero domestic tooling; spares seaborne
- **Fit:** fails the "build to own" modernization rule and SLOC risk

#### Option B — Keep legacy + buy optics only

- **Analogue:** rail retrofit kits on 80s–90s rifles
- **Industrial path:** minimal
- **Cost:** cheap upfront
- **Fit:** not a generational jump; barrels, ergonomics, and parts age out during the Act years

#### Option C — License-build modern design on a retooled domestic line

- **Analogue:** licensed modern service rifle (BREN/FN-class deal)
- **Industrial path:** license + retool existing small-arms plant (see §8)
- **Cost:** see `data/cost-estimates.csv` (`rifle-std-1-*`); ~920 PD/unit at rate; ~60M PD tooling+facility upfront
- **Fit:** matches full-jump doctrine and series industrial depth

#### Option D — Clean-sheet domestic rifle

- **Industrial path:** multi-year R&D before production
- **Fit:** sovereignty theater; burns engineers needed for drones/C4ISR

### 4. Decision and rationale

**Option C — license-build, domestic line, time-boxed surplus bridge for training stocks only.**

Chain: full generational jump requires replacing the legacy rifle; wake-up war and SLOC risk forbid forever-import; we can manufacture but should not redesign; Modernization Act can fund tooling if unit cost falls to rate (~920 PD) by year 5. License must include wartime continuation and full spare-part production.

### 5. Rejected alternatives

- **"Just buy the best foreign rifle."** — Best on the range; worst as an industrial end state for this series and this country's SLOC exposure.
- **"Optics on old rifles is the modern lesson."** — Optics are mandatory *and* insufficient; the jump replaces the weapon system, not only accessories.
- **"Design our own."** — Making ≠ designing. Spend design talent where the wake-up war actually moved the frontier (drones, AD, networking).

### 6. Second-order effects

- Single caliber across the force
- Optics program can assume a stable rail standard
- Plant workforce becomes a national asset for later machine-gun / precision-rifle lines
- Follow-ons: optics, body armor, ammo surge cells (`designs/logistics/`, `industry/`)

---

## B. Industrial design

### 7. Materials and BOM

Full BOM: `data/bom.csv` where `program_id=rifle-std-1`.

**Critical import / mixed lines:** polymer pellets (`stk-01`), finish chemicals (`fin-01`). Everything structural and barrel-related is targeted domestic.

**Stockpile note:** polymer and finish chemicals — 180-day stockpile at rate before relying on wartime imports (`industry/02-materials.md`).

### 8. Production line

Stations: `data/production-lines.csv` where `program_id=rifle-std-1`.

- **Plant:** retool existing small-arms complex (not greenfield)
- **Design rate:** ~40,000 finished rifles/year at two shifts
- **Bottleneck:** station 2 — barrel cold-hammer forge (`rifle-std-1-s02`). Surge means a second forge cell (~15M PD) or accepting rate cap
- **Workforce:** ~33 operators/shift on the named stations × 2 shifts, plus QC/maintenance overhead (~90–110 people total at rate)
- **Training lead:** ~9 months to stand up second-shift competence on forge and proof

### 9. Cost model

Method: `industry/01-costing-method.md`. Rows: `data/cost-estimates.csv` for `rifle-std-1`.

| Year | Phase | Qty | Unit cost (PD) | Capex notes |
| --- | --- | --- | --- | --- |
| 2026 | tooling_setup | 0 | — | 42M tooling + 18M facility |
| 2027 | ramp | 12,000 | 1,450 | learning curve |
| 2028 | ramp | 28,000 | 1,180 | |
| 2029+ | rate | 40,000 | ~920–980 | steady state |

**Confidence:** `study-grade` overall; bottleneck forge capex closer to `quote-analogue`.

**Headline for episodes:** ~60M PD to stand the line up; under 1,000 PD per rifle once at rate; premium import path is ~2.5× unit cost *and* builds no plant.

### 10. Data checklist

- [x] `data/programs.csv`
- [x] `data/bom.csv`
- [x] `data/production-lines.csv`
- [x] `data/cost-estimates.csv`
- [x] `decisions-log.md` D-0001
