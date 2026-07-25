"""Field contract and generator version stamping."""

from __future__ import annotations

import unittest
from copy import deepcopy

from deeptime.v2.contract import (
    GENERATOR_VERSION,
    ContractError,
    validate_contract,
)
from deeptime.v2.export import save_world
from deeptime.v2.model import WorldConfig, generate_world


class ContractTests(unittest.TestCase):
    def test_normal_world_validates_clean(self) -> None:
        world = generate_world(WorldConfig(seed=7, grid_n=32, ticks=8))
        validate_contract(world.geology, world.climate, world.hydrology)

    def test_missing_lithology_key_raises_named_error(self) -> None:
        world = generate_world(WorldConfig(seed=7, grid_n=32, ticks=8))
        geology = deepcopy(world.geology)
        del geology.lithology["felsic"]
        with self.assertRaises(ContractError) as ctx:
            validate_contract(geology, world.climate, world.hydrology)
        self.assertIn("felsic", str(ctx.exception))

    def test_meta_includes_generator_version_and_seed(self) -> None:
        import tempfile
        from pathlib import Path

        world = generate_world(
            WorldConfig(
                seed=11,
                grid_n=32,
                ticks=8,
                tile_global_max_zoom=1,
                tile_deep_max_zoom=1,
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            meta = save_world(world, [Path(tmp)])
        self.assertEqual(meta["seed"], 11)
        self.assertEqual(meta["generator_version"], GENERATOR_VERSION)
        self.assertEqual(GENERATOR_VERSION, "2.2.0")


if __name__ == "__main__":
    unittest.main()
