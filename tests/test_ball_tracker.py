import unittest

from backend.services.ball_observations import BallCandidate, CandidateBatch
from backend.services.ball_tracker import BallTracker


def batch(*points, truncated=False):
    return CandidateBatch([BallCandidate(x, y, 50, (int(x) - 3, int(y) - 3, 6, 6))
                           for x, y in points], truncated)


class BallTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = BallTracker(768, 432)

    def initialize(self):
        self.tracker.update(batch((100, 150)), 0, 0)
        self.tracker.update(batch((110, 150)), 1, .033)
        return self.tracker.update(batch((120, 150)), 2, .066)

    def test_requires_three_coherent_moving_observations(self):
        one = self.tracker.update(batch((100, 150)), 0, 0)
        two = self.tracker.update(batch((110, 150)), 1, .033)
        three = self.tracker.update(batch((120, 150)), 2, .066)
        self.assertEqual([one.status, two.status, three.status], ["tentative", "tentative", "observed"])
        self.assertIsNone(two.observation)
        self.assertEqual(three.observation, (120, 150))
        self.assertTrue(three.break_before)

    def test_stationary_false_object_does_not_initialize(self):
        for index in range(10):
            result = self.tracker.update(batch((100, 150)), index, index / 30)
            self.assertEqual(result.status, "tentative")
            self.assertIsNone(result.observation)

    def test_large_distractor_is_not_preferred_over_motion_match(self):
        initial = self.initialize()
        result = self.tracker.update(batch((600, 250), (130, 150)), 3, .099)
        self.assertEqual(result.observation, (130, 150))
        self.assertEqual(result.track_id, initial.track_id)
        self.assertFalse(result.break_before)

    def test_close_competing_candidates_are_ambiguous(self):
        self.initialize()
        result = self.tracker.update(batch((130, 150), (133, 151)), 3, .099)
        self.assertEqual(result.status, "ambiguous")
        self.assertIsNone(result.observation)
        self.assertIsNotNone(result.prediction)

    def test_saturated_batch_is_never_treated_as_unique(self):
        self.initialize()
        result = self.tracker.update(batch((130, 150), truncated=True), 3, .099)
        self.assertEqual(result.status, "ambiguous")
        other = BallTracker(768, 432)
        self.assertEqual(other.update(batch((100, 150), truncated=True), 0, 0).status, "ambiguous")

    def test_short_loss_recovers_id_without_solid_gap_bridge(self):
        initial = self.initialize()
        missing = self.tracker.update(batch(), 3, .099)
        self.tracker.update(batch(), 4, .132)
        recovered = self.tracker.update(batch((150, 150)), 5, .165)
        self.assertEqual(missing.status, "predicted")
        self.assertIsNone(missing.observation)
        self.assertEqual(recovered.track_id, initial.track_id)
        self.assertEqual(recovered.observation, (150, 150))
        self.assertTrue(recovered.break_before)

    def test_long_loss_requires_new_confirmation_and_identity(self):
        first = self.initialize()
        self.tracker.update(batch(), 3, .099)
        result = self.tracker.update(batch((300, 150)), 10, .4)
        self.assertEqual(result.status, "tentative")
        self.tracker.update(batch((310, 150)), 11, .433)
        second = self.tracker.update(batch((320, 150)), 12, .466)
        self.assertNotEqual(second.track_id, first.track_id)
        self.assertTrue(second.break_before)

    def test_skipped_frame_indices_break_trail_even_when_time_gate_accepts(self):
        self.initialize()
        result = self.tracker.update(batch((140, 150)), 4, .132)
        self.assertEqual(result.status, "observed")
        self.assertTrue(result.break_before)

    def test_impossible_jump_does_not_replace_last_observation(self):
        self.initialize()
        rejected = self.tracker.update(batch((650, 380)), 3, .099)
        self.assertIsNone(rejected.observation)
        recovered = self.tracker.update(batch((140, 150)), 4, .132)
        self.assertEqual(recovered.observation, (140, 150))

    def test_actual_timestamp_interval_controls_prediction(self):
        self.tracker.update(batch((100, 150)), 0, 0)
        self.tracker.update(batch((110, 150)), 1, .02)
        self.tracker.update(batch((120, 150)), 2, .04)
        result = self.tracker.update(batch(), 3, .14)
        self.assertAlmostEqual(result.prediction[0], 170)
        self.assertIsNone(result.observation)

    def test_input_validation_does_not_mutate_state(self):
        self.initialize()
        for points, index, timestamp in [(batch((130, 150)), 2, .1),
                                         (batch((130, 150)), 3, .066),
                                         (batch((130, 150)), 3, float("nan")),
                                         (batch((9999, 150)), 3, .099)]:
            with self.assertRaises(ValueError):
                self.tracker.update(points, index, timestamp)
        self.assertEqual(self.tracker.update(batch((130, 150)), 3, .099).observation, (130, 150))

    def test_sessions_and_reset_do_not_share_state(self):
        self.initialize()
        other = BallTracker(768, 432)
        self.assertEqual(other.update(batch((130, 150)), 0, 0).status, "tentative")
        self.tracker.reset()
        self.assertEqual(self.tracker.update(batch((300, 150)), 0, 0).status, "tentative")

    def test_missing_initial_evidence_breaks_confirmation(self):
        self.tracker.update(batch((100, 150)), 0, 0)
        self.tracker.update(batch(), 1, .033)
        self.assertEqual(self.tracker.update(batch((120, 150)), 2, .066).status, "tentative")
        self.assertEqual(self.tracker.update(batch((130, 150)), 3, .099).status, "tentative")


