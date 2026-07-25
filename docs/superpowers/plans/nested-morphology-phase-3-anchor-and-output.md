# Phase 3 — Anchoring and output (tasks 12–19)

Read [`2026-07-24-nested-morphology.md`](2026-07-24-nested-morphology.md) first.
Phases 1 and 2 must be complete.

**Phase goal:** choose the world that can host the existing campaign, refine it
down to 100 m where it matters, extract named features, ship it to the viewer,
and rewrite canon to match what actually generated.

---

## Task 12: Seed search and canon scoring

Veldara's geography canon is **causal, not decorative**. Several documents
assert specific tectonic relationships, and a world that violates them breaks
the reasoning in the doctrine and threat-analysis documents, not just the
scenery. Read these before writing the scoring function:

- `world/00-world-overview.md` — Aurelian is one continent lineage on mostly
  one present plate, hosting Veldara, Korvath, Doverin and Sereth.
- `world/01-our-nation.md` — Veldara is ~3.2 million km²; Eastmarch is
  continuous crust into Korvath, a political border and not a plate edge.
- `maps/00-world-map-brief.md` — Veldara claims west cordillera coast, plains
  and a gulf; Korvath continues east on the **same** continent with no oceanic
  suture between them.
- `maps/01-country-maps-brief.md` — Eastmarch has open approaches and low
  ridges, explicitly **not** a plate boundary; "no fake border mountain wall".
- `world/08-last-20ka.md` — the Eastmarch plain never gets a glacial wall
  between Veldara and Korvath.
- `world/11-legendary-figures.md` — Cassian crosses the Highspine with a land
  army, so the range needs a passable corridor; he never takes the Solmar core,
  which is therefore a defensible port region.

**Files:**
- Create: `maps/generator/deeptime/v2/anchor.py`
- Create: `maps/generator/tests/test_v2_anchor.py`

- [ ] Implement `score_world(world) -> AnchorScore` with one sub-score per
      constraint, each in 0–1, plus the winning region's cell indices:

| Constraint | Pass condition |
| --- | --- |
| Continent scale | A single landmass of 20–35M km² on one dominant plate |
| Veldara claim area | A contiguous ~3.2M km² sub-region with two-ocean access |
| West cordillera | Coast-parallel range within 400 km of the western shore |
| Gulf | A semi-enclosed embayment on the Veldara coast |
| Highspine | An interior range with ≥ 1 pass corridor under 2,000 m |
| Eastmarch | A ≥ 800 km plain, relief under 300 m, crossing the Veldara–Korvath frontier, **no plate boundary within it**, and unglaciated at LGM |
| Farreach | An offshore island group within 1,500 km of the coast |
| Harbours | ≥ 2 natural deep-water harbour sites (Twin Harbors, Solmar) |

- [ ] Sweep seeds at T0 and T1 only — T1 is affordable per seed after phase 1,
      and the constraints are all resolvable at 4.5 km. Rank by total score,
      break ties deterministically by seed.
- [ ] Record the promoted seed and its score breakdown to
      `maps/generator/promoted-seed.json`.
- [ ] Test: a synthetic world with an orogenic wall across Eastmarch scores
      zero on that constraint; one with an open plain scores near 1.
- [ ] Test: scoring is deterministic and order-independent.

**Done when:** a sweep of at least 200 seeds produces a world passing all eight
constraints. If none passes, do **not** loosen the constraints silently — report
which constraint is unreachable and stop, because that is a physics bug in
phase 2, not a search problem.

---

## Task 13: Nested refinement T2–T4

**Files:**
- Create: `maps/generator/deeptime/v2/refine.py`
- Create: `maps/generator/tests/test_v2_refine.py`

- [ ] Implement window extraction: a lat/lon region plus a 10% margin, resampled
      onto a local equal-area grid at the tier's target resolution.
- [ ] Refine relief conditioned on the parent tier — parent slope, lithology,
      climate and base level drive the added detail. Do **not** add unconditioned
      fractal noise; detail must respect the parent's drainage and structure.
- [ ] Re-run tasks 9, 10 and 11 (erosion, coastal, reefs) inside each window at
      that tier's resolution.
- [ ] Process T3 and T4 as disk-backed tiles with overlap so memory stays
      bounded regardless of window area.
- [ ] Blend window margins back so adjacent windows agree.
- [ ] Test: a refined tier, downsampled to its parent's resolution, matches the
      parent elevation within 50 m RMS.
- [ ] Test: no discontinuity at window seams — gradient magnitude across a seam
      is within 1.2× the gradient just inside it.
- [ ] Test: refinement is deterministic and independent of window tiling order.

---

## Task 14: Feature extraction and naming

**Files:**
- Create: `maps/generator/deeptime/v2/features.py`
- Create: `maps/generator/tests/test_v2_features.py`

- [ ] Extract, with stable IDs: seas, gulfs, straits, lakes, mountain ranges,
      passes, river systems, deltas, island groups, reefs, capes, peninsulas.
- [ ] Classify enclosed vs semi-enclosed seas by the ratio of opening width to
      basin area — this is what distinguishes a Mediterranean from a bay.
- [ ] Derive stable IDs from a hash of the feature's geometry, not from
      iteration order, so IDs survive regeneration and reordering.
- [ ] Assign persistent names, seeded from the feature ID, with canon names
      pinned by an override table so Highspine and Eastmarch keep their names.
- [ ] Export as GeoJSON alongside the existing resource and settlement layers.
- [ ] Test: IDs and names are identical across two runs of the same seed.
- [ ] Test: a synthetic Mediterranean-shaped basin classifies as enclosed; an
      open bay does not.

---

