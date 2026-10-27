import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.evaluate_yolo import candidates_from_boxes, verify_model


class YoloEvaluationTests(unittest.TestCase):
    def test_original_crop_boxes_map_once_to_source(self):
        batch = candidates_from_boxes([[10.2, 20.4, 20.6, 25.2, .8, 32]], (161, 326, 563, 517))
        c = batch.candidates[0]
        self.assertAlmostEqual(c.x, 176.4)
        self.assertAlmostEqual(c.y, 348.8)
        self.assertEqual(c.box, (171, 346, 11, 6))
        self.assertFalse(batch.truncated)

    def test_wrong_classes_and_candidate_overflow(self):
        rows = [[10, 20, 20, 25, .8, 0]] + [[10+i, 20, 20+i, 25, .8, 32] for i in range(13)]
        batch = candidates_from_boxes(rows, (0, 0, 100, 100))
        self.assertEqual(len(batch.candidates), 12)
        self.assertTrue(batch.truncated)

    def test_invalid_boxes_cannot_become_observations(self):
        for row in ([0, 0, 110, 10, .8, 32], [20, 0, 10, 10, .8, 32],
                    [0, 0, 10, 10, float('nan'), 32], [0, 0, 10, 10, .8, 32.5], [0]):
            with self.assertRaises(ValueError):
                candidates_from_boxes([row], (0, 0, 100, 100))

    def test_missing_model_and_wrong_hash_are_rejected_without_download(self):
        with TemporaryDirectory() as directory:
            p = Path(directory)/'model.pt'
            with self.assertRaisesRegex(ValueError, 'existing local'):
                verify_model(p, '0'*64)
            p.write_bytes(b'test fixture, not a model')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                verify_model(p, '0'*64)
            verify_model(p, hashlib.sha256(p.read_bytes()).hexdigest())


    def test_custom_ball_class_keeps_source_geometry_and_ignores_coco_class(self):
        result = candidates_from_boxes([[10,20,20,30,.8,0],[50,20,60,30,.9,32]], (100,200,300,400), ball_class=0)
        self.assertEqual(len(result.candidates),1)
        self.assertEqual((result.candidates[0].x,result.candidates[0].y),(115,225))
