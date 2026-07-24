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
    args = p.parse_args(argv)

    if args.width % 2:
        raise SystemExit("width should be even")

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
    world = generate_world(
        WorldConfig(
            seed=args.seed,
            grid_n=grid_n,
            ticks=args.ticks,
            era=args.era,
            export_width=args.width,
            export_height=args.height,
            tier=args.tier,
            use_cache=not args.no_cache,
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


if __name__ == "__main__":
    main()