## Task 15: Navigability

The militarily useful output of the reef and shelf work. Without this, the
coral modelling from task 11 is decoration.

**Files:**
- Create: `maps/generator/deeptime/v2/navigation.py`
- Create: `maps/generator/tests/test_v2_navigation.py`

- [ ] Channel depth and width for every strait and harbour approach, at T4
      resolution where available.
- [ ] Chokepoint geometry: narrowest width, length, and the alternative routes
      available if closed.
- [ ] Harbour rating from depth, shelter — fetch-weighted wave exposure from
      task 10 — approach width, and hinterland access.
- [ ] Shelf-break position and depth, for submarine operating areas.
- [ ] Coarse tidal-range proxy from basin geometry: funnel-shaped embayments
      amplify, open coasts do not.
- [ ] Test: a modelled strait's width matches a direct geometric measurement
      within 10%.
- [ ] Test: harbour rating correlates with shelter, and the Twin Harbors and
      Solmar sites identified in task 12 both rate highly.

---

## Task 16: Sparse tile pyramid

**Read first:** `deeptime/v2/tiles.py` and `export.py`. Note `max_zoom` is
currently a literal `3` in **three** places: `tiles.py` line 35, and
`export.py` lines 364 and 383. All three must move to config or they will drift.

A full global pyramid to z11 would be 5.6M tiles at roughly 280 GB. Coverage
must be uneven.

**Files:**
- Modify: `maps/generator/deeptime/v2/tiles.py`, `export.py`
- Modify: `maps/generator/tests/test_v2_tiles.py`

- [ ] Global pyramid z0–z6 (5,461 tiles, ~2.4 km/px at the equator).
- [ ] Deep pyramid z7–z11 over the Aurelian and Veldara windows only
      (~35k tiles). Web Mercator resolution is `156543.03 / 2**z` m/px, so z11
      is ~76 m/px and matches the T4 tier.
- [ ] Emit a coverage manifest the viewer can read to know where deep zoom
      exists.
- [ ] Skip writing tiles that are entirely outside the deep region.
- [ ] Test: tile counts match the expected sparse layout, not the dense one.
- [ ] Test: a deep-region tile at z11 differs from its overzoomed parent,
      proving real detail is present rather than upscaling.

---

## Task 17: Viewer

**Read first:** `maps/viewer/src/main.js`.

**Files:**
- Modify: `maps/viewer/src/main.js`, `maps/viewer/README.md`

- [ ] Raise the raster source `maxzoom` to the deep-pyramid maximum and let
      MapLibre overzoom outside the covered region.
- [ ] Add feature and navigability overlays as toggleable layers.
- [ ] Keep the existing polygon fill/line treatment for resources and
      settlements; do not reintroduce circle layers.
- [ ] Verify the globe still renders to the poles — that behaviour comes from
      the raster source and must not regress.
- [ ] Smoke test: `npm run dev`, load, confirm no console errors and that deep
      zoom over Veldara resolves new detail.

---

## Task 18: Validation suite

**Files:**
- Create: `maps/generator/tests/test_v2_morphology_validation.py`

Consolidate the acceptance criteria into one suite that runs against the
promoted world:

- [ ] A strait of ≤ 20 km width exists and is resolvable.
- [ ] An enclosed sea, a great lake, and an archipelago of ≥ 8 islands exist.
- [ ] Cubed-sphere seam continuity: elevation and drainage show no
      discontinuity at face boundaries.
- [ ] Polar cells are not distorted beyond the stated tolerance.
- [ ] Coastline fractal dimension in 1.15–1.35.
- [ ] No D8 spike in river bearings.
- [ ] Hypsometric curve within tolerance of Earth's.
- [ ] Land fraction is reported, not clamped.
- [ ] LGM re-derived from the new bedrock, with plausible land gain.
- [ ] Same seed twice, byte-identical.

---

## Task 19: Re-anchor canon, regenerate, ship

Do this **last**. Rewriting canon before the world is final means doing it
twice.

**Files:**
- Modify: `world/00`–`world/13`, `maps/00-world-map-brief.md`,
  `maps/01-country-maps-brief.md`
- Modify: `threat-analysis/`, `doctrine/`, `episodes/` where geography is cited
- Modify: `decisions-log.md`, `maps/generator/README.md`

- [ ] Rewrite the geography of Aurelian, Veldara, Korvath, Doverin, Sereth,
      Highspine, Eastmarch, Farreach, Twin Harbors and the Solmar core to match
      the promoted world — real coordinates, extents, orientations, coastline
      descriptions.
- [ ] Check every downstream document that reasons **from** geography. The
      Eastmarch threat axis in `threat-analysis/scenarios/01-eastern-invasion.md`
      and the approach geometry in `maps/01-country-maps-brief.md` both depend
      on the open-plain claim; if the promoted world's plain differs in width or
      orientation, those arguments need updating, not just their nouns.
- [ ] Record the promoted seed and `GENERATOR_VERSION` as canon in
      `decisions-log.md`, with a decision superseding D-0027 on resolution.
- [ ] Add the tier table and measured runtime to `maps/generator/README.md`.
- [ ] Full regeneration: promoted seed, present and LGM, all tiers.
- [ ] Regenerate `maps/exports/*` and `maps/viewer/public/world/*`; commit.
- [ ] Verify every geographic claim resolves to an extracted named feature.
- [ ] Push; update the PR.

---

## Phase 3 exit criteria

- [ ] Full validation suite green.
- [ ] Promoted world passes all eight anchor constraints.
- [ ] Deep zoom over Veldara resolves genuine 100 m detail in the viewer.
- [ ] No canon document contradicts the generated map.
