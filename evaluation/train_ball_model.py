"""Explicit local development training; no startup downloads or app promotion."""
import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch

import cv2

from evaluation.ball_dataset import DIGEST, SLUG, digest, new_output, yolo_line
from evaluation.evaluate_yolo import verify_model

# A small pipeline smoke test, not an accuracy-tuned training recipe.
TRAINING_ARGS = dict(epochs=2, imgsz=640, batch=4, device='cpu', workers=0,
    cache=False, plots=False, amp=False, seed=0, deterministic=True, patience=0,
    optimizer='SGD', lr0=.001, lrf=.01, momentum=.9, weight_decay=.0005,
    warmup_epochs=0, mosaic=0, mixup=0, copy_paste=0, fliplr=0, flipud=0,
    degrees=0, translate=0, scale=0, hsv_h=0, hsv_s=0, hsv_v=0, close_mosaic=0)


def check_dataset(dataset):
    dataset = dataset.resolve()
    report = json.loads((dataset/'dataset.json').read_text())
    expected = f'path: {json.dumps(str(dataset))}\ntrain: images/train\nval: images/val\nnames:\n  0: ball\n'
    if (dataset/'data.yaml').read_text() != expected or report.get('purpose') != 'development_smoke_test':
        raise ValueError('Use an unchanged dataset produced by evaluation.training_dataset.')
    splits = report['splits']
    for key in ('recording_id','source_sha256','image_sha256','pixel_sha256'):
        if {e[key] for e in splits['train']['examples']} & {e[key] for e in splits['val']['examples']}:
            raise ValueError('Train/validation recording, source or image overlap.')
    for name in ('train','val'):
        rows = splits[name]['examples']
        for example in rows:
            intended_use = example.get('intended_use', 'development')
            if intended_use not in ('development', 'evaluation_only'):
                raise ValueError('Invalid declared intended use in assembled dataset.')
            if name == 'train' and intended_use == 'evaluation_only':
                raise ValueError('Evaluation-only examples cannot enter model training.')
        if not rows or not any(e['visibility']=='visible' for e in rows):
            raise ValueError('Both splits need reviewed visible balls.')
        actual = sorted((dataset/'images'/name).glob('*.png'))
        if len(actual) != len(rows):
            raise ValueError('Dataset image count changed after assembly.')
        for e in rows:
            if (not SLUG.fullmatch(e['recording_id']) or not DIGEST.fullmatch(e['source_sha256']) or
                    type(e['frame_index']) is not int or not 0 <= e['frame_index'] < 7200 or
                    e['visibility'] not in ('visible','not_visible')):
                raise ValueError('Invalid source-frame identity in assembled dataset.')
            stem = f"{e['recording_id']}-{e['source_sha256'][:12]}-{e['frame_index']:06d}"
            image, label = dataset/'images'/name/f'{stem}.png', dataset/'labels'/name/f'{stem}.txt'
            if image.is_symlink() or label.is_symlink() or digest(image) != e['image_sha256']:
                raise ValueError('Dataset image integrity check failed before training.')
            # Recompute YOLO labels from reviewed source boxes and actual source dimensions.
            pixels = cv2.imread(str(image))
            if pixels is None:
                raise ValueError('Dataset image cannot be decoded.')
            text = yolo_line(e['bbox'], list(pixels.shape[:2][::-1])) if e['visibility']=='visible' else ''
            if label.read_text() != text:
                raise ValueError('Dataset label changed after assembly.')
    return report


def train(dataset, model_path, expected_sha256, output):
    report = check_dataset(dataset)
    verify_model(model_path, expected_sha256)
    os.environ['YOLO_OFFLINE'] = 'true'
    # No data or telemetry can leave this isolated CLI process.
    with patch('socket.socket.connect', side_effect=OSError('Offline local training')):
        from ultralytics import YOLO
        from ultralytics.utils import SETTINGS
        SETTINGS.update({'sync':False})
        model = YOLO(str(model_path.resolve()),task='detect')
        output = new_output(output)
        receipt = dict(status='running', base_model_sha256=expected_sha256,
            dataset_sha256=digest(dataset/'dataset.json'), args=TRAINING_ARGS,
            split_counts={name:split['counts'] for name,split in report['splits'].items()},
            limitation='Development smoke run on tiny reused single-reviewer labels; not independent validation or app-ready tracking.')
        (output/'run.json').write_text(json.dumps(receipt,indent=2)+'\n')
        try:
            # Output was exclusively created above; exist_ok only uses that owned directory.
            model.train(data=str((dataset/'data.yaml').resolve()), project=str(output.parent),
                        name=output.name, exist_ok=True, verbose=False, **TRAINING_ARGS)
            receipt['status'] = 'completed'
            receipt['weights'] = {p.name:digest(p) for p in (output/'weights').glob('*.pt')}
            if 'best.pt' not in receipt['weights']:
                raise ValueError('Training did not produce best.pt.')
        except BaseException:
            receipt['status'] = 'failed'
            raise
        finally:
            (output/'run.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('dataset',type=Path)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--model-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    try:
        print(json.dumps(train(a.dataset,a.model,a.model_sha256,a.output),indent=2))
    except (ValueError,OSError,KeyError,TypeError,ImportError) as error:
        p.exit(1,f'Local training failed: {error}\n')


if __name__ == '__main__':
    main()
