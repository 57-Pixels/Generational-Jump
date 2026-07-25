# Nested morphology — master implementation plan

> **For agentic workers:** this plan is split across four files. Read this one
> first for constraints and conventions, then implement the phase files in
> order. Every task is self-contained: it names the files to read, the exact
> change to make, the test to write, and the command that proves it worked.
> Do not skip the "Read first" lists — several tasks fail silently if you guess
> at the existing signatures.

**Goal:** raise the world generator from ~144 km cells to a nested ladder
(~35 km tectonics → 4.5 km global surface → 100 m operational windows), add
the surface-process systems needed for Earth-like geography, then re-anchor
Veldara canon to the generated world.

**Spec:** [`../specs/2026-07-24-nested-morphology-design.md`](../specs/2026-07-24-nested-morphology-design.md)

**Phases:**

| File | Scope | Tasks |
| --- | --- | --- |
| [`nested-morphology-phase-1-foundations.md`](nested-morphology-phase-1-foundations.md) | Make 25M cells possible at all | 1–6 |
| [`nested-morphology-phase-2-physics.md`](nested-morphology-phase-2-physics.md) | Seafloor, climate, erosion, coasts, reefs | 7–11 |
| [`nested-morphology-phase-3-anchor-and-output.md`](nested-morphology-phase-3-anchor-and-output.md) | Seed search, refinement, features, tiles, canon | 12–19 |

---

## Measured baseline

