"""Sparse Web Mercator tile pyramid tests."""

from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from deeptime.v2.tiles import (
    DEFAULT_DEEP_WINDOWS,
    MERCATOR_MAX_LAT,
    DeepWindow,
    dense_tile_count,
    sparse_tile_count,
    tile_lon_lat_bounds,
    tiles_covering_window,
    write_mercator_tiles,
)


class MercatorTileTests(unittest.TestCase):
    def test_writes_expected_xyz_layout_and_samples_equirect(self) -> None:
        # Distinct colors by latitude band so we can check pole-edge sampling.
        height, width = 180, 360
        image = np.zeros((height, width, 3), dtype=np.uint8)
        image[:20] = (240, 240, 240)  # near north
        image[80:100] = (20, 180, 40)  # equator band
        image[-20:] = (200, 200, 220)  # near south
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "color"
            meta = write_mercator_tiles(image, root, max_zoom=1, tile_size=64)
            self.assertEqual(meta["tile_count"], 1 + 4)
            self.assertTrue((root / "0" / "0" / "0.png").is_file())
            self.assertTrue((root / "1" / "0" / "0.png").is_file())
            z0 = np.array(Image.open(root / "0" / "0" / "0.png"))
            self.assertEqual(z0.shape, (64, 64, 3))
            # Top row of z0 is the north mercator edge (~85°), not empty.
            self.assertGreater(int(z0[0].mean()), 30)
            self.assertAlmostEqual(meta["mercator_max_lat"], MERCATOR_MAX_LAT)

    def test_mercator_max_lat_matches_epsg_3857(self) -> None:
        expected = math.degrees(2 * math.atan(math.exp(math.pi)) - math.pi / 2)
        self.assertAlmostEqual(MERCATOR_MAX_LAT, expected, places=10)

    def test_sparse_tile_counts_match_layout_not_dense(self) -> None:
        window = DeepWindow("test", 0.0, 10.0, 30.0, 40.0)
        global_z = 2
        deep_z = 4
        expected = sparse_tile_count(
            global_max_zoom=global_z,
            deep_max_zoom=deep_z,
            deep_windows=(window,),
        )
        dense = dense_tile_count(deep_z)
        self.assertLess(expected, dense)
        self.assertEqual(dense_tile_count(6), 5461)

        height, width = 180, 360
        image = np.full((height, width, 3), 40, dtype=np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "color"
            meta = write_mercator_tiles(
                image,
                root,
                global_max_zoom=global_z,
                deep_max_zoom=deep_z,
                deep_windows=(window,),
                tile_size=32,
            )
            self.assertTrue(meta["sparse"])
            self.assertEqual(meta["tile_count"], expected)
            self.assertLess(meta["tile_count"], dense)
            self.assertTrue((root / "coverage.json").is_file())
            # Outside the deep window at z=deep_z there must be no tiles.
            deep_tiles = tiles_covering_window(window, deep_z)
            self.assertGreater(len(deep_tiles), 0)
            on_disk = {
                (int(p.parent.name), int(p.stem))
                for p in (root / str(deep_z)).rglob("*.png")
            }
            self.assertEqual(on_disk, set(deep_tiles))
            outside_x = (1 << deep_z) - 1
            outside_y = (1 << deep_z) - 1
            if (outside_x, outside_y) not in deep_tiles:
                self.assertFalse(
                    (root / str(deep_z) / str(outside_x) / f"{outside_y}.png").is_file()
                )

    def test_sparse_write_removes_stale_tiles(self) -> None:
        """A prior dense pyramid must not survive a sparse rewrite."""
        window = DeepWindow("test", 0.0, 10.0, 30.0, 40.0)
        height, width = 90, 180
        image = np.full((height, width, 3), 80, dtype=np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "color"
            # Plant a stale full z=3 tile outside the deep window.
            stale = root / "3" / "7" / "7.png"
            stale.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(
                np.full((32, 32, 3), 255, dtype=np.uint8), mode="RGB"
            ).save(stale)
            self.assertTrue(stale.is_file())
            write_mercator_tiles(
                image,
                root,
                global_max_zoom=1,
                deep_max_zoom=2,
                deep_windows=(window,),
                tile_size=32,
            )
            self.assertFalse(stale.is_file())
            self.assertFalse((root / "3").exists())
            self.assertTrue((root / "0" / "0" / "0.png").is_file())

    def test_deep_tile_differs_from_overzoomed_parent(self) -> None:
        """z_deep sampling must carry real detail, not parent upscaling."""
        window = DeepWindow("veldara", 0.0, 8.0, 32.0, 40.0)
        height, width = 1024, 2048
        image = np.full((height, width, 3), 30, dtype=np.uint8)
        # Fine checkerboard only inside the deep window.
        lon = np.linspace(-180, 180, width, endpoint=False)
        lat = np.linspace(90, -90, height, endpoint=False)
        lon_grid, lat_grid = np.meshgrid(lon, lat)
        inside = (
            (lon_grid >= window.lon_min)
            & (lon_grid <= window.lon_max)
            & (lat_grid >= window.lat_min)
            & (lat_grid <= window.lat_max)
        )
        checker = (
            (lon_grid * 120).astype(np.int32) + (lat_grid * 120).astype(np.int32)
        ) % 2
        image[inside] = np.where(
            checker[inside, None] == 0,
            np.array([220, 40, 40], dtype=np.uint8),
            np.array([40, 40, 220], dtype=np.uint8),
        )

        global_z = 2
        deep_z = 5
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "color"
            meta = write_mercator_tiles(
                image,
                root,
                global_max_zoom=global_z,
                deep_max_zoom=deep_z,
                deep_windows=(window,),
                tile_size=64,
            )
            self.assertGreater(meta["deep_tile_count"], 0)
            tiles = tiles_covering_window(window, deep_z)
            self.assertGreater(len(tiles), 0)
            # Prefer a tile whose centre sits inside the painted window.
            chosen = None
            for tx, ty in tiles:
                lon0, lon1, lat0, lat1 = tile_lon_lat_bounds(deep_z, tx, ty)
                clon = 0.5 * (lon0 + lon1)
                clat = 0.5 * (lat0 + lat1)
                if (
                    window.lon_min <= clon <= window.lon_max
                    and window.lat_min <= clat <= window.lat_max
                ):
                    chosen = (tx, ty)
                    break
            self.assertIsNotNone(chosen)
            tx, ty = chosen  # type: ignore[misc]
            child = np.array(Image.open(root / str(deep_z) / str(tx) / f"{ty}.png"))
            parent_x, parent_y = tx // 2, ty // 2
            parent_path = root / str(deep_z - 1) / str(parent_x) / f"{parent_y}.png"
            self.assertTrue(parent_path.is_file())
            parent = np.array(Image.open(parent_path))
            # Nearest-neighbour overzoom of the parent quadrant matching the child.
            qx = tx % 2
            qy = ty % 2
            half = parent.shape[0] // 2
            quadrant = parent[qy * half : (qy + 1) * half, qx * half : (qx + 1) * half]
            overzoom = np.repeat(np.repeat(quadrant, 2, axis=0), 2, axis=1)
            overzoom = overzoom[: child.shape[0], : child.shape[1]]
            diff = np.abs(child.astype(np.int16) - overzoom.astype(np.int16)).mean()
            self.assertGreater(float(diff), 5.0)

    def test_default_windows_named_aurelian_and_veldara(self) -> None:
        names = {w.name for w in DEFAULT_DEEP_WINDOWS}
        self.assertEqual(names, {"aurelian", "veldara"})


if __name__ == "__main__":
    unittest.main()
