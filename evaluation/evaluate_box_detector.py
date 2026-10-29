"""Offline full-frame box evaluation at one fixed operating point, not AP."""
import argparse
import json
from math import isfinite
import os
from pathlib import Path
from unittest.mock import patch

import cv2

from evaluation.ball_dataset import MAX_BUNDLE_BYTES, digest
from evaluation.evaluate_yolo import verify_model, verify_ball_class
from evaluation.training_dataset import MAX_EXAMPLES, load_export

CONFIDENCE = .25
MATCH_IOU = .5
NMS_IOU = .7
MAX_DETECTIONS = 100


def validate_box(box, dimensions):
    width, height = dimensions
    if (not isinstance(box, (list, tuple)) or len(box) != 4 or
            any(type(v) not in (int, float) or not isfinite(v) for v in box) or
            not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
        raise ValueError('Use finite nonempty source-image boxes inside the frame.')


def box_iou(first, second):
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0, right-left) * max(0, bottom-top)
    first_area = (first[2]-first[0]) * (first[3]-first[1])
    second_area = (second[2]-second[0]) * (second[3]-second[1])
    return intersection / (first_area + second_area - intersection)


def score_box_frame(reference, predictions, dimensions, *, ball_class=0):
    """One manually reviewed ball or explicit full-frame negative; no uncertainty."""
    if (len(dimensions) != 2 or any(type(v) is not int or v < 2 for v in dimensions) or
            type(ball_class) is not int or ball_class < 0):
        raise ValueError('Use source dimensions and a nonnegative ball class.')
    if reference is not None:
        validate_box(reference, dimensions)
    selected = []
    for row in predictions:
        if (len(row) != 6 or any(type(v) not in (int, float) or not isfinite(v) for v in row) or
                not 0 <= row[4] <= 1 or row[5] < 0 or row[5] != int(row[5])):
            raise ValueError('Invalid detector box/confidence/class row.')
        validate_box(row[:4], dimensions)
        if row[5] == ball_class and row[4] >= CONFIDENCE:
            selected.append(row)
    # At most one ground-truth ball. Confidence-ordered duplicates remain false positives.
    matched_iou = None
    for row in sorted(selected, key=lambda item: item[4], reverse=True):
        if reference is not None and matched_iou is None:
            overlap = box_iou(reference, row[:4])
            if overlap >= MATCH_IOU:
                matched_iou = overlap
    tp = int(matched_iou is not None)
    return dict(true_positives=tp, false_positives=len(selected)-tp,
                false_negatives=int(reference is not None)-tp,
                selected_predictions=len(selected), matched_iou=matched_iou,
                negative_with_predictions=reference is None and bool(selected))


def summarize_frames(frames):
    totals = {key: sum(f[key] for f in frames) for key in
              ('true_positives', 'false_positives', 'false_negatives', 'selected_predictions')}
    positives = sum(f['visibility'] == 'visible' for f in frames)
    negatives = sum(f['visibility'] == 'not_visible' for f in frames)
    tp, fp, fn = (totals[key] for key in ('true_positives', 'false_positives', 'false_negatives'))
    totals.update(visible_frames=positives, negative_frames=negatives,
                  negative_frames_with_predictions=sum(f['negative_with_predictions'] for f in frames),
                  detection_limit_frames=sum(f['detection_limit_reached'] for f in frames),
                  precision=tp/(tp+fp) if tp+fp else None,
                  recall=tp/(tp+fn) if tp+fn else None)
    return totals


def reviewed_examples(exports):
    if not 1 <= len(exports) <= 32:
        raise ValueError('Provide 1–32 reviewed exports.')
    examples = [example for directory in exports for example in load_export(directory)]
    identities = [(e['source_sha256'], e['frame_index']) for e in examples]
    if len(set(identities)) != len(identities):
        raise ValueError('Duplicate source frames cannot be scored twice.')
    if (len(examples) > MAX_EXAMPLES or
            sum(e['image'].stat().st_size for e in examples) > MAX_BUNDLE_BYTES*4):
        raise ValueError('Box evaluation is bounded to 2000 images and 512 MiB.')
    return examples


