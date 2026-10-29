"""Optional local YOLO benchmark; no model download or web/app integration."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from math import ceil, floor, isfinite
from pathlib import Path
from time import perf_counter

from backend.adapters.video_reader import VideoError, read_frames
from backend.config import BALL_MAX_CANDIDATES
from backend.services.ball_observations import BallCandidate, CandidateBatch
from backend.services.ball_tracker import BallTracker
from evaluation.evaluate_ball_candidates import verify_source
from evaluation.evaluate_ball_sequences import score_sequence


def verify_model(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or path.suffix != '.pt':
        raise ValueError('Provide an existing local .pt model; downloads are disabled.')
    if len(expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in expected_sha256):
        raise ValueError('Provide the pinned lowercase model SHA256.')
    with path.open('rb') as source:
        actual = hashlib.file_digest(source, 'sha256').hexdigest()
    if actual != expected_sha256:
        raise ValueError('Model checksum does not match the pinned SHA256.')


def verify_ball_class(names, ball_class, expected_class_name=None):
    if type(ball_class) is not int or ball_class < 0:
        raise ValueError('Use a nonnegative ball class.')
    if expected_class_name is not None and (not isinstance(expected_class_name,str) or
                                           not 1 <= len(expected_class_name) <= 64):
        raise ValueError('Provide an explicit published class name.')
    allowed = ('ball','sports ball') if expected_class_name is None else (expected_class_name,)
    if names.get(ball_class) not in allowed:
        raise ValueError('Select a ball class matching the local model names.')


def candidates_from_boxes(rows, region, *, ball_class: int = 32, source_dimensions=None) -> CandidateBatch:
    """Map crop boxes once, or filter native full-frame boxes by source ROI center."""
    left, top, right, bottom = region
    if source_dimensions is None:
        input_width, input_height = right-left, bottom-top
        offset_x, offset_y = left, top
    else:
        input_width, input_height = source_dimensions
        if not (0 <= left < right <= input_width and 0 <= top < bottom <= input_height):
            raise ValueError('The search rectangle is outside the source.')
        offset_x, offset_y = 0, 0
    candidates = []
    for row in rows:
        if len(row) != 6 or not all(isfinite(v) for v in row):
            raise ValueError('YOLO returned an invalid detection row.')
        x1, y1, x2, y2, confidence, class_id = row
        if not (0 <= confidence <= 1 and class_id == int(class_id)):
            raise ValueError('YOLO returned an invalid confidence or class.')
        if class_id != ball_class:
            continue
        if not (0 <= x1 < x2 <= input_width and 0 <= y1 < y2 <= input_height):
            raise ValueError('YOLO box is outside the declared input image.')
        center_x, center_y = offset_x+(x1+x2)/2, offset_y+(y1+y2)/2
        if not (left <= center_x < right and top <= center_y < bottom):
            continue
        x, y = floor(x1)+offset_x, floor(y1)+offset_y
        width, height = ceil(x2)+offset_x-x, ceil(y2)+offset_y-y
        candidates.append(BallCandidate(center_x, center_y,
                                        width*height, (x, y, width, height)))
    return CandidateBatch(candidates[:BALL_MAX_CANDIDATES], len(candidates) > BALL_MAX_CANDIDATES)


def evaluate(video: Path, annotations: dict, model_path: Path, model_sha256: str, *, ball_class: int = 32, input_mode='roi_crop', image_size=640, expected_class_name=None) -> dict:
    if input_mode not in ('roi_crop','source_frame') or image_size not in (640,960):
        raise ValueError('Use an explicit supported detector input mode and image size.')
    verify_source(video, annotations)
    verify_model(model_path, model_sha256)
    # Optional dependencies are never imported by normal workers or unit tests.
    os.environ['YOLO_OFFLINE'] = 'true'
    from ultralytics import YOLO
    from ultralytics.utils import SETTINGS
    SETTINGS.update({'sync': False})
    import torch
    torch.set_num_threads(1)
    model = YOLO(str(model_path.resolve()), task='detect')
    verify_ball_class(model.names, ball_class, expected_class_name)
    last_index = max(r['frame_index'] for s in annotations['sequences'] for r in s['samples'])
    region = tuple(annotations['search_region'])
    width, height = annotations['source_dimensions']
    left, top, right, bottom = region
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError('The search rectangle is outside the source.')
    tracker = BallTracker(width, height)
    records, durations = {}, []
    reader = read_frames(video)
    try:
        for frame in reader:
            if frame.image.shape[:2] != (height, width):
                raise ValueError('Annotation dimensions do not match the source.')
            started = perf_counter()
            pixels = frame.image if input_mode == 'source_frame' else frame.image[top:bottom, left:right]
            detection_limit = 100 if input_mode == 'source_frame' else 13
            result = model.predict(pixels, imgsz=image_size,
                                   conf=.25, iou=.7, classes=[ball_class], max_det=detection_limit,
                                   device='cpu', verbose=False, save=False)[0]
            durations.append(perf_counter()-started)
            rows = result.boxes.data.cpu().tolist()
            batch = candidates_from_boxes(rows, region, ball_class=ball_class,
                source_dimensions=[width,height] if input_mode == 'source_frame' else None)
            if input_mode == 'source_frame' and len(rows) >= detection_limit:
                # A cap outside the ROI may have hidden an in-ROI ball; withhold association.
                batch = CandidateBatch(batch.candidates, True)
            record = asdict(tracker.update(batch, frame.index, frame.timestamp_seconds))
            record.update(timestamp_source=frame.timestamp_source,
                          candidates=[(c.x, c.y) for c in batch.candidates],
                          candidates_truncated=batch.truncated)
            records[frame.index] = record
            if frame.index >= last_index:
                break
    finally:
        reader.close()
    return dict(model_sha256=model_sha256, detector=f'yolo_{image_size}_conf025',
                ball_class=ball_class, expected_class_name=expected_class_name, input_mode=input_mode, image_size=image_size, source_sha256=annotations['sha256'], source_dimensions=[width, height],
                search_region=list(region),
                initialization='consecutive_v1', processed_frames=len(records),
                mean_predict_seconds=sum(durations)/len(durations) if durations else None,
                first_predict_seconds=durations[0] if durations else None,
                sequences={s['name']: score_sequence(s['samples'], records,
                           annotations['matching_tolerance_px']) for s in annotations['sequences']},
                limitation='Reused center annotations, not bounding-box AP or independent validation. Prediction time includes first-call setup, excludes decoding/loading. No training or runtime promotion.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--model-sha256', required=True)
    parser.add_argument('--ball-class', type=int, default=32, help='32 for COCO;0 for the custom ball model.')
    parser.add_argument('--expected-class-name',help='Explicit model label name after verifying its semantic mapping.')
    parser.add_argument('--input-mode', choices=('roi_crop','source_frame'), default='roi_crop')
    parser.add_argument('--image-size', type=int, choices=(640,960), default=640)
    args = parser.parse_args()
    try:
        print(json.dumps(evaluate(args.video, json.loads(args.annotations.read_text()),
                                  args.model, args.model_sha256, ball_class=args.ball_class, input_mode=args.input_mode, image_size=args.image_size, expected_class_name=args.expected_class_name), indent=2))
    except (ValueError, OSError, VideoError, ImportError) as error:
        parser.exit(1, f'Local YOLO benchmark failed: {error}\n')


if __name__ == '__main__':
    main()
