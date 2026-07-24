# Scenario: Eastern invasion (modernization race)

> **Adversary:** Korvath
> **Likelihood:** Medium
> **Severity if it happens:** Existential
> **Status:** starter draft — [STARTER SUGGESTION]

## 1. Adversary objective

Defeat Veldara quickly enough that great-power politics freeze a favorable line. Prefer to fight **after** their modernization tranche lands and **before** ours does.

## 2. Their theory of victory

*"We do not need to occupy everything. We punch through with modern fires, drones, and AD umbrellas we learned from the distant war. Their legacy pockets fight bravely and die out of contact. International mediation locks in our gains before their new factories matter."*

## 3. Timeline and warning

- **Warning:** 2–4 weeks of visible mobilization.
- **Speed:** days to weeks depending on how modern each side's AD and logistics are that year.
- **First 72 hours:** AD denseness, C2 survival, ammo release, reserve call-up.

## 4. Forces they bring

A mix that shifts by year of the race: early years still legacy-heavy; later years modern artillery, drones, SHORAD/MRAD, and better networking. Exact ORBAT is less important than the rule — **do not design against their parade inventory from 1995.**

## 5. Where and how

Primary axis: **Eastmarch** plains/low ridges into the **Heartland** (see `maps/01-country-maps-brief.md`). Maritime pressure on Westreach and Gulf Coast ports can accompany the land attack to starve imported components.

## 6. What failure looks like for us

Lost territory plus a frozen conflict — and a ruined modernization narrative at home. Alternatively: we "win" tactically with irreplaceable legacy stocks and emerge unable to reconstitute.

## 7. Requirements this scenario generates

| # | Requirement (as a problem) | Priority | Design / data |
| --- | --- | --- | --- |
| 1 | Legacy logistics cannot fuel and rearm a modern fight | Must-have | `designs/logistics/` |
| 2 | Reservists and regulars still on mixed 80s–90s small arms / poor optics | Must-have | [`designs/soldier-systems/infantry-rifle.md`](../../designs/soldier-systems/infantry-rifle.md) + `data/*` rifle rows |
| 3 | C2 and ISR are voice-era; drone mass is not integrated | Must-have | `designs/c4isr/` |
| 4 | Land fires and armor are generation-behind | Must-have | `designs/land/` |
| 5 | Air defense cannot handle mass drones + cruise missiles | Must-have | `designs/air/` |
| 6 | Air force cannot survive or contribute past day one | Must-have | `designs/air/` |
| 7 | Navy cannot protect materials SLOCs under pressure | Must-have | `designs/sea/` |
| 8 | Factories cannot surge ammo and drones | Must-have | `industry/`, `data/` |
