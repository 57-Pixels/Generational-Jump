"""Per-tier resumable checkpoints keyed by seed and generator version."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .contract import GENERATOR_VERSION


def checkpoint_path(
    cache_dir: Path, seed: int, version: str, tier: str
) -> Path:
    return Path(cache_dir) / str(seed) / version / f"{tier}.npz"


def save(
    cache_dir: Path,
    tier: str,
    seed: int,
    version: str,
    payload: dict[str, Any],
) -> Path:
    """Write ``payload`` arrays (and optional ``meta`` dict) to an npz checkpoint."""
    path = checkpoint_path(cache_dir, seed, version, tier)
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays: dict[str, Any] = {}
    meta = {"seed": seed, "version": version, "tier": tier}
    for key, value in payload.items():
        if key == "meta" and isinstance(value, dict):
            meta.update(value)
            continue
        arrays[key] = np.asarray(value)
    arrays["_meta_json"] = np.asarray(json.dumps(meta, sort_keys=True))
    np.savez_compressed(path, **arrays)
    return path


def load(
    cache_dir: Path,
    tier: str,
    seed: int,
    version: str = GENERATOR_VERSION,
) -> dict[str, Any] | None:
    """Return payload dict or ``None`` on cache miss.

    A version or seed mismatch is always a miss — never a silent stale hit.
    """
    path = checkpoint_path(cache_dir, seed, version, tier)
    if not path.is_file():
        return None
    with np.load(path, allow_pickle=False) as data:
        meta = json.loads(str(data["_meta_json"]))
        if int(meta.get("seed", -1)) != int(seed):
            return None
        if str(meta.get("version", "")) != str(version):
            return None
        if str(meta.get("tier", "")) != str(tier):
            return None
        payload = {key: data[key] for key in data.files if key != "_meta_json"}
        payload["meta"] = meta
        return payload
