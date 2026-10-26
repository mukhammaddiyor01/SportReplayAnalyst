import unittest

import cv2
import numpy as np

from backend.adapters.ball_tracking import TrackingRun
from backend.adapters.video_reader import VideoError, VideoFrame


class TrackingRunTests(unittest.TestCase):
    def test_real_candidates_feed_temporal_rules_and_source_records(self):
        run = TrackingRun((100, 50, 500, 300))
        for index, x in enumerate([None, 200, 210, 220, None, 240]):
            image = np.full((432, 768, 3), (80, 60, 30), np.uint8)
            if x is not None:
                cv2.circle(image, (x, 150), 5, (245, 245, 245), -1)
            run.consume(VideoFrame(index, index / 30, "presentation", image))
        result = run.result()
        self.assertEqual(len(result["frames"]), 6)
        self.assertEqual(result["track_count"], 1)
        self.assertEqual(result["frames"][3]["status"], "observed")
        self.assertEqual(result["frames"][4]["status"], "predicted")
        self.assertIsNone(result["frames"][4]["observation"])
        self.assertTrue(result["frames"][5]["break_before"])
        self.assertEqual(result["frames"][5]["timestamp_seconds"], 5 / 30)

    def test_region_must_match_decoded_dimensions(self):
        run = TrackingRun((0, 0, 1000, 600))
        image = np.zeros((48, 64, 3), np.uint8)
        with self.assertRaises(VideoError):
            run.consume(VideoFrame(0, 0, "presentation", image))

    def test_empty_run_and_independent_runs_have_no_fabricated_track(self):
        first = TrackingRun((0, 0, 64, 48))
        second = TrackingRun((0, 0, 64, 48))
        first.consume(VideoFrame(0, 0, "fps_fallback", np.zeros((48, 64, 3), np.uint8)))
        self.assertEqual(second.result()["frames"], [])
        self.assertEqual(first.result()["track_count"], 0)
        self.assertEqual(first.result()["frames"][0]["timestamp_source"], "fps_fallback")
