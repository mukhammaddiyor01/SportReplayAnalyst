import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from evaluation.ball_dataset import digest, export_review
from evaluation.evaluate_box_detector import (box_iou, evaluate, reviewed_examples,
                                             score_box_frame, summarize_frames)


def make_export(root):
    bundle = root/'bundle'
    bundle.mkdir()
    manifest = dict(schema_version=1, recording_id='one', source_sha256='a'*64,
                    source_dimensions=[80, 40], coordinate_space='source_image_xyxy', frames=[])
    labels = []
    for index, visibility in enumerate(('visible', 'not_visible', 'uncertain')):
        image = bundle/f'frame-{index:06d}.png'
        cv2.imwrite(str(image), np.full((40, 80, 3), index*20, np.uint8))
        manifest['frames'].append(dict(frame_index=index, filename=image.name,
            image_sha256=digest(image), timestamp_seconds=index*.04, timestamp_source='presentation'))
        labels.append(dict(frame_index=index, image_sha256=digest(image), visibility=visibility,
                           bbox=[10, 5, 30, 15] if visibility == 'visible' else None))
    (bundle/'manifest.json').write_text(json.dumps(manifest))
    review = {k:v for k,v in manifest.items() if k != 'frames'}
    review['labels'] = labels
    labels_file = root/'review.json'
    labels_file.write_text(json.dumps(review))
    export = root/'export'
    export_review(bundle, labels_file, export)
    return export


class BoxEvaluationTests(unittest.TestCase):
    def test_overlap_and_confidence_ordered_duplicate_matching(self):
        self.assertEqual(box_iou([10, 5, 30, 15], [10, 5, 30, 15]), 1)
        self.assertEqual(box_iou([0, 0, 10, 10], [10, 0, 20, 10]), 0)
        self.assertAlmostEqual(box_iou([0, 0, 10, 10], [0, 0, 5, 10]), .5)
        rows = [[50, 5, 60, 15, .95, 0], [10, 5, 30, 15, .8, 0], [10, 5, 30, 15, .7, 0]]
        score = score_box_frame([10, 5, 30, 15], rows, [80, 40])
        self.assertEqual((score['true_positives'], score['false_positives'], score['false_negatives']), (1, 2, 0))
        self.assertEqual(score['matched_iou'], 1)

    def test_near_center_does_not_replace_iou_and_misses_remain_false_negatives(self):
        score = score_box_frame([10, 5, 30, 15], [[19, 9, 21, 11, .9, 0]], [80, 40])
        self.assertEqual((score['true_positives'], score['false_positives'], score['false_negatives']), (0, 1, 1))
        self.assertIsNone(score['matched_iou'])
        empty = score_box_frame([10, 5, 30, 15], [], [80, 40])
        self.assertEqual(empty['false_negatives'], 1)

    def test_explicit_negative_confidence_boundary_and_ball_class(self):
        rows = [[10, 5, 30, 15, .25, 0], [10, 5, 30, 15, .249, 0], [10, 5, 30, 15, .9, 32]]
        score = score_box_frame(None, rows, [80, 40])
        self.assertEqual(score['false_positives'], 1)
        self.assertEqual(score['false_negatives'], 0)
        self.assertTrue(score['negative_with_predictions'])
        coco = score_box_frame([10, 5, 30, 15], rows, [80, 40], ball_class=32)
        self.assertEqual(coco['true_positives'], 1)

    def test_zero_denominators_are_unknown_not_perfect_results(self):
        empty = summarize_frames([])
        self.assertIsNone(empty['precision'])
        self.assertIsNone(empty['recall'])
        negative = dict(visibility='not_visible', detection_limit_reached=False,
                        **score_box_frame(None, [], [80, 40]))
        score = summarize_frames([negative])
        self.assertEqual(score['negative_frames'], 1)
        self.assertIsNone(score['precision'])
        self.assertIsNone(score['recall'])

    def test_invalid_detector_rows_or_manual_geometry_cannot_be_scored(self):
        for row in ([0, 0, 90, 10, .8, 0], [5, 0, 2, 10, .8, 0],
                    [0, 0, 10, 10, float('nan'), 0], [0, 0, 10, 10, 1.1, 0],
                    [0, 0, 10, 10, .8, .5], [0, 0, 10, 10, True, 0], [0]):
            with self.subTest(row=row), self.assertRaises(ValueError):
                score_box_frame(None, [row], [80, 40])
        for reference in ([0, 0, 81, 40], [1, 1, 1, 2], [0, 0, True, 5]):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                score_box_frame(reference, [], [80, 40])

    def test_duplicate_frames_and_modified_review_export_are_rejected(self):
        with TemporaryDirectory() as directory:
            export = make_export(Path(directory))
            examples = reviewed_examples([export])
            self.assertEqual([e['visibility'] for e in examples], ['visible', 'not_visible'])
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                reviewed_examples([export, export])
            next((export/'labels').glob('*.txt')).write_text('0 .9 .9 .1 .1\n')
            with self.assertRaisesRegex(ValueError, 'differs'):
                reviewed_examples([export])

    def test_local_inference_composition_is_full_frame_and_socket_blocked(self):
        # Synthetic framework stub verifies orchestration, not real model quality.
        with TemporaryDirectory() as directory:
            root = Path(directory)
            export = make_export(root)
            model_path = root/'model.pt'
            model_path.write_bytes(b'synthetic test weights')
            model = Mock()
            model.names = {0:'ball'}
            calls = []
            def predict(pixels, **kwargs):
                import socket
                with self.assertRaisesRegex(OSError, 'Offline box evaluation'):
                    socket.socket.connect(None, None)
                self.assertEqual(pixels.shape, (40, 80, 3))
                self.assertEqual(kwargs['imgsz'], expected_image_size)
                self.assertFalse(kwargs['save'])
                rows = [[10, 5, 30, 15, .9, 0]] if not calls else [[50, 5, 60, 15, .8, 0]]
                calls.append(kwargs)
                data = Mock()
                data.cpu.return_value.tolist.return_value = rows
                return [SimpleNamespace(boxes=SimpleNamespace(data=data))]
            model.predict.side_effect = predict
            factory = Mock(return_value=model)
            modules = {'ultralytics':SimpleNamespace(YOLO=factory),
                       'ultralytics.utils':SimpleNamespace(SETTINGS=Mock()),
                       'torch':SimpleNamespace(set_num_threads=Mock())}
            for expected_image_size in (640,960):
                calls.clear()
                with patch.dict('sys.modules', modules):
                    result = evaluate([export], model_path, digest(model_path), image_size=expected_image_size)
                self.assertEqual(result['settings']['image_size'],expected_image_size)
            self.assertEqual(len(calls), 2)
            self.assertEqual(result['summary']['true_positives'], 1)
            self.assertEqual(result['summary']['false_positives'], 1)
            self.assertEqual(result['summary']['precision'], .5)
            self.assertEqual(result['summary']['recall'], 1)
            self.assertEqual(result['recordings']['one'], result['summary'])
            self.assertNotIn(str(root), json.dumps(result))

    def test_changed_model_is_rejected_before_importing_optional_framework(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            export = make_export(root)
            model = root/'model.pt'
            model.write_bytes(b'synthetic test weights')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                evaluate([export], model, '0'*64)
