# Soldier systems — Rifle arc (worked example)

> **[WORKED EXAMPLE]** — shows how one program becomes an episode (or a short arc if I'm enjoying it).
> **Source design doc:** [`designs/soldier-systems/infantry-rifle.md`](../designs/soldier-systems/infantry-rifle.md)
> **Program id:** `rifle-std-1`
> **Data:** `data/programs.csv`, `data/costs.csv`

Depth follows interest. This can be one solid episode or a short arc — but industry/cost stays a brief beat, not its own mini-series.

---

## Part 1 — The legacy rifle problem & the options (~15 min)

**Status:** outline
**Focus:** requirement, legacy baseline, and the four options steelmanned

### Cold open
"We still issue rifles designed before most of our corporals were born — and the fix isn't the rifle you'd expect."

### Beats
- Mixed 80s–90s inventory and dual-caliber risk
- Wake-up war lesson: optics + ammo + training, not brand mystique
- The four options (import / optics-only / license-build / clean-sheet), each at its strongest
- Leave the decision open until after the trade-offs

---

## Part 2 — The decision, with a rough cost check (~15 min)

**Status:** outline
**Focus:** decide Option C, and sanity-check it on cost — briefly

### Cold open
"The best rifle you can buy off a foreign shelf is the wrong rifle for a country rebuilding its own plants."

### Beats
- Constraint chain → license-build on the existing plant
- **Rough cost beat (keep it short):** ~60M PD to set up, ~1,000 PD/unit at scale, ~310M PD total; import path ~2.5× per unit and builds no plant. Say the numbers are rough estimates.
- Key materials in one line: barrel steel/aluminum domestic; polymer + some chemicals imported (small stockpile)
- License clauses that matter: wartime continuation + spare-part rights
- Answer the "why not just buy the best?" objection on camera

### Data on screen
- `data/costs.csv` row for `rifle-std-1`

---

## Part 3 (optional) — Fielding & what it unlocks (~8–10 min)

**Status:** optional — merge into Part 2 if the topic doesn't warrant its own episode

### Beats
- Fielding order (active → reserve), surplus bridge for training only
- Optics program now has a stable rail standard
- Single-caliber logistics simplification
- Tease the next thing I actually want to design

---

## Production notes

- **Visuals:** one options table; one small cost callout from `data/costs.csv`
- **Canon:** D-0001
- **Rule:** keep the industry/cost segment brief; the reasoning is the show
