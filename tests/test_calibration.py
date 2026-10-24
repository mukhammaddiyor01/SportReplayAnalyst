import unittest

import cv2
import httpx
import numpy as np

from backend.adapters.table_geometry import table_homography
from backend.main import create_app
from backend.services.calibration import CalibrationError, validate_corners


class GeometryTests(unittest.TestCase):
    def test_perspective_corners_map_to_unit_table_plane(self):
        corners = [(180, 80), (600, 90), (590, 320), (190, 310)]
        validated = validate_corners(corners, 768, 432)
        matrix = np.asarray(table_homography(validated))
        projected = cv2.perspectiveTransform(np.asarray([corners], dtype=np.float32), matrix)
        np.testing.assert_allclose(projected[0], [(0, 0), (1, 0), (1, 1), (0, 1)], atol=1e-6)

    def test_invalid_geometries_are_rejected(self):
        cases = [[], [(1, 1)] * 4,
                 [(10, 10), (50, 50), (50, 10), (10, 50)],
                 [(10, 10), (10, 50), (50, 50), (50, 10)],
                 [(0, 0), (100, 0), (100, 50), (0, 50)],
                 [(10, 10), (11, 10), (11, 11), (10, 11)],
                 [(float("nan"), 10), (50, 10), (50, 50), (10, 50)],
                 [(10, 10), (30, 10), (50, 10), (10, 50)],
                 [(10, 10), (50, 10), (20, 20), (10, 50)]]
        for corners in cases:
            with self.subTest(corners=corners), self.assertRaises(CalibrationError):
                validate_corners(corners, 100, 100)


class CalibrationApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=create_app()),
                                       base_url="http://127.0.0.1:8014")
        self.payload = {"width": 100, "height": 100,
                        "corners": [[10, 10], [90, 10], [90, 90], [10, 90]]}

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_calibration_response_and_same_origin(self):
        response = await self.client.post("/api/calibration", json=self.payload,
                                          headers={"Origin": "http://127.0.0.1:8014"})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["coordinate_space"], "unit_table_plane")
        self.assertIn("airborne", result["warning"])
        self.assertEqual(len(result["homography"]), 3)

    async def test_cross_origin_is_rejected(self):
        response = await self.client.post("/api/calibration", json=self.payload,
                                          headers={"Origin": "https://untrusted.example"})
        self.assertEqual(response.status_code, 403)

    async def test_bad_corner_and_dimension_payloads(self):
        for change in [{"width": 99999}, {"corners": [[1, 2, 3]] * 4},
                       {"corners": [[1, 2]] * 4}, {"filename": "unused"}]:
            response = await self.client.post("/api/calibration", json=self.payload | change)
            self.assertEqual(response.status_code, 422)
