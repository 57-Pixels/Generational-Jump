# Phase 2 — Surface physics (tasks 7–11)

Read [`2026-07-24-nested-morphology.md`](2026-07-24-nested-morphology.md) first.
**Phase 1 must be complete** — these tasks are only testable at T1 resolution,
where the features they produce are large enough to measure.

**Phase goal:** produce Earth-like geography from process rather than from
noise. This is where enclosed seas, archipelagos, fjords, canyons and reefs
actually appear.

Constants below are starting values chosen to put outputs in Earth's observed
range. Tune them against the acceptance tests, not against how the map looks.

---

## Task 7: Ocean-floor construction

**Read first:** `geology.py` lines 442–492 — the current ocean elevation is
`-2600 - 250 * sqrt(ocean_age)`, where `ocean_age` is synthesised from ridge
memory plus smoothed noise rather than from spreading history. The depth curve
is roughly right (−2600 m at the ridge, −5950 m at 180 Ma); the **age field** is
the part that is fake, so the ocean floor has no fracture zones, no trenches
and no back-arc basins.

**Files:**
- Create: `maps/generator/deeptime/v2/seafloor.py`
- Modify: `maps/generator/deeptime/v2/geology.py`
- Create: `maps/generator/tests/test_v2_seafloor.py`

- [ ] Track real seafloor age during the T0 tick loop. Oceanic cells created at
      a divergent boundary get `age = 0`; every tick, surviving oceanic cells
      age by `dt_ma`; cells consumed at convergent boundaries are removed. Store
      as a new `seafloor_age_ma` field on `GeologyFields` and add it to the
      contract.
- [ ] Depth from half-space cooling, flattening after 80 Ma:

```python
depth = np.where(
    age < 80.0,
    2600.0 + 345.0 * np.sqrt(age),
    5650.0 - 2470.0 * np.exp(-0.0278 * age),
)
```

- [ ] Trenches: at convergent boundaries with an oceanic downgoing plate, add a
      narrow depression up to 4,000 m below local abyssal depth, with a
      half-width of ~60 km and an outer rise of +200 m on the seaward side.
- [ ] Back-arc basins: behind arcs where the overriding plate is extending,
      raise the floor to ~3,000 m and mark the cells so phase 3 can recognise
      them as semi-enclosed seas.
- [ ] Hotspot swells: broad Gaussian uplift, ~1,000 km radius, +800 m at centre.
- [ ] Fracture zones: transform offsets produce age discontinuities across the
      strike. Propagate them so the age field has visible lineations, and let
      the depth formula turn them into scarps.
- [ ] Variable shelf width driven by margin type: passive margins 100–300 km,
      active margins 10–50 km. Replace the current fixed `shelf_zone` band in
      `geology.py` lines 484–491, which is a constant function of
      `continental_soft` and therefore uniform everywhere.
- [ ] Test: depth is monotonic in age below 80 Ma; abyssal depth at 150 Ma is
      within 5,600–6,000 m.
- [ ] Test: every trench cell is deeper than the median depth of the abyssal
      cells within 500 km.
- [ ] Test: passive-margin shelves are on average at least 3× wider than
      active-margin shelves.

---

## Task 8: Climate and ocean circulation

**Read first:** all of `climate.py`. Orographic uplift already exists in the
64-iteration moisture loop (lines 105–114) — the missing pieces are an explicit
leeward drying term, ocean heat transport, and a monsoon that responds to land
distribution rather than to latitude alone.

**Files:**
- Modify: `maps/generator/deeptime/v2/climate.py`
- Create: `maps/generator/deeptime/v2/ocean.py`
- Create: `maps/generator/tests/test_v2_climate_bands.py`

- [ ] Add an explicit rain-shadow term: after the moisture loop, compute
      downslope descent along the wind vector and multiply precipitation by
      `exp(-descent_m / 900.0)` on the leeward side. Without this, ranges wet
      both flanks roughly equally.
- [ ] In `ocean.py`, build wind-driven surface circulation: subtropical gyres,
      western boundary intensification, and equatorial upwelling. A streamfunction
      on the sphere driven by the existing `_wind_vectors` output is sufficient;
      this does not need to be a real ocean model.
- [ ] Advect sea-surface temperature along those currents so west and east
      coasts at the same latitude differ. Target a 5–10 °C contrast at 40°
      latitude, matching the Atlantic.
- [ ] Feed SST back into the coastal air temperature and into reef viability
      in task 11.
- [ ] Add cold-water upwelling on eastern ocean margins and make it drive
      coastal aridity — this is what produces Atacama- and Namib-style deserts,
      and it is what the current latitude-only `subtropical_dry` term cannot do.
- [ ] Test: across a synthetic ridge fixture, windward precipitation is at
      least 3× leeward.
- [ ] Test: at 40° latitude, mean west-coast and east-coast SST differ by
      5–10 °C, with the correct sign for the hemisphere.
- [ ] Test: at least one coastal desert exists adjacent to an upwelling zone.

---

## Task 9: Erosion, lakes and glaciation

The single largest realism win in the plan. Real coastlines are erosional
products; no amount of tectonic detail substitutes for running water.

**Read first:** `hydrology.py` in full. Note that `_priority_flood` **fills**
depressions and the code then recovers lakes by measuring fill depth
(`depression > 20.0`, line 120). That is backwards for our purposes — we want
lakes to be first-class, and we want endorheic basins to stay closed.

