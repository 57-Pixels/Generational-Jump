# Costing Method

> How we estimate costs so episode numbers stay consistent and a future website can trust `data/cost-estimates.csv`.

## Units

- **Currency:** project-dollars (`PD`) ≈ 2025 USD purchasing power. Not real money; treat the relative scale as serious.
- **Unit cost:** recurring cost to produce one acceptably finished article at the stated annual quantity (materials + labor + scrap + factory opex allocation). **Does not** include R&D or one-time tooling unless the row's `phase` says otherwise.
- **Tooling / facility capex:** one-time (or refresh) capital. Put these in their own year rows with `quantity=0` when needed.
- **Annual opex:** keep-the-lights-on cost of the line that year (salaries, energy, maintenance contracts) even between batches.

## Learning curve (default)

Unless a design doc argues otherwise:

- First production year unit cost is **~1.5×** steady-state rate cost.
- Reach design rate in **3 years** for small arms / trucks; **5–8 years** for armor / aircraft / ships.
- Scrap starts high and falls; encode the effect in unit_cost, not a separate column (keep the CSV schema stable).

## Confidence tags (in `notes`)

| Tag | Meaning |
| --- | --- |
| `order-of-magnitude` | ±3× — directional only |
| `study-grade` | ±50% — good enough to compare options |
| `quote-analogue` | ±25% — anchored to a real-world analogue adjusted for our labor/materials |
| `line-model` | ±15% — derived from a filled `production-lines.csv` for that program |

Worked examples should aim for `study-grade` or better. Never put a number on screen in an episode at lower confidence than the CSV admits.

## What we deliberately do not model (yet)

- Inflation / PD deflators over decades
- Full life-cycle cost including demilitarization
- Detailed vendor profit margins

Add columns later only as a versioned schema change logged in `decisions-log.md`.
