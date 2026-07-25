"""CLI: python3 -m deeptime --seed 42"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python3 -m deeptime` from maps/generator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deeptime.simulate import SimConfig, run_until_hooks, save_result, simulate
from deeptime.v2.export import save_world
from deeptime.v2.model import WorldConfig, generate_world
from deeptime.v2.tiers import TIERS, resolve_grid_n
from deeptime.v2.tiles import DEFAULT_DEEP_MAX_ZOOM, DEFAULT_GLOBAL_MAX_ZOOM

GENERATOR = Path(__file__).resolve().parent.parent
EXPORTS = GENERATOR.parent / "exports"
VIEWER_WORLD = GENERATOR.parent / "viewer" / "public" / "world"
_TIER_NAMES = tuple(tier.name for tier in TIERS)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Deep-time spherical world generator")
    p.add_argument(
        "--engine",
        choices=("v2", "v1"),
        default="v2",
        help="v2 spherical pipeline (default) or legacy v1 raster prototype",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=512)
    p.add_argument("--ticks", type=int, default=80)
    p.add_argument("--grid-n", type=int, default=64, help="v2 cubed-sphere face resolution")
    p.add_argument(
        "--tier",
        choices=_TIER_NAMES,
        default="dev",
        help="resolution tier (t0/t1 override --grid-n; dev keeps --grid-n)",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable per-tier geology checkpoints",
    )
    p.add_argument("--era", choices=("present", "lgm"), default="present")
    p.add_argument(
        "--publish",
        action="store_true",
        help=(
            "Smoother viewer export: denser equirect, global tiles through z6, "
            "deep tiles through z8 over Aurelian/Veldara"
        ),
    )
    p.add_argument(
        "--tile-global-max-zoom",
        type=int,
        default=None,
        help="Override global dense tile max zoom (default: 2, or 6 with --publish)",
    )
    p.add_argument(
        "--tile-deep-max-zoom",
        type=int,
        default=None,
        help="Override deep-window tile max zoom (default: 3, or 8 with --publish)",
    )
    p.add_argument(
        "--reroll-hooks",
        action="store_true",
        help="Try nearby seeds until story hooks pass",
    )
    p.add_argument("--max-tries", type=int, default=12)
    p.add_argument(
        "--no-viewer-copy",
        action="store_true",
        help="Unused placeholder; exports always copy to viewer for now",
    )
    p.add_argument(
        "--sweep-seeds",
        type=int,
        default=0,
        help="If >0, score this many seeds (0..N-1) and write promoted-seed.json",
    )
    p.add_argument(
        "--promote-path",
        type=Path,
        default=GENERATOR / "promoted-seed.json",
        help="Where to write the promoted seed record",
    )
    args = p.parse_args(argv)

    if args.width % 2:
        raise SystemExit("width should be even")

    if args.sweep_seeds > 0:
        from deeptime.v2.anchor import promote_best, sweep_seeds

        grid_n = resolve_grid_n(args.tier, args.grid_n)
        results = sweep_seeds(
            range(args.sweep_seeds),
            grid_n=grid_n,
            ticks=args.ticks,
            tier=args.tier,
            use_cache=not args.no_cache,
        )
        payload = promote_best(results, args.promote_path)
        best = results[0]
        print(
            f"sweep n={args.sweep_seeds} status={payload['status']} "
            f"best_seed={best.seed} total={best.score.total:.3f} "
            f"failing={best.score.failing()} -> {args.promote_path}"
        )
        if payload["status"] != "promoted":
            print("failure_counts=", payload.get("failure_counts"))
            raise SystemExit(2)
        return

    if args.engine == "v1":
        cfg = SimConfig(
            width=args.width,
            height=args.height,
            seed=args.seed,
            ticks=args.ticks,
            era=args.era,
        )
        if args.reroll_hooks:
            result = run_until_hooks(cfg, max_tries=args.max_tries)
        else:
            result = simulate(cfg)
        save_result(result)
        return

    grid_n = resolve_grid_n(args.tier, args.grid_n)
    # Full sparse pyramid for real tiers; keep dev/default zooms cheap.
    if args.publish:
        tile_global = DEFAULT_GLOBAL_MAX_ZOOM
        tile_deep = min(8, DEFAULT_DEEP_MAX_ZOOM)
        export_width = max(args.width, 2048)
        export_height = max(args.height, 1024)
        if args.tier == "dev":
            grid_n = max(grid_n, 128)
    elif args.tier in ("t0", "t1"):
        tile_global = DEFAULT_GLOBAL_MAX_ZOOM
        tile_deep = DEFAULT_DEEP_MAX_ZOOM
        export_width = args.width
        export_height = args.height
    else:
        tile_global = 2
        tile_deep = 3
        export_width = args.width
        export_height = args.height
    if args.tile_global_max_zoom is not None:
        tile_global = args.tile_global_max_zoom
    if args.tile_deep_max_zoom is not None:
        tile_deep = args.tile_deep_max_zoom
    world = generate_world(
        WorldConfig(
            seed=args.seed,
            grid_n=grid_n,
            ticks=args.ticks,
            era=args.era,
            export_width=export_width,
            export_height=export_height,
            tier=args.tier,
            use_cache=not args.no_cache,
            tile_global_max_zoom=tile_global,
            tile_deep_max_zoom=tile_deep,
        )
    )
    destinations = [EXPORTS]
    if not args.no_viewer_copy:
        destinations.append(VIEWER_WORLD)
    meta = save_world(world, destinations)
    print(
        f"v2 seed={args.seed} tier={args.tier} land={meta['land_fraction']:.3f} "
        f"plates={meta['plate_count']} continents={meta['continent_count']} "
        f"landmasses={meta['landmass_count']} deposits={meta['resource_deposit_count']}"
    )
    tiles = meta.get("viewer_tiles") or {}
    if tiles.get("tile_count"):
        print(
            f"tiles={tiles['tile_count']} global_z={tiles.get('global_max_zoom')} "
            f"deep_z={tiles.get('deep_max_zoom')} sparse={tiles.get('sparse')}"
        )


if __name__ == "__main__":
    main()
