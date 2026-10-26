import unittest

from backend.services.tracking_review import tracking_gaps


def row(index, status='observed', identity=1, time=None):
    return dict(frame_index=index, timestamp_seconds=index / 30 if time is None else time,
                status=status, track_id=identity,
                observation=[100, 100] if status == 'observed' else None,
                prediction=[110, 100] if status == 'predicted' else None)


class TrackingReviewTests(unittest.TestCase):
    def test_empty_or_fully_observed_clip_has_no_gap(self):
        self.assertEqual(tracking_gaps([]), [])
        self.assertEqual(tracking_gaps([row(0), row(1)]), [])

    def test_clip_boundaries_stay_open(self):
        gaps = tracking_gaps([row(0, 'tentative', None), row(1), row(2, 'predicted')])
        self.assertEqual([gap['position'] for gap in gaps], ['clip_start', 'clip_end'])
        self.assertIsNone(gaps[0]['previous_track_id'])
        self.assertEqual(gaps[0]['resume_seconds'], 1 / 30)
        self.assertIsNone(gaps[1]['next_track_id'])
        self.assertIsNone(gaps[1]['resume_seconds'])

    def test_mixed_missing_states_preserve_source_times_and_ids(self):
        gaps = tracking_gaps([row(90, time=3), row(91, 'predicted', time=3.02),
                              row(92, 'ambiguous', time=3.07), row(93, 'tentative', time=3.12),
                              row(94, identity=2, time=3.18)])
        self.assertEqual(len(gaps), 1)
        gap = gaps[0]
        self.assertEqual((gap['start_frame'], gap['end_frame'], gap['frame_count']), (91, 93, 3))
        self.assertEqual((gap['start_seconds'], gap['end_seconds'], gap['resume_seconds']), (3.02, 3.12, 3.18))
        self.assertEqual((gap['previous_track_id'], gap['next_track_id']), (1, 2))
        self.assertEqual(gap['status_counts'], dict(predicted=1, ambiguous=1, tentative=1))
        self.assertEqual(gap['position'], 'between_observations')

    def test_single_missing_frame_is_reviewable_without_invented_duration(self):
        gap = tracking_gaps([row(0), row(1, 'predicted'), row(2)])[0]
        self.assertEqual(gap['frame_count'], 1)
        self.assertEqual(gap['start_seconds'], gap['end_seconds'])
        self.assertNotIn('duration_seconds', gap)

    def test_entire_unobserved_clip_is_not_a_rally_or_occlusion(self):
        gap = tracking_gaps([row(0, 'searching', None), row(1, 'ambiguous', None)])[0]
        self.assertEqual(gap['position'], 'entire_clip')
        self.assertIsNone(gap['previous_track_id'])
        self.assertIsNone(gap['next_track_id'])
        self.assertEqual(gap['frame_count'], 2)
        self.assertNotIn('rally', gap)

    def test_invalid_sequence_or_observation_state_is_rejected(self):
        inconsistent = row(0, 'predicted')
        inconsistent['observation'] = [100, 100]
        for rows in ([row(0), row(2)], [row(1), row(2, time=0)],
                     [row(0, time=float('nan'))], [inconsistent]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                tracking_gaps(rows)
