from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import numpy as np

from backend.adapters.ball_detector import find_ball_candidates
from backend.services.ball_observations import BallCandidate, CandidateBatch
from evaluation.evaluate_ball_candidates import evaluate, score_candidates


class BallDetectorTests(unittest.TestCase):
    def setUp(self):
        self.background = np.full((432, 768, 3), (80, 60, 30), np.uint8)
        cv2.putText(self.background, "Static white overlay", (120, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, .8, (230, 230, 230), 2)
        self.region = (50, 50, 700, 380)

    def ball(self, center):
        image = self.background.copy()
        cv2.circle(image, center, 5, (245, 245, 245), -1)
        return image

    def test_moving_bright_ball_keeps_source_coordinates(self):
        batch = find_ball_candidates(self.ball((160, 150)), self.ball((200, 150)), self.region)
        self.assertFalse(batch.truncated)
        self.assertEqual(len(batch.candidates), 1)
        self.assertAlmostEqual(batch.candidates[0].x, 200, delta=1)
        self.assertAlmostEqual(batch.candidates[0].y, 150, delta=1)

    def test_static_overlays_and_static_white_object_do_not_move(self):
        image = self.ball((200, 150))
        self.assertEqual(find_ball_candidates(image, image, self.region).candidates, [])

    def test_blurred_ball_can_remain_a_candidate(self):
        current = self.background.copy()
        cv2.ellipse(current, (200, 150), (7, 2), 0, 0, 360, (245, 245, 245), -1)
        batch = find_ball_candidates(self.background, current, self.region)
        self.assertEqual(len(batch.candidates), 1)
        self.assertAlmostEqual(batch.candidates[0].x, 200, delta=1)

    def test_multiple_candidates_remain_ambiguous(self):
        current = self.ball((200, 150))
        cv2.circle(current, (280, 150), 5, (245, 245, 245), -1)
        batch = find_ball_candidates(self.background, current, self.region)
        self.assertEqual(len(batch.candidates), 2)
        self.assertTrue(score_candidates(batch, (200, 150), 8)["ambiguous"])

    def test_tiny_dim_large_and_long_objects_are_rejected(self):
        objects = []
        tiny = self.background.copy()
        cv2.circle(tiny, (200, 150), 2, (245, 245, 245), -1)
        objects.append(tiny)
        dim = self.background.copy()
        cv2.circle(dim, (200, 150), 5, (100, 100, 100), -1)
        objects.append(dim)
        large = self.background.copy()
        cv2.rectangle(large, (200, 100), (300, 180), (245, 245, 245), -1)
        objects.append(large)
        line = self.background.copy()
        cv2.line(line, (200, 100), (500, 100), (245, 245, 245), 3)
        objects.append(line)
        for image in objects:
            with self.subTest():
                self.assertEqual(find_ball_candidates(self.background, image, self.region).candidates, [])

    def test_scaled_source_geometry_has_scaled_candidate_coordinates(self):
        before = cv2.resize(self.ball((160, 150)), (1536, 864))
        current = cv2.resize(self.ball((200, 150)), (1536, 864))
        batch = find_ball_candidates(before, current, (100, 100, 1400, 760))
        self.assertEqual(len(batch.candidates), 1)
        self.assertAlmostEqual(batch.candidates[0].x, 400, delta=2)
        self.assertAlmostEqual(batch.candidates[0].y, 300, delta=2)

    def test_candidate_limit_is_explicit(self):
        current = self.background.copy()
        for y in [75, 120, 165, 300]:
            for x in [100, 200, 300, 400, 500]:
                cv2.circle(current, (x, y), 5, (245, 245, 245), -1)
        batch = find_ball_candidates(self.background, current, self.region)
        self.assertTrue(batch.truncated)
        self.assertEqual(len(batch.candidates), 12)

    def test_invalid_source_or_search_window_is_rejected(self):
        with self.assertRaises(ValueError):
            find_ball_candidates(self.background[:100], self.background, self.region)
        for region in [(-1, 0, 20, 20), (50, 50, 10, 10), (0, 0, 900, 432)]:
            with self.assertRaises(ValueError):
                find_ball_candidates(self.background, self.background, region)

    def test_small_candidate_area_override_scales_with_source(self):
        current = self.background.copy()
        cv2.circle(current, (200, 150), 3, (245, 245, 245), -1)
        self.assertEqual(find_ball_candidates(self.background, current, self.region).candidates, [])
        for scale in (1, 2):
            batch = find_ball_candidates(cv2.resize(self.background, None, fx=scale, fy=scale),
                                         cv2.resize(current, None, fx=scale, fy=scale),
                                         tuple(value * scale for value in self.region), minimum_area=25)
            self.assertEqual(len(batch.candidates), 1)
            self.assertAlmostEqual(batch.candidates[0].x, 200 * scale, delta=2)
        for invalid in (0, -1, 181, float('nan')):
            with self.assertRaises(ValueError):
                find_ball_candidates(self.background, current, self.region, minimum_area=invalid)


class CandidateEvaluationTests(unittest.TestCase):
    def test_one_reference_ball_cannot_match_two_observations(self):
        one = BallCandidate(100, 100, 50, (95, 95, 10, 10))
        two = BallCandidate(101, 100, 50, (96, 95, 10, 10))
        batch = CandidateBatch([one, two])
        score = score_candidates(batch, (100, 100), 8)
        self.assertTrue(score["hit"])
        self.assertEqual(score["false_candidates"], 1)
        self.assertEqual(score_candidates(batch, None, 8)["false_candidates"], 2)

    def test_wrong_video_is_not_scored_against_other_footage(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "other.mp4"
            path.write_bytes(b"different video")
            with self.assertRaisesRegex(ValueError, "does not match"):
                evaluate(path, {"sha256": "not this file"}, "held_out")
