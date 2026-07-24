# Phase 1 — Foundations (tasks 1–6)

Read [`2026-07-24-nested-morphology.md`](2026-07-24-nested-morphology.md) first
for constraints, conventions and the measured baseline.

**Phase goal:** make a 25.2M-cell (`grid_n = 2048`) world buildable inside
11 GB. No new physics in this phase. At the end of it the pipeline should do
exactly what it does today, only at 32× the linear resolution.

**Order matters.** Task 2 unblocks everything else; do not reorder.

---

## Task 1: Dependencies, version stamp, field contract

**Read first:** `maps/generator/requirements.txt`,
`maps/generator/deeptime/v2/model.py` (the `GeologyFields` consumers in
`_deposit_context`, lines 61–162), `maps/generator/deeptime/v2/export.py`.

**Files:**
- Modify: `maps/generator/requirements.txt`
- Create: `maps/generator/deeptime/v2/contract.py`
- Modify: `maps/generator/deeptime/v2/model.py`
- Create: `maps/generator/tests/test_v2_contract.py`

- [ ] Add `scipy>=1.11` to `requirements.txt` and install it.
- [ ] In `contract.py`, define `GENERATOR_VERSION = "2.1.0"` and a
      `FIELD_CONTRACT` mapping of every field name that a downstream consumer
      reads, to `(dtype, units, valid_range)`. Derive the list from the actual
      reads in `model._deposit_context` — it consumes `geology.history`,
      `geology.lithology`, `geology.paleoclimate`, `geology.basin_depth`,
      `geology.sediment`, `geology.orogeny`, `geology.continental`,
      `geology.elevation_m`. Do not invent fields; enumerate what is read.
- [ ] Add `validate_contract(geology, climate, hydrology) -> None` raising
      `ContractError` listing every missing key and every out-of-range field.
- [ ] Call it at the end of `generate_world`, behind a `validate: bool = True`
      argument on `WorldConfig`.
- [ ] Add `GENERATOR_VERSION` and `seed` to the exported `meta` dict.
- [ ] Test: removing a key from `geology.lithology` raises `ContractError`
      naming that key; a normal `grid_n = 32` world validates clean.

**Done when:** `python3 -m unittest tests.test_v2_contract -v` is green and
`python3 -m deeptime --seed 42` still prints its summary line.

---

## Task 2: Vectorised grid construction

This is the critical-path task. See the master plan for why the current code
costs ~1,470 bytes/cell.

**Read first:** all of `maps/generator/deeptime/v2/grid.py`. Pay attention to
the index convention: `index = face * n * n + j * n + i`, where `i` indexes
`alpha` and `j` indexes `beta`, and `meshgrid(..., indexing="xy")` produces
arrays shaped `(n, n)` with `beta` along axis 0. Getting this wrong silently
corrupts every field.

**Files:**
- Modify: `maps/generator/deeptime/v2/grid.py`
- Create: `maps/generator/tests/test_v2_grid_scaling.py`

- [ ] Replace the `set`-based adjacency build. The existing offset loop already
      computes, for each of the 8 `(di, dj)` offsets and each face, the target
      index of every cell — that is exactly a dense `(N, 8)` neighbour table.
      Write it straight into `neighbors` instead of accumulating `edge_cells`
      and symmetrising through sets:

```python
OFFSETS = ((-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1))
neighbors = np.full((6 * n * n, 8), -1, dtype=np.int32)
for slot, (di, dj) in enumerate(OFFSETS):
    aa, bb = alpha + di * delta, beta + dj * delta
    for face in range(6):
        target = cls.indices_for_xyz_static(
            _face_vectors(face, aa, bb).reshape(-1, 3), n
        )
        neighbors[face * n * n : (face + 1) * n * n, slot] = target
self_ref = neighbors == np.arange(6 * n * n, dtype=np.int32)[:, None]
neighbors[self_ref] = -1
```

**This code has been prototyped against the current implementation.** It
produces set-identical neighbour rows at `n` = 4, 8, 16, 32, 64, 96 and 128,
and the resulting table is already **fully symmetric** at every one of those
resolutions — the measured count of one-directional edges was zero. The
`set`-based symmetrisation in the current code is therefore redundant, not
load-bearing.

- [ ] Do not add a symmetry-repair pass. Add a **symmetry assertion** instead,
      run in tests at small `n` and behind a debug flag at large `n`. Only the
      `24n − 24` cells on face borders could ever be asymmetric (49,128 cells at
      `n = 2048`), so if the assertion ever fires, repair just those: collect
      their outgoing edges, test whether the reverse is present with
      `(neighbors[b] == a[:, None]).any(axis=1)`, and widen the table via
      `np.bincount` on the missing sources.
- [ ] Make `edge_cells` a lazily built cached property rather than an eager
      field. It is only consumed by `PlateModel.boundaries` and
      `geology._apply_crust_events`, both of which run at T0. At T1 it would be
      ~100M pairs and must never be materialised.
- [ ] Make `lon_deg` and `lat_deg` lazy properties derived from `xyz`. They are
      404 MB of redundant storage at T1.