**Files:**
- Create: `maps/generator/deeptime/v2/surface.py`
- Modify: `maps/generator/deeptime/v2/hydrology.py`
- Create: `maps/generator/tests/test_v2_drainage.py`
- Create: `maps/generator/tests/test_v2_glacial.py`

- [ ] Implement stream-power incision with hillslope diffusion, iterated to
      convergence:

```python
# Detachment-limited stream power. m/n = 0.5 is the standard ratio.
K, m, n = 3.0e-6, 0.5, 1.0
incision = K * discharge**m * slope**n
# Hillslope diffusion, m^2/yr.
D = 0.01
```

      Run 200–400 iterations at T1 with an adaptive timestep, checking that
      total relief stabilises rather than running to a peneplain.
- [ ] Add sediment transport and deposition: eroded mass moves downstream and
      deposits where transport capacity drops, building alluvial fans, valley
      fills and deltas.
- [ ] Rework lake handling. A depression becomes a lake if inflow exceeds
      evaporation over its area; otherwise it is an endorheic basin (salt pan,
      no outflow). Lakes get a real water surface and act as local base level
      for upstream incision. Do not fill them away.
- [ ] Glaciation. Compute an equilibrium line altitude from latitude and
      temperature; cells above it accumulate ice. Glacial erosion scales with
      ice flux and over-deepens valleys into U-shaped profiles. Where a glaciated
      valley meets the coast and the over-deepened floor drops below sea level,
      the result is a fjord — assert this, because fjords are the clearest test
      that glacial erosion is actually running.
- [ ] Add present-day polar ice caps as standing features, and include their
      mass in the sea-level budget.
- [ ] Canyon incision: where uplift rate approaches incision rate in an arid
      cell, the river cuts a narrow steep-walled gorge rather than widening a
      valley.
- [ ] Test: the drainage network is acyclic and every river cell reaches either
      the ocean or a lake.
- [ ] Test: **no grid-aligned drainage.** Build a histogram of river-segment
      bearings and assert no spike at the eight D8 directions — specifically,
      that no 10° bin holds more than 1.6× the mean bin count. This is the
      test most likely to fail; if it does, the fix is flow routing with
      D-infinity or a randomised tie-break, not a smoothing pass.
- [ ] Test: lakes survive routing, and at least one endorheic basin exists.
- [ ] Test: at least one fjord — a below-sea-level over-deepened glacial valley
      with length ≥ 5× its width.
- [ ] Test: hypsometric curve is within tolerance of Earth's, which is the
      cheapest single check that erosion is doing the right thing globally.

---

## Task 10: Coastal evolution

**Files:**
- Create: `maps/generator/deeptime/v2/coastal.py`
- Create: `maps/generator/tests/test_v2_coastal.py`

- [ ] Compute wave energy per coastal cell from fetch — distance of open water
      upwind — and from the prevailing wind field.
- [ ] Erode high-energy headlands and deposit in low-energy bays, producing
      spits, barrier islands, tombolos and lagoons.
- [ ] Add longshore drift so deposition is directional rather than symmetric.
- [ ] Let drowned river valleys become rias, and drowned glacial valleys fjords
      (from task 9).
- [ ] Test: coastline fractal dimension, by box counting, lands in **1.15–1.35**.
      Earth's coastlines sit in this band; a smooth blob scores near 1.0. This
      is the direct quantitative answer to the original complaint about
      circular continents.
- [ ] Test: sheltered coasts accumulate sediment and exposed coasts retreat.

---

## Task 11: Islands, volcanoes and reefs

**Files:**
- Create: `maps/generator/deeptime/v2/reefs.py`
- Modify: `maps/generator/deeptime/v2/seafloor.py`
- Create: `maps/generator/tests/test_v2_reefs.py`

- [ ] Volcanic arcs as discrete edifices along subduction zones, spaced 50–70 km
      apart, not as a continuous ridge. Island arcs are the Philippines/Japan
      analogue and the current model cannot produce them.
- [ ] Hotspot chains with monotonic age progression along plate motion, each
      edifice subsiding as the plate cools and moves off the swell.
- [ ] Reef growth tracking relative sea level: growth up to ~10 mm/yr, requiring
      SST above 18 °C (from task 8) and photic-zone depth under ~50 m.
- [ ] The Darwin sequence: fringing reef on a young volcanic island, barrier
      reef as it subsides, atoll once the edifice drowns. Atolls must only
      appear over subsided edifices — that is the test.
- [ ] Test: every atoll sits over a drowned volcanic edifice in water warm
      enough for reef growth.
- [ ] Test: hotspot chain ages increase monotonically along the chain.
- [ ] Test: at least one archipelago of ≥ 8 islands exists at T1.

---

## Phase 2 exit criteria

- [ ] `DEEPTIME_SLOW=1` suite green.
- [ ] Coastline fractal dimension in 1.15–1.35.
- [ ] Hypsometric curve within tolerance of Earth's.
- [ ] No D8 spike in river bearings.
- [ ] A T1 world contains at least one enclosed sea, one great lake, one fjord
      coast, one archipelago of ≥ 8 islands, and one atoll.
- [ ] Still inside 11 GB and still deterministic.
- [ ] Commit, push, update the PR before phase 3.
