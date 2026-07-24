"""Tier checkpoints: hit/miss, version invalidation, byte identity."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from deeptime.v2 import checkpoint as checkpoint_mod
from deeptime.v2.checkpoint import load, save
from deeptime.v2.contract import GENERATOR_VERSION
from deeptime.v2.model import WorldConfig, generate_world
from deeptime.v2.tiers import get_tier, resolve_grid_n


class TierTests(unittest.TestCase):
    def test_resolve_grid_n(self) -> None:
        self.assertEqual(resolve_grid_n("t0", 64), 256)
        self.assertEqual(resolve_grid_n("t1", 64), 2048)
        self.assertEqual(resolve_grid_n("dev", 48), 48)
        self.assertEqual(get_tier("t0").target_km, 35.0)


class CheckpointTests(unittest.TestCase):
    def test_same_seed_writes_byte_identical_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {"elevation_m": np.arange(12, dtype=np.float64), "meta": {"k": 1}}
            a = save(root, "t0", 42, "2.1.0", payload)
            b = save(root, "t0", 42, "2.1.0", payload)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_version_mismatch_is_cache_miss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save(root, "t0", 7, "2.1.0", {"x": np.ones(4)})
            self.assertIsNone(load(root, "t0", 7, version="9.9.9"))
            hit = load(root, "t0", 7, version="2.1.0")
            self.assertIsNotNone(hit)
            np.testing.assert_array_equal(hit["x"], np.ones(4))

    def test_second_generate_world_is_cache_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = WorldConfig(
                seed=3,
                grid_n=12,
                ticks=6,
                tier="dev",
                cache_dir=root,
                use_cache=True,
                validate=False,
                export_width=64,
                export_height=32,
            )
            first = generate_world(config)
            # Poison simulate_geology — cache must prevent a call.
            with mock.patch(
                "deeptime.v2.model.simulate_geology",
                side_effect=AssertionError("cache missed; geology recomputed"),
            ):
                second = generate_world(config)
            np.testing.assert_allclose(
                first.geology.elevation_m, second.geology.elevation_m
            )

    def test_bumping_generator_version_invalidates_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = WorldConfig(
                seed=5,
                grid_n=12,
                ticks=6,
                tier="dev",
                cache_dir=root,
                use_cache=True,
                validate=False,
                export_width=64,
                export_height=32,
            )
            generate_world(config)
            with mock.patch.object(checkpoint_mod, "GENERATOR_VERSION", "9.9.9"):
                with mock.patch(
                    "deeptime.v2.model.GENERATOR_VERSION", "9.9.9"
                ):
                    # Must recompute under the new version.
                    calls = {"n": 0}
                    real = __import__(
                        "deeptime.v2.geology", fromlist=["simulate_geology"]
                    ).simulate_geology

                    def wrapped(*args, **kwargs):
                        calls["n"] += 1
                        return real(*args, **kwargs)

                    with mock.patch("deeptime.v2.model.simulate_geology", wraps=wrapped):
                        generate_world(config)
                    self.assertEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()