- [ ] Change `@lru_cache(maxsize=12)` on `create` to `maxsize=2`. Twelve cached
      T1 grids would be ~19 GB.
- [ ] Test (fast): for `n` in 4, 8, 16, 32, assert the new `neighbors` is
      exactly symmetric — for every `a` and every `b` in `neighbors[a]`, `a`
      appears in `neighbors[b]` — and that it matches the old set-based result
      cell for cell. Keep a copy of the old builder in the test file as the
      reference oracle.
- [ ] Test (fast): the degree distribution is **exactly 24 cells of degree 7 and
      every other cell of degree 8**, at every `n`. This was measured on the
      current implementation at `n` = 8, 16, 32 and 64 and holds exactly; the 24
      are the three cells meeting at each of the 8 cube corners. It is a much
      sharper invariant than a range check, so use it — any deviation means the
      seam handling is wrong.
- [ ] Test (slow, `DEEPTIME_SLOW`): `create(1024)` completes under 60 s and
      2.5 GB peak RSS.

**Done when:** the scaling table below is reproduced. Measured prototype
figures for the neighbour build alone, to compare against:

| `grid_n` | Cells | Build | Peak RSS | Bytes/cell |
| --- | --- | --- | --- | --- |
| 256 | 393,216 | 0.42 s | 169 MB | 451 |
| 512 | 1,572,864 | 1.83 s | 169 MB | 113 |

Against the baseline's 4.30 s and 1,468 B/cell at `n = 256`, that is ~10× faster
with flat memory.

```bash
python3 -c "
import resource, time, gc
from deeptime.v2.grid import CubedSphere
for n in (256, 512, 1024):
    gc.collect()
    t = time.perf_counter(); g = CubedSphere.create(n); dt = time.perf_counter() - t
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f'n={n} cells={g.size} t={dt:.2f}s peak={peak:.0f}MB {peak*1048576/g.size:.0f}B/cell')
"
```

---

## Task 3: Vectorised connected components

**Read first:** `grid.components` (`grid.py` lines 184–206),
`deeptime/v2/topology.py`, and the three call sites:
`topology.component_labels`, `plates.PlateModel.assert_connected`,
`hydrology.compute_hydrology` (lake labelling).

`grid.components` is a pure-Python DFS with an explicit stack. It is only 0.6%
of the profile at `grid_n = 128`, but it is O(N) Python and becomes minutes at
T1.

**Files:**
- Modify: `maps/generator/deeptime/v2/topology.py`
- Modify: `maps/generator/deeptime/v2/grid.py`
- Modify: `maps/generator/tests/test_v2_surface.py`

- [ ] Reimplement `component_labels` on top of
      `scipy.sparse.csgraph.connected_components`. Build a COO matrix from the
      masked sub-graph only (`src` and `dst` both in `mask`), with
      `data=np.ones(len(src), dtype=np.int8)` to keep it small.
- [ ] Return labels ordered by descending component size, matching today's
      behaviour — `grid.components` sorts by `len` descending and
      `component_labels` assigns label 0 to the largest. Existing tests and
      `export.py` depend on this.
- [ ] Reimplement `grid.components` as a thin wrapper over the new label
      function so `assert_connected` gets the speedup too.
- [ ] Test: on a `grid_n = 32` world, new and old implementations produce
      identical label arrays (keep the old DFS in the test as the oracle).
- [ ] Test: label 0 is the largest component by cell count.

**Done when:** `component_labels` at `grid_n = 512` runs in under 3 s.

---

## Task 4: Memory-bounded climate and hydrology

**Read first:** `deeptime/v2/climate.py` (especially `_upstream_neighbors`
lines 60–72 and `_ocean_influence` lines 30–37), `deeptime/v2/hydrology.py`
(`_priority_flood` lines 30–64, `_receivers` lines 67–87, and the accumulation
loop at lines 108–112).

Two different problems here — do not conflate them.

**Memory (blocking).** `climate._upstream_neighbors` materialises
`grid.xyz[:, None, :] - neighbor_xyz`, shape `(N, 8, 3)` float64. At T1 that is
**4.8 GB in one allocation**, and it builds several such temporaries.
`_ocean_influence` gathers `(N, 8)` — 1.6 GB — 24 times.

**Speed (measure first).** `hydrology._priority_flood` is a Python `heapq`
loop, and the drainage accumulation is a Python loop over land cells in reverse
pop order. Both are inherently sequential. Measured cost is 0.30 s for all of
`compute_hydrology` at 98k cells; linear extrapolation to T1 is ~75 s, which is
**within budget for a one-time run**. Do not rewrite these unless the benchmark
in this task shows otherwise.

**Files:**
- Modify: `maps/generator/deeptime/v2/climate.py`
- Modify: `maps/generator/deeptime/v2/hydrology.py`
- Create: `maps/generator/tests/test_v2_budget.py`

- [ ] Rewrite `_upstream_neighbors` to process cells in slices of ~2M, keeping
      only the per-slice `argmax` result. Peak extra allocation must be under
      600 MB regardless of `N`.
