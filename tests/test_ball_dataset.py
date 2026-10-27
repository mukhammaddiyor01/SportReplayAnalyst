import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import numpy as np

from evaluation.ball_dataset import digest, export_review, prepare, validate_review, yolo_line


class BallDatasetTests(unittest.TestCase):
    def fixture(self, directory):
        bundle = Path(directory)/'bundle'
        bundle.mkdir()
        image = bundle/'frame-000020.png'
        cv2.imwrite(str(image), np.zeros((40, 80, 3), np.uint8))
        manifest = dict(schema_version=1, recording_id='source-a', source_sha256='a'*64,
                        source_dimensions=[80, 40], coordinate_space='source_image_xyxy',
                        frames=[dict(frame_index=20, filename=image.name, image_sha256=digest(image),
                                     timestamp_seconds=.333, timestamp_source='presentation')])
        review = {k:v for k,v in manifest.items() if k != 'frames'}
        review['labels'] = [dict(frame_index=20, image_sha256=digest(image), visibility='visible', bbox=[10, 5, 30, 15])]
        (bundle/'manifest.json').write_text(json.dumps(manifest))
        labels = Path(directory)/'review.json'
        labels.write_text(json.dumps(review))
        return bundle, labels, manifest, review

    def test_yolo_normalization_preserves_source_box(self):
        self.assertEqual(yolo_line([10, 5, 30, 15], [80, 40]), '0 0.25000000 0.25000000 0.25000000 0.25000000\n')

    def test_export_only_reviewed_and_explicit_negative_frames(self):
        with TemporaryDirectory() as directory:
            bundle, labels, manifest, review = self.fixture(directory)
            out = Path(directory)/'export'
            result = export_review(bundle, labels, out)
            self.assertEqual(result['split'], 'unassigned')
            self.assertEqual((out/'labels/source-a-000020.txt').read_text(), yolo_line([10, 5, 30, 15], [80, 40]))
            self.assertFalse((out/'data.yaml').exists())
            review['labels'][0].update(visibility='not_visible', bbox=None)
            labels.write_text(json.dumps(review))
            export_review(bundle, labels, Path(directory)/'negative')
            self.assertEqual((Path(directory)/'negative/labels/source-a-000020.txt').read_text(), '')
            review['labels'][0].update(visibility='uncertain')
            labels.write_text(json.dumps(review))
            with self.assertRaisesRegex(ValueError, 'at least one'):
                export_review(bundle, labels, Path(directory)/'uncertain')

    def test_point_labels_invalid_boxes_duplicate_and_foreign_sources_are_rejected(self):
        with TemporaryDirectory() as directory:
            _, _, manifest, review = self.fixture(directory)
            for box in (None, [10, 5], [30, 5, 10, 15], [0, 0, 81, 40], [True, 0, 5, 5], [0, 0, float('nan'), 5]):
                bad = copy.deepcopy(review);bad['labels'][0]['bbox'] = box
                with self.assertRaises(ValueError):validate_review(manifest, bad)
            bad = copy.deepcopy(review);bad['labels'] *= 2
            with self.assertRaises(ValueError):validate_review(manifest, bad)
            bad = copy.deepcopy(review);bad['source_sha256'] = 'b'*64
            with self.assertRaisesRegex(ValueError, 'another source'):validate_review(manifest, bad)

    def test_modified_images_and_path_traversal_fail_before_output(self):
        with TemporaryDirectory() as directory:
            bundle, labels, manifest, review = self.fixture(directory)
            (bundle/'frame-000020.png').write_bytes(b'modified')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                export_review(bundle, labels, Path(directory)/'export')
            self.assertFalse((Path(directory)/'export').exists())
            manifest['frames'][0]['filename'] = '../escape.png'
            with self.assertRaisesRegex(ValueError, 'provenance'):validate_review(manifest, review)

    def test_preparation_keeps_decoded_indices_times_and_cleans_short_source(self):
        with TemporaryDirectory() as directory:
            video = Path(directory)/'source.avi'
            writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 30, (80, 40))
            for i in range(6):writer.write(np.full((40, 80, 3), i*20, np.uint8))
            writer.release()
            m = prepare(video, Path(directory)/'prepared', 'recording-one', 1, 6, 2)
            self.assertEqual([f['frame_index'] for f in m['frames']], [1, 3, 5])
            self.assertAlmostEqual(m['frames'][0]['timestamp_seconds'], 1/30)
            self.assertEqual(m['source_sha256'], digest(video))
            review = {k:v for k,v in m.items() if k!='frames'};review['labels']=[]
            validate_review(m,review)
            with self.assertRaisesRegex(ValueError, 'source ended'):
                prepare(video, Path(directory)/'short', 'recording-one', 1, 10)
            self.assertFalse((Path(directory)/'short').exists())
            with self.assertRaises(FileExistsError):prepare(video, Path(directory)/'prepared', 'recording-one', 1, 3)