def evaluate(exports, model_path, model_sha256, *, ball_class=0, image_size=640, expected_class_name=None):
    if image_size not in (640,960):
        raise ValueError('Use a supported explicit inference image size.')
    examples = reviewed_examples(exports)
    verify_model(model_path, model_sha256)
    if type(ball_class) is not int or ball_class < 0:
        raise ValueError('Use a nonnegative ball class.')
    os.environ['YOLO_OFFLINE'] = 'true'
    # Optional framework imports and inference are isolated from app workers.
    with patch('socket.socket.connect', side_effect=OSError('Offline box evaluation')):
        from ultralytics import YOLO
        from ultralytics.utils import SETTINGS
        SETTINGS.update({'sync': False})
        import torch
        torch.set_num_threads(1)
        model = YOLO(str(model_path.resolve()), task='detect')
        verify_ball_class(model.names, ball_class, expected_class_name)
        frames = []
        for example in examples:
            # Recheck bytes immediately before inference, after initial export validation.
            if digest(example['image']) != example['image_sha256']:
                raise ValueError('Reviewed image changed before inference.')
            pixels = cv2.imread(str(example['image']))
            if pixels is None:
                raise ValueError('Reviewed image cannot be decoded.')
            dimensions = list(pixels.shape[:2][::-1])
            result = model.predict(pixels, imgsz=image_size, conf=CONFIDENCE, iou=NMS_IOU,
                                   classes=[ball_class], max_det=MAX_DETECTIONS,
                                   device='cpu', verbose=False, save=False)[0]
            predictions = result.boxes.data.cpu().tolist()
            score = score_box_frame(example['bbox'], predictions, dimensions, ball_class=ball_class)
            frames.append(dict(recording_id=example['recording_id'],
                               source_sha256=example['source_sha256'], frame_index=example['frame_index'],
                               image_sha256=example['image_sha256'], intended_use=example['intended_use'],
                               source_dimensions=dimensions,
                               timestamp_seconds=example['timestamp_seconds'],
                               timestamp_source=example['timestamp_source'], visibility=example['visibility'],
                               detection_limit_reached=len(predictions) >= MAX_DETECTIONS, **score))
    return dict(schema_version=1, purpose='development_box_evaluation', model_sha256=model_sha256,
                settings=dict(ball_class=ball_class, expected_class_name=expected_class_name, image_size=image_size, confidence=CONFIDENCE,
                              matching_iou=MATCH_IOU, nms_iou=NMS_IOU, max_detections=MAX_DETECTIONS,
                              coordinate_space='full_source_image_xyxy'),
                reviewed_export_sha256=[digest(directory/'provenance.json') for directory in exports],
                summary=summarize_frames(frames),
                recordings={group: summarize_frames([f for f in frames if f['recording_id'] == group])
                            for group in sorted({f['recording_id'] for f in frames})}, frames=frames,
                limitation=('One fixed confidence/IoU operating point; not AP, temporal tracking or independent '
                            'validation. Uncertain/unreviewed frames excluded; explicit negatives cover the '
                            'whole prepared image. A reached detection cap can undercount false positives. '
                            'No model promotion. Original source transform/label limits remain applicable.'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exports', type=Path, nargs='+', required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--model-sha256', required=True)
    parser.add_argument('--ball-class', type=int, default=0)
    parser.add_argument('--expected-class-name',help='Explicit model label name after verifying its semantic mapping.')
    parser.add_argument('--image-size',type=int,choices=(640,960),default=640)
    args = parser.parse_args()
    try:
        print(json.dumps(evaluate(args.exports, args.model, args.model_sha256,
                                  ball_class=args.ball_class,image_size=args.image_size,expected_class_name=args.expected_class_name), indent=2))
    except (ValueError, OSError, KeyError, TypeError, ImportError) as error:
        parser.exit(1, f'Box evaluation failed: {error}\n')


if __name__ == '__main__':
    main()
