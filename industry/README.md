# Industry (lightweight)

> **Status:** deliberately thin. Industry **matters but is not the focus** of this project.
> Keep this rough. A rough cost and a rough build plan are enough — often AI-generated. Do **not** sink hours here; the design reasoning and the videos are the point.

## What we track (and nothing more)

For any hardware program, answer three quick questions — a few sentences each, not a study:

1. **Build path** — do we *make* it, *license* + build it, or *import* it? And roughly where (existing plant vs. new)?
2. **Key materials** — the handful of inputs that actually matter or carry supply risk (e.g. barrel steel, propellant, microelectronics). Skip the exhaustive parts list.
3. **Rough cost** — a setup/tooling number, a per-unit number, and a rough program total. Put the numbers in [`../data/costs.csv`](../data/costs.csv).

That's it. If a program needs deeper industrial analysis later, add it then — for one program, on demand.

## Cost conventions

- **Currency:** project-dollars (`PD`) ≈ 2025 USD. Fictional but treated seriously.
- **Unit cost:** rough cost to build one at scale (materials + labor + overhead). Ignore learning curves and inflation unless it changes a decision.
- **Setup cost:** one-time tooling/facility spend to stand the line up.
- **Confidence:** tag each number `rough` (gut/AI estimate), `study` (compared options), or `firm` (anchored to a real-world analogue). Most numbers here will be `rough`, and that's fine — just say so on camera.

## Materials note (starter)

> **[STARTER SUGGESTION]**

Likely national supply risks to keep in mind, not to model in depth: propellants/explosives, microelectronics, and jet-engine hot-section metals are the usual import chokepoints; structural metals and small arms are domestically achievable. Prefer building capacity for high-consumption items (ammo, drones, vehicles); accept imports for low-volume exquisite systems early in the jump.
