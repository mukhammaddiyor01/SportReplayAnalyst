"""Assemble verified manual exports into recording-separated YOLO splits."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

import cv2

from evaluation.ball_dataset import (MAX_BUNDLE_BYTES, MAX_IMAGE_BYTES, digest,
                                     new_output, review_intended_use, validate_review, yolo_line)

MAX_EXAMPLES = 2000


def load_export(directory):
    provenance = json.loads((directory/'provenance.json').read_text())
    manifest, review = provenance['manifest'], provenance['review']
    labels = validate_review(manifest, review)
    frames = {f['frame_index']:f for f in manifest['frames']}
    examples = []
    for label in labels:
        if label['visibility'] == 'uncertain':
            continue
        index = label['frame_index']
        stem = f"{manifest['recording_id']}-{index:06d}"
        image = directory/'images'/f'{stem}.png'
        text = directory/'labels'/f'{stem}.txt'
        if (image.is_symlink() or text.is_symlink() or not image.is_file() or
                not text.is_file() or image.stat().st_size > MAX_IMAGE_BYTES or text.stat().st_size > 1024):
            raise ValueError('Missing, linked or oversized exported image/label.')
        if digest(image) != frames[index]['image_sha256']:
            raise ValueError('Exported image checksum does not match its review.')
        expected = yolo_line(label['bbox'], manifest['source_dimensions']) if label['visibility'] == 'visible' else ''
        if text.read_text() != expected:
            raise ValueError('Exported YOLO label differs from the reviewed source box.')
        pixels = cv2.imread(str(image))
        if pixels is None or list(pixels.shape[:2][::-1]) != manifest['source_dimensions']:
            raise ValueError('Exported image dimensions do not match source provenance.')
        examples.append(dict(recording_id=manifest['recording_id'], source_sha256=manifest['source_sha256'],
            frame_index=index, image_sha256=frames[index]['image_sha256'],
            intended_use=review_intended_use(manifest, review),
            pixel_sha256=hashlib.sha256(pixels.tobytes()).hexdigest(),
            timestamp_seconds=frames[index]['timestamp_seconds'], timestamp_source=frames[index]['timestamp_source'],
            visibility=label['visibility'], bbox=label['bbox'], image=image, text=expected))
    if not examples:
        raise ValueError('A reviewed export must contain usable visible/negative examples.')
    return examples


def assemble(train, val, output):
    if not train or not val:
        raise ValueError('Provide reviewed exports for both train and validation.')
    splits = {name:[e for directory in directories for e in load_export(directory)]
              for name, directories in [('train',train),('val',val)]}
    if any(e['intended_use'] == 'evaluation_only' for e in splits['train']):
        raise ValueError('Evaluation-only reviewed exports cannot enter the training split.')
    if sum(map(len, splits.values())) > MAX_EXAMPLES:
        raise ValueError('This local assembly is bounded to 2000 examples.')
    if sum(e['image'].stat().st_size for rows in splits.values() for e in rows) > MAX_BUNDLE_BYTES*4:
        raise ValueError('This local assembly exceeds 512 MiB.')
    # A renamed recording is still rejected if source bytes or decoded pixels repeat.
    for key in ('recording_id','source_sha256','image_sha256','pixel_sha256'):
        if {e[key] for e in splits['train']} & {e[key] for e in splits['val']}:
            raise ValueError(f'Train/validation leakage: overlapping {key}.')
    for name, rows in splits.items():
        identities = [(e['source_sha256'],e['frame_index']) for e in rows]
        if len(identities) != len(set(identities)):
            raise ValueError(f'Duplicate source frames inside {name}; merge each review before assembling.')
        if not any(e['visibility'] == 'visible' for e in rows):
            raise ValueError(f'{name} needs at least one reviewed visible ball.')
    output = new_output(output)
    try:
        report = dict(schema_version=1, purpose='development_smoke_test', classes={'0':'ball'}, splits={},
                      warning='Small single-reviewer development labels. Recording separation does not make reused footage fresh validation. No model quality or production readiness is established.')
        for name, rows in splits.items():
            (output/'images'/name).mkdir(parents=True)
            (output/'labels'/name).mkdir(parents=True)
            entries = []
            for e in rows:
                stem = f"{e['recording_id']}-{e['source_sha256'][:12]}-{e['frame_index']:06d}"
                shutil.copyfile(e['image'],output/'images'/name/f'{stem}.png')
                (output/'labels'/name/f'{stem}.txt').write_text(e['text'])
                entries.append({k:v for k,v in e.items() if k not in ('image','text')})
            report['splits'][name] = dict(counts=dict(Counter(e['visibility'] for e in rows)),
                recording_ids=sorted({e['recording_id'] for e in rows}), examples=entries)
        # Absolute path is generated locally outside Git; YOLO resolves relative roots against settings.
        yaml = f'path: {json.dumps(str(output))}\ntrain: images/train\nval: images/val\nnames:\n  0: ball\n'
        (output/'data.yaml').write_text(yaml)
        (output/'dataset.json').write_text(json.dumps(report,indent=2)+'\n')
        return report
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--train',type=Path,nargs='+',required=True)
    p.add_argument('--val',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    try:
        r = assemble(a.train,a.val,a.output)
        print(json.dumps({name:{'counts':s['counts'],'recording_ids':s['recording_ids']} for name,s in r['splits'].items()},indent=2))
    except (ValueError,OSError,KeyError,TypeError) as error:
        p.exit(1,f'Dataset assembly failed: {error}\n')


if __name__ == '__main__':
    main()
