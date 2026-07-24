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
| **Continent** | A **continental plate** (or major continental plate fragment) |
| **Landmass** | Continuous dry land — may contain **multiple continents** after collision |
| **Present land** | ≈ **29%** of surface (Earth-like); LGM higher via lower seas |

Example: Farreach can be one landmass made of **Nerath** + **Tesen** plates colliding at a suture.

## Classical isolation

West and East classical giants barely meet until early modern **because of oceans, mountains, and deserts** — Rome/China logic on *this* map.

## Detail budget

- **Time:** coarser further back; full detail for last century → Maravic → jump.
- **Polities:** full history for **important/neighbors**, **odd ones out**, and **countries of interest**; footnotes otherwise.

## Map generation

Deep-time plates (`maps/generator/deeptime`) form continents **and** (next) resource prospects; settlement and culture layers follow. Unique story ⇒ optional new seed; still obey this sequence.
