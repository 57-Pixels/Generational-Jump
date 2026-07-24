# [Equipment name / program name]

> **Domain:** logistics / soldier-systems / c4isr / land / air / sea
> **Status:** draft / decided / superseded by [link]
> **Program id:** [must match `data/programs.csv`]
> **Drives episode(s):** [link(s)]
> **Decision logged:** [link to decisions-log.md entry, or "pending"]

The focus is the **design reasoning** below. The industry section is deliberately short — a rough build plan and rough cost, often AI-assisted. Don't over-invest there.

## 1. Requirement

What operational problem does this solve? State it as a problem, not a product.

- **Traces to scenario(s):** [link]
- **Legacy baseline:** what 80s–90s system this replaces (or supplements)
- **What happens if we don't solve it:**
- **Quantity and timeline:** how many, fielded by when

## 2. Constraints

Every constraint links to the world bible. If it isn't written down, write it there first.

| Constraint | Value | Source |
| --- | --- | --- |
| Budget / affordability | | `world/03`, `data/costs.csv` |
| Industrial capability | design / license-build / assemble / import | `industry/README.md` |
| Geography and climate | | `world/01-our-nation.md` |
| Manpower and training | | `world/01-our-nation.md` |
| Import / supplier politics | | `world/04-alliances-and-diplomacy.md` |

## 3. Options considered

Three to five options. Include a cheap option and a gold-plated option. Steelman each.

### Option A: [name]

- **Real-world analogue:**
- **Build path:** import / license / domestic design
- **Rough cost:** (per-unit + setup; point at `data/costs.csv` once estimated)
- **Pros / cons / fit:**

### Option B / C / … — same structure

## 4. Decision and rationale

One sentence pick, then the chain from constraints → choice. Must be specific to *this* country.

## 5. Rejected alternatives

Answer "why not just X?" for the obvious objections. This section *is* the video argument.

## 6. Second-order effects

Logistics tail, training, doctrine, follow-on programs triggered.

## 7. Industry (rough — keep it short)

A few sentences each; this is a supporting thread, not a study.

- **Build path:** make / license+build / import, and roughly where (existing plant or new).
- **Key materials:** the handful that matter or carry supply risk (skip the full parts list). See `industry/README.md`.
- **Rough cost:** setup + per-unit + program total, with a confidence tag (`rough`/`study`/`firm`). Put the numbers in `data/costs.csv` (`program_id` = this program) and add a row to `data/programs.csv`.
