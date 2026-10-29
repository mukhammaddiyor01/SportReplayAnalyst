import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from evaluation.evaluate_yolo import candidates_from_boxes, verify_model, verify_ball_class


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

    def test_full_source_boxes_keep_coordinates_and_filter_roi_before_candidate_cap(self):
        outside=[[10+i,20,20+i,30,.9,0] for i in range(20)]
        inside=[110,220,130,240,.8,0]
        result=candidates_from_boxes(outside+[inside],(100,200,300,400),ball_class=0,source_dimensions=[640,480])
        self.assertEqual(len(result.candidates),1)
        self.assertEqual((result.candidates[0].x,result.candidates[0].y),(120,230))
        self.assertEqual(result.candidates[0].box,(110,220,20,20))
        self.assertFalse(result.truncated)

    def test_full_source_box_may_cross_roi_edge_but_center_must_be_inside(self):
        rows=[[90,210,130,230,.8,0],[290,210,310,230,.8,0]]
        result=candidates_from_boxes(rows,(100,200,300,400),ball_class=0,source_dimensions=[640,480])
        self.assertEqual(len(result.candidates),1)
        self.assertEqual(result.candidates[0].x,110)
        with self.assertRaisesRegex(ValueError,'outside the source'):
            candidates_from_boxes([], (100,200,700,400),source_dimensions=[640,480])
        with self.assertRaisesRegex(ValueError,'declared input'):
            candidates_from_boxes([[0,0,650,20,.8,0]],(100,200,300,400),ball_class=0,source_dimensions=[640,480])

    def test_numeric_publisher_class_requires_explicit_verified_name(self):
        with self.assertRaisesRegex(ValueError,'matching'):
            verify_ball_class({0:'0',1:'1'},0)
        verify_ball_class({0:'0',1:'1'},0,'0')
        with self.assertRaisesRegex(ValueError,'matching'):
            verify_ball_class({0:'0',1:'1'},1,'0')
        with self.assertRaisesRegex(ValueError,'nonnegative'):
            verify_ball_class({0:'ball'},True)
