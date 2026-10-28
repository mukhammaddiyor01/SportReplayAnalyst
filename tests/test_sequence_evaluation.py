import unittest

from evaluation.evaluate_ball_sequences import score_sequence


def label(index, visibility='visible'):
    return dict(frame_index=index, visibility=visibility,
                center=[10, 10] if visibility == 'visible' else None)


def record(index, observation=None, identity=1, boundary=False):
    return dict(timestamp_seconds=index * .04, observation=observation,
                prediction=[10, 10], track_id=identity, break_before=boundary)


class SequenceEvaluationTests(unittest.TestCase):
    def test_prediction_is_a_miss_and_trailing_loss_is_retained(self):
        result = score_sequence([label(0), label(1)],
                                {0: record(0), 1: record(1)}, 8)
        self.assertEqual(result['counts']['missed'], 2)
        self.assertEqual(result['longest_visible_loss_frames'], 2)
        self.assertEqual(result['visible_loss_runs'][0]['end_seconds'], .04)

    def test_wrong_observation_breaks_correct_run(self):
        rows = {0: record(0, [10, 10]), 1: record(1, [50, 50]),
                2: record(2, [10, 10])}
        result = score_sequence([label(i) for i in range(3)], rows, 8)
        self.assertEqual(result['counts']['wrong'], 1)
        self.assertEqual(result['counts']['correct_runs'], 2)

    def test_reacquired_identity_change_is_counted_across_visible_loss(self):
        rows = {0: record(0, [10, 10]), 1: record(1),
                2: record(2, [10, 10], identity=2)}
        result = score_sequence([label(i) for i in range(3)], rows, 8)
        self.assertEqual(result['counts']['id_changes_between_correct_observations'], 1)

    def test_uncertain_is_neither_negative_nor_identity_evidence(self):
        rows = {0: record(0, [10, 10]), 1: record(1, [50, 50]),
                2: record(2, [10, 10], identity=2)}
        result = score_sequence([label(0), label(1, 'uncertain'), label(2)], rows, 8)
        self.assertEqual(result['counts']['uncertain'], 1)
        self.assertEqual(result['counts']['wrong'], 0)
        self.assertEqual(result['counts']['negative'], 0)
        self.assertEqual(result['counts']['id_changes_between_correct_observations'], 0)

    def test_negative_false_observation_and_explicit_break(self):
        rows = {0: record(0, [10, 10]), 1: record(1, [10, 10], boundary=True),
                2: record(2, [10, 10])}
        result = score_sequence([label(0), label(1),
                                 label(2, 'not_visible_in_search_region')], rows, 8)
        self.assertEqual(result['counts']['correct_runs'], 2)
        self.assertEqual(result['counts']['observations_on_negatives'], 1)

    def test_incomplete_or_invalid_labels_are_rejected(self):
        for labels, rows in [([], {}), ([label(0), label(2)], {}),
                             ([label(0)], {}), ([label(0, 'unknown')], {0: record(0)}),
                             ([dict(frame_index=0, visibility='visible', center=None)], {0: record(0)})]:
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                score_sequence(labels, rows, 8)

    def test_detection_failure_is_separate_from_association_failure(self):
        rows = {0: record(0), 1: record(1)}
        rows[0]['candidates'] = [[10, 10], [70, 70]]
        rows[1]['candidates'] = [[70, 70]]
        result = score_sequence([label(0), label(1)], rows, 8)
        self.assertEqual(result['detection']['near_reference'], 1)
        self.assertEqual(result['detection']['missing_near_reference'], 1)
        self.assertEqual(result['detection']['near_reference_without_correct_association'], 1)
        self.assertIs(result['frames'][0]['candidate_near_reference'], True)
        self.assertIs(result['frames'][1]['candidate_near_reference'], False)

    def test_negative_candidates_do_not_imply_confirmed_false_track(self):
        rows = {0: record(0), 1: record(1)}
        for row in rows.values():
            row.update(candidates=[[50, 50]], candidates_truncated=True)
        result = score_sequence([label(0, 'not_visible_in_search_region'),
                                 label(1, 'uncertain')], rows, 8)
        self.assertEqual(result['detection']['negative_frames_with_candidates'], 1)
        self.assertEqual(result['detection']['truncated_frames'], 1)
        self.assertEqual(result['counts']['observations_on_negatives'], 0)

    def test_loss_span_and_reacquisition_use_irregular_source_time(self):
        rows = {0: record(0, [10, 10]), 1: record(1), 2: record(2),
                3: record(3, [10, 10], identity=2, boundary=True)}
        for row, timestamp in zip(rows.values(), [0.1, 0.13, 0.21, 0.28]):
            row['timestamp_seconds'] = timestamp
        result = score_sequence([label(i) for i in range(4)], rows, 8)
        self.assertAlmostEqual(result['longest_visible_loss_sample_span_seconds'], .08)
        recovered = result['visible_reacquisitions'][0]
        self.assertEqual((recovered['first_loss_frame'], recovered['last_loss_frame']), (1, 2))
        self.assertEqual(recovered['reacquired_frame'], 3)
        self.assertAlmostEqual(recovered['elapsed_since_last_correct_seconds'], .18)
        self.assertFalse(recovered['same_track_id'])
        self.assertTrue(recovered['break_before'])

    def test_single_loss_sample_has_zero_span_not_invented_frame_duration(self):
        rows = {0: record(0, [10, 10]), 1: record(1), 2: record(2, [10, 10])}
        result = score_sequence([label(i) for i in range(3)], rows, 8)
        self.assertEqual(result['visible_loss_runs'][0]['sample_span_seconds'], 0)
        self.assertAlmostEqual(result['visible_reacquisitions'][0]['elapsed_since_last_correct_seconds'], .08)
        self.assertTrue(result['visible_reacquisitions'][0]['same_track_id'])

    def test_uncertain_negative_or_leading_loss_cannot_establish_reacquisition(self):
        for state in ['uncertain', 'not_visible_in_search_region']:
            rows = {0: record(0, [10, 10]), 1: record(1), 2: record(2),
                    3: record(3), 4: record(4, [10, 10])}
            labels = [label(0), label(1), label(2, state), label(3), label(4)]
            result = score_sequence(labels, rows, 8)
            self.assertEqual(result['visible_reacquisitions'], [])
        result = score_sequence([label(0), label(1)],
                                {0: record(0), 1: record(1, [10, 10])}, 8)
        self.assertEqual(result['visible_reacquisitions'], [])

    def test_invalid_timestamps_cannot_produce_timing_metrics(self):
        for timestamp in [0, -.1, float('nan'), float('inf'), '0.1', True]:
            rows = {0: record(0), 1: record(1)}
            rows[1]['timestamp_seconds'] = timestamp
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                score_sequence([label(0), label(1)], rows, 8)
