import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from backend.adapters.ball_detector import find_appearance_candidates
from evaluation.diagnose_tracking_losses import diagnose, diagnose_frame, MAX_NEARBY_COMPONENTS


class TrackingDiagnosticsTests(unittest.TestCase):
    region = (50, 50, 700, 380)

    def scene(self, ball=False, value=60):
        image = np.full((432, 768, 3), value, np.uint8)
        if ball:
            cv2.circle(image, (200, 150), 5, (245, 245, 245), -1)
        return image

    def test_diagnostics_do_not_change_candidates(self):
        before, current = self.scene(), self.scene(True)
        expected = find_appearance_candidates(before, current, self.region)
        components = []
        actual = find_appearance_candidates(before, current, self.region, on_component=components.append)
        self.assertEqual(actual, expected)
        self.assertIsNone(components[0]['rejection_reason'])
        self.assertGreater(components[0]['moving_pixels'], 0)

    def test_static_shape_reports_motion_failure_not_a_missing_ball(self):
        current = self.scene(True)
        result = diagnose_frame(current, current, self.region, (200, 150), 8)
        self.assertEqual(result['near_reference_candidates'], 0)
        component = result['nearby_components'][0]
        self.assertEqual(component['rejection_reason'], 'motion')
        self.assertEqual(component['moving_pixels'], 0)
        self.assertIsNone(component['background_value'])

    def test_bright_surroundings_report_background_rejection(self):
        before = self.scene(value=170)
        current = before.copy()
        cv2.circle(current, (200, 150), 3, (245, 245, 245), -1)
        result = diagnose_frame(before, current, self.region, (200, 150), 8)
        self.assertEqual(result['nearby_components'][0]['rejection_reason'], 'background')
        self.assertEqual(result['nearby_components'][0]['background_value'], 170)

    def test_small_area_and_sparse_fill_keep_first_failed_stage(self):
        before = self.scene()
        tiny = before.copy()
        cv2.circle(tiny, (200, 150), 2, (245, 245, 245), -1)
        result = diagnose_frame(before, tiny, self.region, (200, 150), 8)
        self.assertEqual(result['nearby_components'][0]['rejection_reason'], 'area')
        sparse = before.copy()
        cv2.line(sparse, (193, 143), (208, 158), (245, 245, 245), 1)
        cv2.line(sparse, (193, 158), (208, 143), (245, 245, 245), 1)
        result = diagnose_frame(before, sparse, self.region, (200, 150), 8)
        self.assertEqual(result['nearby_components'][0]['rejection_reason'], 'fill')

    def test_dense_noise_has_bounded_report_and_explicit_omissions(self):
        before = self.scene()
        current = before.copy()
        for x in range(194, 208, 2):
            for y in range(144, 158, 2):
                current[y, x] = 245
        result = diagnose_frame(before, current, self.region, (200, 150), 8)
        self.assertEqual(len(result['nearby_components']), MAX_NEARBY_COMPONENTS)
        self.assertGreater(result['omitted_nearby_components'], 0)

    def test_source_ending_before_labels_fails_explicitly(self):
        annotations = dict(sequences=[dict(samples=[dict(frame_index=99, visibility='visible', center=[10, 10])])])
        with patch('evaluation.diagnose_tracking_losses.collect_records', return_value={}):
            with self.assertRaisesRegex(ValueError, 'source ended'):
                diagnose(Path('unused.mp4'), annotations)
