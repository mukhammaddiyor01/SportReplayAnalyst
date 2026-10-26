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
            batch = run.consume(VideoFrame(index, index / 30, "presentation", image))
            self.assertEqual(bool(batch.candidates), x is not None)
            self.assertNotIn('candidates', run.frames[-1])
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

    def test_small_ball_continues_but_cannot_initialize_or_restart_a_track(self):
        def frame(index, x, radius):
            image = np.full((432, 768, 3), (80, 60, 30), np.uint8)
            if x is not None:
                cv2.circle(image, (x, 150), radius, (245, 245, 245), -1)
            return VideoFrame(index, index / 30, "presentation", image)

        run = TrackingRun((100, 50, 500, 300), small_candidate_continuation=True)
        for i, x in enumerate([None, 200, 210, 220]):
            run.consume(frame(i, x, 5))
        self.assertEqual(run.frames[-1]['status'], 'observed')
        run.consume(frame(4, 230, 3))
        self.assertEqual(run.frames[-1]['status'], 'observed')
        self.assertAlmostEqual(run.frames[-1]['observation'][0], 230, delta=1)
        run.consume(frame(11, 300, 3))
        self.assertEqual(run.frames[-1]['status'], 'searching')
        self.assertIsNone(run.frames[-1]['observation'])

        fresh = TrackingRun((100, 50, 500, 300), small_candidate_continuation=True)
        for i, x in enumerate([None, 200, 210, 220]):
            fresh.consume(frame(i, x, 3))
        self.assertEqual(fresh.result()['track_count'], 0)

    def test_small_distractors_still_withhold_ambiguous_continuation(self):
        run = TrackingRun((100, 50, 500, 300), small_candidate_continuation=True)
        for i, x in enumerate([None, 200, 210, 220, 230]):
            image = np.full((432, 768, 3), (80, 60, 30), np.uint8)
            if x is not None:
                cv2.circle(image, (x, 150), 5, (245, 245, 245), -1)
            if i == 4:
                cv2.circle(image, (230, 160), 3, (245, 245, 245), -1)
            run.consume(VideoFrame(i, i / 30, "presentation", image))
        self.assertEqual(run.frames[-1]['status'], 'ambiguous')
        self.assertIsNone(run.frames[-1]['observation'])

    def test_legacy_path_keeps_strict_area_during_continuation(self):
        run = TrackingRun((100, 50, 500, 300), appearance_filter=False)
        for i, x in enumerate([None, 200, 210, 220, 230]):
            image = np.full((432, 768, 3), (80, 60, 30), np.uint8)
            if x is not None:
                cv2.circle(image, (x, 150), 3 if i == 4 else 5, (245, 245, 245), -1)
            run.consume(VideoFrame(i, i / 30, "presentation", image))
        self.assertEqual(run.frames[-1]['status'], 'predicted')
        self.assertIsNone(run.frames[-1]['observation'])
