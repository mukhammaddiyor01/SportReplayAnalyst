import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import cv2
import numpy as np

from evaluation.ball_dataset import digest, export_review
from evaluation.training_dataset import assemble


class TrainingDatasetTests(unittest.TestCase):
    def export(self,root,name,value,*,group=None,source=None,intended_use=None,reserved_manifest=False):
        bundle=root/(name+'-bundle');bundle.mkdir()
        image=bundle/'frame-000001.png'
        cv2.imwrite(str(image),np.full((40,80,3),value,np.uint8))
        m=dict(schema_version=1,recording_id=group or name,source_sha256=source or (hex(value)[2:]*64)[:64],
               source_dimensions=[80,40],coordinate_space='source_image_xyxy',frames=[dict(frame_index=1,
               filename=image.name,image_sha256=digest(image),timestamp_seconds=.1,timestamp_source='presentation')])
        if reserved_manifest:m['intended_use']='evaluation_only'
        review={k:v for k,v in m.items() if k not in ('frames','intended_use')}
        if intended_use is not None:review['intended_use']=intended_use
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


    def test_training_rechecks_labels_and_refuses_changed_yaml(self):
        from evaluation.train_ball_model import check_dataset
        with TemporaryDirectory() as directory:
            root=Path(directory);a=self.export(root,'one',10);b=self.export(root,'two',20)
            dataset=root/'dataset';assemble([a],[b],dataset)
            self.assertEqual(check_dataset(dataset)['purpose'],'development_smoke_test')
            label=next((dataset/'labels/train').glob('*.txt'));original=label.read_text()
            label.write_text('0 .9 .9 .1 .1\n')
            with self.assertRaisesRegex(ValueError,'label changed'):check_dataset(dataset)
            label.write_text(original)
            (dataset/'data.yaml').write_text('download: forbidden\n')
            with self.assertRaisesRegex(ValueError,'unchanged dataset'):check_dataset(dataset)

    def test_training_rejects_source_path_injection(self):
        from evaluation.train_ball_model import check_dataset
        with TemporaryDirectory() as directory:
            root=Path(directory);a=self.export(root,'one',10);b=self.export(root,'two',20)
            dataset=root/'dataset';assemble([a],[b],dataset)
            report=json.loads((dataset/'dataset.json').read_text())
            report['splits']['train']['examples'][0]['recording_id']='../outside'
            (dataset/'dataset.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'source-frame identity'):check_dataset(dataset)

    def test_evaluation_only_export_is_allowed_for_val_but_not_train(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            development=self.export(root,'development',10)
            evaluation=self.export(root,'evaluation',20,intended_use='evaluation_only')
            with self.assertRaisesRegex(ValueError,'Evaluation-only'):
                assemble([evaluation],[development],root/'rejected')
            self.assertFalse((root/'rejected').exists())
            result=assemble([development],[evaluation],root/'accepted')
            self.assertEqual(result['splits']['val']['examples'][0]['intended_use'],'evaluation_only')

    def test_source_manifest_reservation_survives_review_without_marker(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            reserved=self.export(root,'reserved',10,reserved_manifest=True)
            ordinary=self.export(root,'ordinary',20)
            with self.assertRaisesRegex(ValueError,'Evaluation-only'):
                assemble([reserved],[ordinary],root/'rejected')

    def test_unknown_use_cannot_silently_become_training_data(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'intended use'):
                self.export(Path(directory),'bad',10,intended_use='evaluation-onyl')

    def test_training_rechecks_reserved_role_in_assembled_manifest(self):
        from evaluation.train_ball_model import check_dataset
        with TemporaryDirectory() as directory:
            root=Path(directory);a=self.export(root,'one',10);b=self.export(root,'two',20)
            dataset=root/'dataset';assemble([a],[b],dataset)
            report=json.loads((dataset/'dataset.json').read_text())
            report['splits']['train']['examples'][0]['intended_use']='evaluation_only'
            (dataset/'dataset.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'Evaluation-only'):
                check_dataset(dataset)

    def test_training_profiles_require_explicit_matching_dataset_and_leave_smoke_unchanged(self):
        from evaluation.train_ball_model import training_arguments, TRAINING_ARGS
        self.assertEqual(training_arguments('smoke','development_smoke_test')['epochs'],2)
        with self.assertRaisesRegex(ValueError,'must match'):
            training_arguments('development_v1','development_smoke_test')
        with self.assertRaisesRegex(ValueError,'must match'):
            training_arguments('smoke','development_finetune_v1')
        args=training_arguments('development_v1','development_finetune_v1')
        self.assertEqual(args['freeze'],10)
        args['epochs']=999
        self.assertEqual(training_arguments('development_v1','development_finetune_v1')['epochs'],60)
        self.assertEqual(TRAINING_ARGS['epochs'],2)

    def test_finetune_dataset_preserves_reserved_validation_and_train_separation(self):
        from evaluation.train_ball_model import check_dataset
        with TemporaryDirectory() as directory:
            root=Path(directory)
            a=self.export(root,'train-one',10);b=self.export(root,'val-one',20,reserved_manifest=True)
            dataset=root/'dataset'
            assemble([a],[b],dataset,purpose='development_finetune_v1')
            report=check_dataset(dataset)
            self.assertEqual(report['purpose'],'development_finetune_v1')
            self.assertEqual(report['splits']['val']['examples'][0]['intended_use'],'evaluation_only')
