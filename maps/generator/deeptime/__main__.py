"""CLI: python3 -m deeptime --seed 42"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python3 -m deeptime` from maps/generator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deeptime.simulate import SimConfig, run_until_hooks, save_result, simulate


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description="Deep-time plate world generator v1")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--width", type=int, default=1024)
    p.add_argument("--height", type=int, default=512)
    p.add_argument("--ticks", type=int, default=80)
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


if __name__ == "__main__":
    main()
