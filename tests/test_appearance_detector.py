import unittest

import cv2
import numpy as np

from backend.adapters.ball_detector import find_appearance_candidates, find_ball_candidates
from backend.adapters.ball_tracking import TrackingRun
from backend.adapters.video_reader import VideoFrame


class AppearanceDetectorTests(unittest.TestCase):
    region = (50, 50, 700, 380)

    def image(self, x=None, *, value=60, radius=5):
        frame = np.full((432, 768, 3), value, np.uint8)
        if x is not None:
            cv2.circle(frame, (x, 150), radius, (245, 245, 245), -1)
        return frame

    def test_whole_center_survives_small_frame_displacement(self):
        before, current = self.image(198), self.image(200)
        self.assertEqual(find_ball_candidates(before, current, self.region).candidates, [])
        batch = find_appearance_candidates(before, current, self.region)
        self.assertEqual(len(batch.candidates), 1)
        self.assertAlmostEqual(batch.candidates[0].x, 200, delta=.1)
        self.assertAlmostEqual(batch.candidates[0].y, 150, delta=.1)

    def test_static_shapes_and_bright_surroundings_are_rejected(self):
        current = self.image(200)
        self.assertEqual(find_appearance_candidates(current, current, self.region).candidates, [])
        self.assertEqual(find_appearance_candidates(self.image(160, value=170),
                         self.image(200, value=170), self.region).candidates, [])

    def test_sparse_bright_shape_is_rejected(self):
        before = self.image()
        current = before.copy()
        cv2.line(current, (200, 150), (215, 165), (245, 245, 245), 1)
        cv2.line(current, (200, 165), (215, 150), (245, 245, 245), 1)
        self.assertEqual(find_appearance_candidates(before, current, self.region).candidates, [])

    def test_scaled_coordinates_motion_and_search_validation(self):
        for scale in (1, 2):
            before = cv2.resize(self.image(198), None, fx=scale, fy=scale)
            current = cv2.resize(self.image(200), None, fx=scale, fy=scale)
            batch = find_appearance_candidates(before, current, tuple(v * scale for v in self.region))
            self.assertEqual(len(batch.candidates), 1)
            self.assertAlmostEqual(batch.candidates[0].x, 200 * scale, delta=1)
        with self.assertRaises(ValueError):
            find_appearance_candidates(self.image()[:100], self.image(), self.region)
        with self.assertRaises(ValueError):
            find_appearance_candidates(self.image(), self.image(), (0, 0, 900, 432))

    def test_default_pipeline_uses_appearance_and_preserves_confirmation(self):
        run = TrackingRun(self.region)
        for index, x in enumerate([None, 200, 210, 220]):
            batch = run.consume(VideoFrame(index, index / 30, 'presentation', self.image(x, radius=3)))
        self.assertEqual(run.result()['detector'], 'full_shape_v1')
        self.assertEqual(len(batch.candidates), 1)
        self.assertEqual(run.frames[2]['status'], 'tentative')
        self.assertEqual(run.frames[3]['status'], 'observed')
        self.assertNotIn('candidates', run.result()['frames'][3])

    def test_candidate_overflow_remains_explicit(self):
        before = self.image()
        current = before.copy()
        for y in (75, 120, 165, 300):
            for x in (100, 200, 300, 400, 500):
                cv2.circle(current, (x, y), 5, (245, 245, 245), -1)
        batch = find_appearance_candidates(before, current, self.region)
        self.assertTrue(batch.truncated)
        self.assertEqual(len(batch.candidates), 12)


class RelativeBackgroundTests(unittest.TestCase):
    region = AppearanceDetectorTests.region
    image = AppearanceDetectorTests.image
    def test_relative_contrast_rescues_only_high_contrast_bright_background(self):
        for value, expected in ((170, 1), (200, 0)):
            before, current = self.image(160, value=value, radius=3), self.image(200, value=value, radius=3)
            diagnostics = []
            candidates = find_appearance_candidates(before, current, self.region,
                                                     relative_background=True, on_component=diagnostics.append)
            self.assertEqual(len(candidates.candidates), expected)
            if expected:
                self.assertTrue(any(row['foreground_value'] is not None for row in diagnostics))
            self.assertEqual(find_appearance_candidates(before, current, self.region).candidates, [])

    def test_experiment_remains_opt_in_and_legacy_is_reproducible(self):
        run = TrackingRun(self.region, sparse_motion=True)
        legacy = TrackingRun(self.region, sparse_motion=True, appearance_filter=False)
        for i, x in enumerate((None, 200, None, 210, None, 220)):
            run.consume(VideoFrame(i, i / 60, 'presentation', self.image(x, value=170, radius=3)))
        self.assertEqual(run.result()['detector'], 'full_shape_relative_v1')
        self.assertEqual(run.result()['initialization'], 'bounded_paths_v1')
        self.assertEqual(run.frames[-1]['observation'], (220, 150))
        self.assertFalse(legacy.sparse_motion)