All figures below were measured on the target host (4 vCPU, 15 GB RAM,
230 GB disk) on the current `main`. Reproduce with the commands in
[Verification](#verification). **Do not trust remembered numbers — these are
the real ones.**

Grid construction, `CubedSphere.create`:

| `grid_n` | Cells | Time | Peak RSS | Bytes/cell |
| --- | --- | --- | --- | --- |
| 64 | 24,576 | 0.25 s | 64 MB | 2,746 |
| 128 | 98,304 | 0.99 s | 161 MB | 1,718 |
| 192 | 221,184 | 2.37 s | 322 MB | 1,526 |
| 256 | 393,216 | 4.30 s | 550 MB | 1,468 |

Full pipeline, `generate_world`:

| `grid_n` | Cells | Time | Peak RSS |
| --- | --- | --- | --- |
| 48 | 13,824 | 2.1 s | 65 MB |
| 64 | 24,576 | 3.0 s | 96 MB |
| 96 | 55,296 | 6.2 s | 156 MB |

Stage breakdown at `grid_n = 128`:

| Stage | Time | Share |
| --- | --- | --- |
| `CubedSphere.create` | 1.13 s | 10.9% |
| `simulate_geology` (80 ticks) | 8.57 s | 82.3% |
| `component_labels` | 0.07 s | 0.6% |
| `compute_climate` | 0.34 s | 3.3% |
| `compute_hydrology` | 0.30 s | 2.9% |

## Why the grid cannot simply be turned up

Asymptotic cost is **~1,470 bytes per cell** and **~10.9 µs per cell**. At the
T1 target of `grid_n = 2048` (25.2M cells) that extrapolates to **~37 GB and
~275 s for grid construction alone**, against a 15 GB host. It will OOM, not
run slowly.

The memory is not the arrays. `xyz`, `area_sr` and `neighbors` together are
about 1.6 GB at that size, which is affordable. The cost is in
`CubedSphere.create`, which builds one Python `set` per cell:

```python
adjacency: list[set[int]] = [set() for _ in range(6 * n * n)]
for left, right in edge_cells:
    adjacency[int(left)].add(int(right))
    adjacency[int(right)].add(int(left))
```

`sys.getsizeof(set())` is 216 bytes, so 25.2M empty sets cost 5.4 GB before any
contents, and the loop is ~100M Python-level iterations. **Task 2 replaces
this.** Until that lands, nothing else in the plan can be tested at scale.

The replacement has been prototyped and measured, so task 2 is a known
quantity rather than a hope — it produces byte-identical neighbour tables at
`n` = 4, 8, 16, 32, 64, 96 and 128, and it builds the neighbour table in 0.42 s
at `n = 256` and 1.83 s at `n = 512` with peak RSS flat at 169 MB. That is
~1.2 µs/cell against 10.9, and it extrapolates to roughly **30 s and 1.5 GB at
`grid_n = 2048`**. See phase 1 task 2 for the code.

Four other stages have the same shape of problem — correct, vectorised-looking
code with a pure-Python loop over cells hidden inside. They are enumerated in
phase 1, tasks 3 and 4. `simulate_geology` dominates today's profile at 82%,
but it stays at T0 (`grid_n = 256`, ~34 s for 80 ticks) and is **not** on the
T1 critical path, so it is deliberately not optimised.

## Global constraints

- No magic; fictional geography; real physics metaphors.
- v2 only. Do not touch `deeptime/simulate.py`, `deeptime/resources.py` or
  anything else outside `deeptime/v2/` except the CLI and docs.
- No land-fraction target. Sea level is fixed: 0 m present, −120 m LGM.
- Seed + `GENERATOR_VERSION` must reproduce byte-identical output.
- Hard budget: **peak RSS ≤ 11 GB**, leaving headroom on the 15 GB host.
  Exceeding it is a task failure, not a tuning note. Use `np.memmap` backed by
  `/workspace/.cache/deeptime/` when a stage cannot fit.
- Where canon and generated geography disagree, generated output wins.
- Branch: `cursor/fantasy-military-repo-c216`.

## Conventions for the implementing agent

**Dependencies.** `scipy` is not currently installed and the generator is
numpy-only. Phase 1 task 1 adds `scipy>=1.11` to
`maps/generator/requirements.txt`; use `scipy.ndimage`, `scipy.sparse` and
`scipy.spatial` freely after that. Do not add other dependencies.

**Determinism.** Never seed from wall clock, `os.urandom`, `hash()`, or set
iteration order. Derive every stage's generator from one seed sequence so that
adding a stage cannot shift another stage's stream:

```python
root = np.random.SeedSequence(config.seed)
geology_rng, climate_rng, surface_rng = (
    np.random.default_rng(s) for s in root.spawn(3)
)
```

Add new stages by extending the `spawn` count at the **end**, never by
inserting in the middle.

**Dtypes.** Use `float32` for any per-cell field at T1 or finer unless a test
shows it matters; that halves the memory budget. Keep `float64` for
accumulators (drainage area, discharge) and for anything compared against a
tolerance. Index arrays are `int32` up to 2³¹ cells.

**Chunking.** Several existing stages allocate `(N, 8)` or `(N, 8, 3)`
temporaries. At 25.2M cells those are 1.6 GB and 4.8 GB respectively. When you
touch such a stage, rewrite it to process cells in slices of ~2M and accumulate,
rather than materialising the whole temporary. The known offenders are listed
in phase 1 task 4.

**Testing.** `unittest`, in `maps/generator/tests/`, named `test_v2_*.py`.
Every task adds tests and every task ends green. Keep the default test suite
fast: anything that needs `grid_n > 256` goes behind
`@unittest.skipUnless(os.environ.get("DEEPTIME_SLOW"), "slow")`.

**Commits.** One commit per task, message describing the behaviour change.
Push after each phase.

## Verification

Run from `maps/generator/`.

```bash
# Full fast suite — must be green at the end of every task.
python3 -m unittest discover -s tests -v

# Slow suite, including the T1-scale tests.
DEEPTIME_SLOW=1 python3 -m unittest discover -s tests -v

# Re-measure the baseline table.
python3 -c "
import resource, time, gc
from deeptime.v2.grid import CubedSphere
for n in (64, 128, 192, 256):
    gc.collect()
    t = time.perf_counter(); g = CubedSphere.create(n); dt = time.perf_counter() - t
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f'n={n} cells={g.size} t={dt:.2f}s peakRSS={peak:.0f}MB')
"

# End-to-end at current defaults.
python3 -m deeptime --seed 42
```

## Definition of done

- `DEEPTIME_SLOW=1` suite green.
- A T1 world (`grid_n = 2048`) builds within 11 GB peak RSS.
- The promoted world contains a resolvable strait ≤ 20 km, an enclosed sea, a
  great lake, and an archipelago of ≥ 8 islands, each asserted by test.
- Same seed twice produces byte-identical artifacts.
- Every geographic claim in `world/` and `maps/` resolves to an extracted,
  named feature in the promoted world.
- `maps/exports/` and `maps/viewer/public/world/` regenerated and committed.
