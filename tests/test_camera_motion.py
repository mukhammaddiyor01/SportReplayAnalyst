from dataclasses import replace
import unittest

import cv2
import numpy as np

from backend.adapters.camera_motion import CameraMotionEstimator
from backend.services.camera_motion import MotionEvidence, is_reliable, summarize_motion


def textured_scene():
    image = np.full((360, 640, 3), 75, np.uint8)
    random = np.random.default_rng(142)
    for _ in range(450):
        x, y = random.integers([8, 8], [632, 352])
        color = int(random.integers(100, 250))
        cv2.circle(image, (int(x), int(y)), int(random.integers(2, 6)), (color,) * 3, -1)
    return image


class CameraAdapterTests(unittest.TestCase):
    def test_fixed_scene_is_supported(self):
        image = textured_scene()
        evidence = CameraMotionEstimator(image).measure(image, 15, .5)
        self.assertTrue(is_reliable(evidence), evidence)
        self.assertLess(evidence.displacement_px, .05)

    def test_translation_uses_original_pixel_coordinates_after_resize(self):
        image = cv2.resize(textured_scene(), (1280, 720))
        moved = cv2.warpAffine(image, np.float32([[1, 0, 24], [0, 1, 14]]), (1280, 720))
        evidence = CameraMotionEstimator(image).measure(moved, 15, .5)
        self.assertTrue(is_reliable(evidence), evidence)
        self.assertAlmostEqual(evidence.displacement_px, np.hypot(24, 14), delta=1)
        report = summarize_motion([evidence], 1280, 720, .04)
        self.assertEqual(report["status"], "movement_detected")
        self.assertEqual(report["calibration_reuse"], "blocked")

    def test_rotation_is_not_mistaken_for_a_fixed_camera(self):
        image = textured_scene()
        matrix = cv2.getRotationMatrix2D((320, 180), 2, 1)
        moved = cv2.warpAffine(image, matrix, (640, 360))
        evidence = CameraMotionEstimator(image).measure(moved, 15, .5)
        self.assertTrue(is_reliable(evidence), evidence)
        self.assertGreater(evidence.displacement_px, 10)

    def test_small_moving_foreground_does_not_dominate_static_scene(self):
        image = textured_scene()
        changed = image.copy()
        changed[50:105, 80:135] = 200
        evidence = CameraMotionEstimator(image).measure(changed, 15, .5)
        self.assertTrue(is_reliable(evidence), evidence)
        self.assertLess(evidence.displacement_px, .5)

    def test_blank_or_occluded_images_are_inconclusive(self):
        blank = np.zeros((360, 640, 3), np.uint8)
        cases = [(blank, blank), (textured_scene(), blank)]
        for reference, current in cases:
            evidence = CameraMotionEstimator(reference).measure(current, 15, .5)
            self.assertFalse(is_reliable(evidence))
            report = summarize_motion([evidence], 640, 360, .04)
            self.assertEqual(report["status"], "uncertain")
            self.assertEqual(report["calibration_reuse"], "blocked")


class CameraEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.good = MotionEvidence(15, .5, 100, 90, .5, .8, .8, .1)

    def test_no_motion_requires_temporal_and_spatial_support(self):
        report = summarize_motion([self.good, replace(self.good, frame_index=30, timestamp_seconds=1)],
                                  640, 360, .04)
        self.assertEqual(report["status"], "no_movement_detected")
        self.assertEqual(report["calibration_reuse"], "review_required")
        for bad in [replace(self.good, inlier_points=4), replace(self.good, coverage_fraction=.01),
                    replace(self.good, vertical_span=.05), replace(self.good, matched_points=1000),
                    replace(self.good, displacement_px=float("nan"))]:
            with self.subTest(evidence=bad):
                self.assertFalse(is_reliable(bad))
                self.assertEqual(summarize_motion([self.good, bad], 640, 360, .04)["status"], "uncertain")

    def test_short_coverage_or_time_gaps_cannot_clear_calibration(self):
        self.assertEqual(summarize_motion([], 640, 360, .04)["status"], "uncertain")
        self.assertEqual(summarize_motion([self.good], 640, 360, .04)["status"], "uncertain")
        self.assertEqual(summarize_motion([self.good] * 2, 640, 360, 1.5)["status"], "uncertain")

    def test_later_loss_of_evidence_does_not_erase_detected_movement(self):
        moved = replace(self.good, displacement_px=10)
        unknown = replace(self.good, inlier_points=0)
        report = summarize_motion([moved, unknown], 640, 360, .04)
        self.assertEqual(report["status"], "movement_detected")
        self.assertEqual(report["inconclusive_comparisons"], 1)
