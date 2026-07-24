# Worldbuilding Principles

> Short canon. Full design: [`../docs/superpowers/specs/2026-07-24-world-generation-design.md`](../docs/superpowers/specs/2026-07-24-world-generation-design.md).

## Why Earth-mirroring

1. **Comprehension** — viewers grasp roles faster (classical West/East, industrial heirs, legacy forces).
2. **Path dependence** — 2025 industry needs an Earthlike *sequence* (agriculture → classical surplus/literacy/law → early modern science/trade → fossil industry → industrial war). Roles, not Earth names.
3. **Environment → culture** — packages come from coasts, rivers, plains, deserts, mountains.
4. **Humans build on forefathers** — languages, law, doctrine, kit inherit; the generational jump rebuilds *on* 80s–90s ancestors.
5. **Resources from geology** — ore, fuel, and strategic materials sit where deep-time processes put them (arcs, cratons, basins, shelves). No painted mega-mines. See [`13-resources-from-geology.md`](13-resources-from-geology.md).

## Geography definitions

| Term | Meaning |
| --- | --- |
| **Plate** | Instantaneous rigid kinematic domain; may carry oceanic and continental crust |
| **Continent** | Major continental-crust / terrane lineage; may cross or change plates over deep time |
| **Landmass** | Continuous dry land — may contain **multiple continents** after collision |
| **Present land** | **Emergent** from crust history in the algorithmic generator (no forced %). Veldara reference-campaign board remains Earth-comparable (~29%) by authoring |

Example: Farreach can be one landmass made of **Nerath** + **Tesen** plates colliding at a suture.

## Classical isolation

West and East classical giants barely meet until early modern **because of oceans, mountains, and deserts** — Rome/China logic on *this* map.

## Detail budget

- **Time:** coarser further back; full detail for last century → Maravic → jump.
- **Polities:** full history for **important/neighbors**, **odd ones out**, and **countries of interest**; footnotes otherwise.

## Settlement is not one score

1. **Physical habitability** changes by technology era: preindustrial → industrial → A/C.
2. **A/C only helps where grid reliability, capital, and energy headroom exist**; cooling energy and water burdens stay visible.
3. **Incentives are separate:** resources, trade/harbors, strategy/passes, policy/subsidy, sacred/institutional value.
4. Incentives may create a mine, fortress, free port, or capital in marginal terrain. They do **not** retroactively make the terrain comfortable.
5. The map keeps a no-incentive counterfactual so an **incentive-driven** settlement is explicit.

## Map generation

Deep-time v2 (`maps/generator/deeptime/v2`) forms rigid plates, continental terranes, landmasses, climate, drainage, resources, and era-specific settlement layers. Unique story ⇒ optional new seed; still obey this sequence.