- [ ] Rewrite `_ocean_influence` to iterate in slices, writing into a
      preallocated output buffer instead of allocating per iteration.
- [ ] Vectorise `hydrology._receivers`. The current `for cell in
      np.flatnonzero(land)` loop is trivially expressible as a masked `argmin`
      over `filled[safe]` with ocean-adjacent cells forced to `-1`. This is a
      pure win; do it.
- [ ] Leave `_priority_flood`'s heap and the accumulation loop alone.
- [ ] Add a benchmark harness `tests/test_v2_budget.py` that runs each stage at
      `grid_n = 256` and asserts a per-stage ceiling on peak RSS delta. Record
      the measured numbers in the test as comments so regressions are visible.
- [ ] Test: refactored `_upstream_neighbors` and `_ocean_influence` produce
      bit-identical output to the originals at `grid_n = 32` and `64`.

**Done when:** a `grid_n = 512` climate + hydrology pass stays under 3 GB peak
RSS and the identity tests are green.

---

## Task 5: Tier configuration and checkpointing

**Read first:** `deeptime/v2/model.py` (`WorldConfig`, `generate_world`),
`deeptime/__main__.py`.

**Files:**
- Create: `maps/generator/deeptime/v2/tiers.py`
- Create: `maps/generator/deeptime/v2/checkpoint.py`
- Modify: `maps/generator/deeptime/v2/model.py`
- Modify: `maps/generator/deeptime/__main__.py`
- Create: `maps/generator/tests/test_v2_checkpoint.py`

- [ ] In `tiers.py` define the ladder from the spec as data, not scattered
      literals:

```python
@dataclass(frozen=True)
class Tier:
    name: str          # "t0".."t4"
    grid_n: int | None # None for windowed tiers
    target_km: float   # nominal cell size
    windowed: bool

TIERS = (
    Tier("t0", 256,  35.0, False),
    Tier("t1", 2048,  4.5, False),
    Tier("t2", None,  1.0, True),
    Tier("t3", None,  0.25, True),
    Tier("t4", None,  0.1, True),
)
```

- [ ] Add `tier: str = "t1"` and `cache_dir: Path` to `WorldConfig`.
- [ ] In `checkpoint.py`, implement `save(tier, seed, version, payload)` and
      `load(tier, seed, version)` writing `.npz` under
      `<cache_dir>/<seed>/<version>/<tier>.npz`. A version or seed mismatch is
      a cache miss, never a silent stale hit.
- [ ] Restructure `generate_world` so each tier checks for a checkpoint before
      computing, and writes one after. Re-running T4 must not recompute T0.
- [ ] Add `--tier` and `--no-cache` flags to the CLI.
- [ ] Test: run T0 twice; second run is a cache hit (assert by timing or by
      monkeypatching `simulate_geology` to raise).
- [ ] Test: bumping `GENERATOR_VERSION` invalidates the cache.
- [ ] Test: same seed twice produces byte-identical `.npz` payloads.

---

## Task 6: T0 → T1 field transfer

**Read first:** `geology.simulate_geology` (particularly what it returns), and
`grid.indices_for_xyz_static`.

Tectonics stays at T0 (`grid_n = 256`, ~34 s for 80 ticks). T1 does not re-run
plates; it receives the T0 crust fields once and refines from there. This is
what keeps the whole design affordable.

**Files:**
- Create: `maps/generator/deeptime/v2/transfer.py`
- Modify: `maps/generator/deeptime/v2/model.py`
- Create: `maps/generator/tests/test_v2_transfer.py`

- [ ] Implement `upsample(field, source_grid, target_grid, method)` where
      `method` is `"nearest"` for label fields (`plate_id`, `continent_id`) and
      `"smooth"` for continuous fields. `"smooth"` should do nearest sampling
      via `target_grid.indices_for_xyz` inverted through the source grid,
      followed by `source_grid.smooth`-equivalent blending on the target so the
      T0 cell boundaries do not print through as 35 km staircase edges.
- [ ] Verify no staircase artifact: this is the most likely visible failure of
      the whole phase. Assert that the gradient magnitude histogram of the
      upsampled elevation has no spike at the T0 cell spacing.
- [ ] Test: upsampling then area-weighted downsampling recovers the T0 land
      mask area within 2%.
- [ ] Test: label fields upsample without introducing labels absent from T0.
- [ ] Wire into `generate_world`: T0 geology → transfer → T1 fields.

**Done when:** a `grid_n = 1024` world builds end to end within budget, and
visual inspection of the exported elevation PNG shows no 35 km grid pattern.

---

## Phase 1 exit criteria

- [ ] `DEEPTIME_SLOW=1 python3 -m unittest discover -s tests` green.
- [ ] `grid_n = 2048` world builds within 11 GB peak RSS. Record the actual
      time and RSS in the commit message.
- [ ] Same seed twice, byte-identical output.
- [ ] Commit and push; open or update the PR before starting phase 2.
