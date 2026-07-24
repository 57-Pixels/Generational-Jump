# [Equipment name / program name]

> **Domain:** land / air / sea / c4isr / soldier-systems / logistics
> **Status:** draft / decided / superseded by [link]
> **Drives episode:** [link to episode doc, or "not yet scheduled"]
> **Decision logged:** [link to decisions-log.md entry, or "pending"]

## 1. Requirement

What operational problem does this solve? State it as a problem, not as a product ("we cannot stop armor crossing the eastern plain," not "we need tanks").

- **Traces to scenario(s):** [link to threat-analysis/scenarios/ doc(s)]
- **What happens if we don't solve it:** [concrete consequence in the scenario]
- **Quantity and timeline:** roughly how many, fielded by when, and why that deadline

## 2. Constraints

Every constraint must link to the world bible. If a constraint isn't written down in `world/`, either write it there first or don't use it here.

| Constraint | Value | Source |
| --- | --- | --- |
| Budget ceiling for this program | | `world/03-economy-and-industrial-base.md` |
| Domestic industry capability | can build / can assemble under license / must import | `world/03-economy-and-industrial-base.md` |
| Geography and climate it must operate in | | `world/01-our-nation.md` |
| Manpower and training pipeline | | `world/01-our-nation.md` |
| Import restrictions / who will sell to us | | `world/04-alliances-and-diplomacy.md` |

## 3. Options considered

Use real-world-analogous options with honest trade-offs. Three to five options is the sweet spot. Include at least one cheap option and at least one "gold-plated" option, even if only to reject them.

### Option A: [name]

- **Real-world analogue:** [what this is modeled on]
- **Rough unit cost and sustainment cost:**
- **Pros:**
- **Cons:**
- **Fit with our constraints:**

### Option B: [name]

(same structure)

### Option C: [name]

(same structure)

## 4. Decision and rationale

State the pick in one sentence, then the reasoning. The rationale must reference the constraints table — if the decision would be the same for any country, the rationale is not done yet.

## 5. Rejected alternatives

Why the *obvious* choices were wrong **for this country**. This is the most important section for the video: viewers will arrive with "why not just buy X?" already in their heads. Answer each one directly.

- **"Why not just [obvious option]?"** — [answer grounded in constraints]
- **"Why not just [second obvious option]?"** — [answer]

## 6. Second-order effects

What this decision drags along with it:

- **Logistics tail:** spares, ammunition types, fuel, transport requirements
- **Training burden:** who has to learn what, and how long that takes
- **Doctrine changes:** what tactics or org structure must change to use this well
- **Industrial effects:** jobs, license terms, dependence created or removed
- **Follow-on decisions triggered:** [links to future design docs this creates the need for]
