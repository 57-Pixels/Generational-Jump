# Standard Infantry Rifle Program

> **[WORKED EXAMPLE]** — this doc demonstrates the intended depth of the design-doc template using the starter world. Fully replaceable once canon changes.
>
> **Domain:** soldier-systems
> **Status:** decided
> **Drives episode:** [`episodes/ep04-infantry-rifle.md`](../../episodes/ep04-infantry-rifle.md)
> **Decision logged:** decisions-log.md, entry D-0001

## 1. Requirement

We are building a mobilization army: ~35,000 active troops but a wartime force of 150,000+ within weeks (strategic task 3, `doctrine/00-national-defense-strategy.md`). Every one of those people needs a rifle, ammunition for it, and spare parts — **from a supply chain that keeps working when the port is closed and import approvals are frozen**.

- **Traces to scenario:** [`threat-analysis/scenarios/01-eastern-invasion.md`](../../threat-analysis/scenarios/01-eastern-invasion.md), requirement #5.
- **What happens if we don't solve it:** reservists muster at depots and receive worn 1960s-analogue rifles in a different caliber from active forces, splitting our wartime ammunition logistics in two at the worst possible moment.
- **Quantity and timeline:** 180,000 rifles (wartime force + attrition float + territorial defense) over 8 years, prioritizing active units and first-line reserves in the first 3.

## 2. Constraints

| Constraint | Value | Source |
| --- | --- | --- |
| Budget ceiling for this program | ~$40M/year sustained (4% of the ~$1.0B annual procurement budget) | `world/03-economy-and-industrial-base.md` |
| Domestic industry capability | Can design and build small arms and small-arms ammunition domestically | `world/03-economy-and-industrial-base.md` |
| Geography and climate | Continental: -25°C winters, dust in summer, six weeks of mud; must run dirty | `world/01-our-nation.md` |
| Manpower and training | Conscript/reserve force; most users fire a few hundred rounds a year, not thousands | `world/01-our-nation.md` |
| Import restrictions | Western current-generation smallarms available but with end-use strings; port blockade cuts seaborne resupply | `world/04-alliances-and-diplomacy.md` |

## 3. Options considered

### Option A: Buy current-generation Western rifles off the shelf

- **Real-world analogue:** a modern AR-pattern rifle from a premium Western manufacturer (HK416/SCAR class).
- **Rough cost:** ~$2,500/rifle landed with accessories; ~$450M total before spares. Spares and warranty ties to the vendor.
- **Pros:** best-in-class reliability and ergonomics out of the box; instant credibility; no development risk.
- **Cons:** roughly double the program budget; every spare part crosses the ocean into our one blockadable port; end-use monitoring gives a foreign parliament a vote in our war.
- **Fit:** fails the survivability-of-supply constraint outright. This is the option that looks best on day 1 and worst on day 40.

### Option B: Second-tier surplus, immediately

- **Real-world analogue:** refurbished 1980s AK-pattern rifles from the surplus market.
- **Rough cost:** ~$400/rifle; ~$72M total. Almost free by program standards.
- **Pros:** instant fielding; famously mud-tolerant; ammunition cheap and globally available.
- **Cons:** a 40-year-old platform with no accessory rail path worth having; optics are now the difference in infantry fights (recent-war lesson) and bolting them onto surplus receivers is a losing retrofit; buying surplus builds no domestic capability and the surplus market itself dries up in every regional crisis.
- **Fit:** solves 2026's problem by recreating it in 2034.

### Option C: License-build a proven modern design domestically

- **Real-world analogue:** licensed production of a proven modern AR-pattern design (CZ BREN 2 / FN-class licensing deal) at our small-arms plant.
- **Rough cost:** ~$1,100/rifle at rate production after ~$60M in licensing, tooling, and line setup; ~$260M program total. First deliveries ~24 months in.
- **Pros:** modern platform with full optics/accessory architecture; **every rifle, spare part, and cartridge made inside our borders**; builds workforce and export potential; licensing from a non-aligned producer keeps the political strings short.
- **Cons:** 24-month gap before first deliveries; unit cost triple the surplus option; license terms need care (right to produce spares and to continue production in wartime must be explicit).
- **Fit:** the only option that satisfies the blockade constraint and the budget at the same time.

### Option D: Design a domestic rifle from scratch

- **Real-world analogue:** a national rifle program (the historical graveyard is well populated).
- **Rough cost:** unknowable, which is the answer. Development alone would eat years and $100M+ before the first production rifle.
- **Pros:** full sovereignty; national pride.
- **Cons:** we would spend a decade rediscovering solved problems while our actual asymmetric advantages (drones, software — `world/03`) starve for engineers; rifle design is a mature field where "new" buys almost nothing.
- **Fit:** sovereignty theater. Rejected hardest.

## 4. Decision and rationale

**License-build a proven modern rifle domestically (Option C), bridged by a small surplus buy (a slice of Option B) for territorial-defense units while the line spins up.**

The reasoning chain: the scenario says the port closes and we fight alone for 90 days (`world/04`); therefore the supply chain must live inside our borders; our industry can build small arms but not design them competitively (`world/03`); therefore we license. The budget (~$40M/year) fits Option C's profile and cannot fit Option A. The 24-month gap is covered by ~20,000 surplus rifles ($8M) that later cascade to training stocks. Caliber: the standard intermediate cartridge our plant already produces — commonality with existing stocks outweighs any ballistic argument for a boutique caliber, for a force of occasional shooters.

The license contract must include: full spare-part production rights, wartime production continuation clause, and export rights after year 5 (our negotiating leverage: the licensor wants access to our drone-software sector, per `world/03`).

## 5. Rejected alternatives

- **"Why not just buy the best Western rifle? Your soldiers deserve it."** — They deserve a rifle that still has spare parts in month three of a blockade. The premium import is a better rifle on the range and a worse one in this war. We buy weapons for our scenario, not for reviews.
- **"Why not just buy cheap surplus and spend the savings on drones?"** — Tempting, and half right — we *do* spend our real money on drones. But the rifle is a 30-year decision: surplus locks 180,000 soldiers to a platform that can't carry the optics that decide modern infantry fights, and the "savings" get eaten rebuilding this program in a decade under worse conditions.
- **"Why not design our own? You have the factories."** — We have factories that can *make* rifles, which is a different thing from an industry that can *design* one better than the mature market. Sovereignty comes from the production line and license terms, not from the nameplate.

## 6. Second-order effects

- **Logistics tail:** single rifle caliber across active, reserve, and territorial forces simplifies wartime distribution; magazine, cleaning kit, and armorer-tool standardization follows; surplus bridge rifles create a temporary dual-caliber pocket in territorial units (accepted, time-boxed).
- **Training burden:** one platform for conscripts and reserves shortens refresher training; armorer school needs standing up (~40 armorers/year); the optics decision (separate program) now has a stable mounting standard to build on.
- **Doctrine changes:** none directly, but universal optics-capable rifles enable the designated-marksman-per-squad concept the recent war validated.
- **Industrial effects:** ~300 jobs at the plant; establishes precision-manufacturing workforce that the artillery-barrel license retooling (`world/03`) can draw on; creates one new strategic site to defend and disperse.
- **Follow-on decisions triggered:** rifle optics program (`designs/soldier-systems/`, not yet written); body armor program; small-arms ammunition war-reserve sizing (`designs/logistics/`, not yet written).
