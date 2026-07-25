"""Publish CLI resolution for high-quality viewer packages."""

from __future__ import annotations

import unittest

from deeptime.publish import resolve_publish_settings
from deeptime.v2.tiles import DEFAULT_DEEP_MAX_ZOOM, DEFAULT_GLOBAL_MAX_ZOOM


class PublishSettingsTests(unittest.TestCase):
    def test_publish_selects_t1_morphology_and_full_tile_pyramid(self) -> None:
        settings = resolve_publish_settings(
            tier="dev",
            grid_n=64,
            width=1024,
            height=512,
            publish=True,
        )
        self.assertEqual(settings.tier, "t1")
        self.assertEqual(settings.grid_n, 2048)
        self.assertEqual(settings.tile_global_max_zoom, DEFAULT_GLOBAL_MAX_ZOOM)
        self.assertEqual(settings.tile_deep_max_zoom, DEFAULT_DEEP_MAX_ZOOM)
        self.assertGreaterEqual(settings.export_width, 4096)
        self.assertGreaterEqual(settings.export_height, 2048)

    def test_explicit_tier_overrides_publish_morphology(self) -> None:
        settings = resolve_publish_settings(
            tier="t0",
            grid_n=64,
            width=1024,
            height=512,
            publish=True,
        )
        self.assertEqual(settings.tier, "t0")
        self.assertEqual(settings.grid_n, 256)
        self.assertEqual(settings.tile_deep_max_zoom, DEFAULT_DEEP_MAX_ZOOM)

    def test_non_publish_dev_stays_cheap(self) -> None:
        settings = resolve_publish_settings(
            tier="dev",
            grid_n=64,
            width=1024,
            height=512,
            publish=False,
        )
        self.assertEqual(settings.tier, "dev")
        self.assertEqual(settings.grid_n, 64)
        self.assertEqual(settings.tile_global_max_zoom, 2)
        self.assertEqual(settings.tile_deep_max_zoom, 3)
        self.assertEqual(settings.export_width, 1024)


if __name__ == "__main__":
    unittest.main()