class SparseInitializationTests(unittest.TestCase):
    def setUp(self):
        self.tracker = BallTracker(768, 432, temporal_initialization=True)

    def test_missing_frames_are_not_backfilled_as_observations(self):
        updates = [self.tracker.update(batch(*points), i, i / 60)
                   for i, points in enumerate([[(100, 150)], [], [(110, 150)], [], [(120, 150)]])]
        self.assertEqual([u.observation for u in updates], [None, None, None, None, (120, 150)])
        self.assertTrue(updates[-1].break_before)
        self.assertTrue(all(u.prediction is None for u in updates))
        missing = self.tracker.update(batch(), 5, 5 / 60)
        recovered = self.tracker.update(batch((130, 150)), 6, 6 / 60)
        self.assertIsNone(missing.observation)
        self.assertEqual(recovered.track_id, updates[-1].track_id)
        self.assertTrue(recovered.break_before)

    def test_two_coherent_paths_remain_ambiguous(self):
        for i in range(3):
            result = self.tracker.update(batch((100 + 10*i, 150), (500 + 10*i, 300)), i, i / 60)
        self.assertEqual(result.status, 'ambiguous')
        self.assertIsNone(result.observation)

    def test_stationary_path_cannot_confirm_but_does_not_hide_unique_moving_path(self):
        for i in range(3):
            result = self.tracker.update(batch((100 + 10*i, 150), (500, 300)), i, i / 60)
        self.assertEqual(result.observation, (120, 150))
        self.tracker.reset()
        for i in range(10):
            result = self.tracker.update(batch((100, 150)), i, i / 60)
            self.assertIsNone(result.observation)

    def test_expired_seeds_and_impossible_jumps_cannot_confirm(self):
        self.tracker.update(batch((100, 150)), 0, 0)
        self.tracker.update(batch((110, 150)), 4, .067)
        self.assertIsNone(self.tracker.update(batch((120, 150)), 5, .084).observation)
        self.assertEqual(self.tracker.update(batch((130, 150)), 6, .101).observation, (130, 150))
        self.tracker.reset()
        for i, x in enumerate((100, 600, 110)):
            self.assertIsNone(self.tracker.update(batch((x, 150)), i, i / 60).observation)

    def test_saturation_and_path_overflow_discard_all_seeds(self):
        self.tracker.update(batch((100, 150)), 0, 0)
        result = self.tracker.update(batch((110, 150), truncated=True), 1, 1 / 60)
        self.assertEqual(result.status, 'ambiguous')
        self.assertEqual(self.tracker.hypotheses, [])
        # Twelve nearby alternatives produce more than the bounded 64 paths.
        for i in (2, 3):
            result = self.tracker.update(batch(*[(100 + j, 150) for j in range(12)]), i, i / 60)
        self.assertEqual(result.status, 'ambiguous')
        self.assertEqual(self.tracker.hypotheses, [])
        self.assertIsNone(self.tracker.update(batch((120, 150)), 4, 4 / 60).observation)

    def test_reset_and_long_active_loss_require_fresh_evidence(self):
        for i in range(3):
            first = self.tracker.update(batch((100 + i*10, 150)), i, i / 60)
        self.tracker.update(batch((300, 150)), 20, 20 / 60)
        self.tracker.update(batch((310, 150)), 21, 21 / 60)
        second = self.tracker.update(batch((320, 150)), 22, 22 / 60)
        self.assertNotEqual(first.track_id, second.track_id)
        self.tracker.reset()
        self.assertEqual(self.tracker.hypotheses, [])
        self.assertEqual(self.tracker.update(batch((100, 150)), 0, 0).status, 'tentative')
