import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import numpy as np

from evaluation.ball_dataset import digest, export_review
from evaluation.training_dataset import assemble


class TrainingDatasetTests(unittest.TestCase):
    def export(self,root,name,value,*,group=None,source=None):
        bundle=root/(name+'-bundle');bundle.mkdir()
        image=bundle/'frame-000001.png'
        cv2.imwrite(str(image),np.full((40,80,3),value,np.uint8))
        m=dict(schema_version=1,recording_id=group or name,source_sha256=source or (hex(value)[2:]*64)[:64],
               source_dimensions=[80,40],coordinate_space='source_image_xyxy',frames=[dict(frame_index=1,
               filename=image.name,image_sha256=digest(image),timestamp_seconds=.1,timestamp_source='presentation')])
        review={k:v for k,v in m.items() if k!='frames'}
        review['labels']=[dict(frame_index=1,image_sha256=digest(image),visibility='visible',bbox=[10,5,30,15])]
        (bundle/'manifest.json').write_text(json.dumps(m));label=root/(name+'.json');label.write_text(json.dumps(review))
        output=root/(name+'-export');export_review(bundle,label,output)
        return output

    def test_independent_recording_exports_make_complete_local_splits(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);a=self.export(root,'one',10);b=self.export(root,'two',20)
            result=assemble([a],[b],root/'dataset')
            self.assertEqual(result['splits']['train']['counts'],{'visible':1})
            self.assertEqual(result['splits']['val']['recording_ids'],['two'])
            self.assertEqual(len(list((root/'dataset/images/train').glob('*.png'))),1)
            self.assertIn('0: ball',(root/'dataset/data.yaml').read_text())
            self.assertNotIn(str(root), (root/'dataset/dataset.json').read_text())
            with self.assertRaises(FileExistsError):assemble([a],[b],root/'dataset')

    def test_related_recordings_sources_and_duplicate_pixels_are_rejected(self):
        for kind in ('group','source','pixels'):
            with self.subTest(kind=kind),TemporaryDirectory() as directory:
                root=Path(directory);a=self.export(root,'one',10,source='a'*64)
                b=self.export(root,'two',10 if kind=='pixels' else 20,
                              group='one' if kind=='group' else 'two',source='a'*64 if kind=='source' else 'b'*64)
                with self.assertRaisesRegex(ValueError,'leakage'):assemble([a],[b],root/'dataset')
                self.assertFalse((root/'dataset').exists())

    def test_changed_labels_and_duplicate_examples_fail_before_output(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);a=self.export(root,'one',10);b=self.export(root,'two',20)
            with self.assertRaisesRegex(ValueError,'Duplicate'):assemble([a,a],[b],root/'dataset')
            next((a/'labels').glob('*.txt')).write_text('0 .9 .9 .1 .1\n')
            with self.assertRaisesRegex(ValueError,'differs'):assemble([a],[b],root/'dataset')
            self.assertFalse((root/'dataset').exists())


    def test_reencoded_identical_pixels_cannot_cross_splits(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);a=self.export(root,'one',10,source='a'*64);b=self.export(root,'two',10,source='b'*64)
            image=next((b/'images').glob('*.png'))
            cv2.imwrite(str(image),cv2.imread(str(image)),[cv2.IMWRITE_PNG_COMPRESSION,9])
            provenance=json.loads((b/'provenance.json').read_text())
            provenance['manifest']['frames'][0]['image_sha256']=digest(image)
            provenance['review']['labels'][0]['image_sha256']=digest(image)
            (b/'provenance.json').write_text(json.dumps(provenance))
            with self.assertRaisesRegex(ValueError,'pixel_sha256'):
                assemble([a],[b],root/'dataset')
