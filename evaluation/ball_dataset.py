"""Prepare exact local frames and export explicitly reviewed YOLO ball labels."""
import argparse
from collections import Counter
import hashlib
import json
from math import isfinite
from pathlib import Path
import re
import shutil

import cv2

from backend.adapters.video_reader import VideoError, read_frames
from backend.config import MAX_VIDEO_BYTES

MAX_FRAMES = 120
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_BUNDLE_BYTES = 128 * 1024 * 1024
SLUG = re.compile(r'[a-z0-9][a-z0-9-]{0,63}')
DIGEST = re.compile(r'[0-9a-f]{64}')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def new_output(path):
    path = path.resolve()
    repository = Path(__file__).resolve().parents[1]
    if path == repository or repository in path.parents:
        raise ValueError('Keep generated images/datasets outside the repository.')
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return path


def prepare(video, output, recording_id, start, stop, stride=1):
    if not SLUG.fullmatch(recording_id) or not (0 <= start < stop <= 7200 and stride >= 1):
        raise ValueError('Use a recording slug and a bounded nonempty source-frame range.')
    selected = set(range(start, stop, stride))
    if len(selected) > MAX_FRAMES:
        raise ValueError('Prepare at most 120 frames per review bundle.')
    if not 0 < video.stat().st_size <= MAX_VIDEO_BYTES:
        raise ValueError('Use a nonempty source up to 100 MiB.')
    source_sha = digest(video)
    output = new_output(output)
    manifest = dict(schema_version=1, recording_id=recording_id, source_sha256=source_sha,
                    coordinate_space='source_image_xyxy', frames=[])
    reader = read_frames(video)
    total_bytes = 0
    try:
        for frame in reader:
            if frame.index in selected:
                height, width = frame.image.shape[:2]
                manifest['source_dimensions'] = [width, height]
                ok, encoded = cv2.imencode('.png', frame.image)
                if not ok or len(encoded) > MAX_IMAGE_BYTES:
                    raise ValueError('A source frame exceeds the PNG review limit.')
                total_bytes += len(encoded)
                if total_bytes > MAX_BUNDLE_BYTES:
                    raise ValueError('Review bundle exceeds 128 MiB.')
                filename = f'frame-{frame.index:06d}.png'
                image = output / filename
                image.write_bytes(encoded.tobytes())
                image.chmod(0o600)
                manifest['frames'].append(dict(frame_index=frame.index, filename=filename,
                    image_sha256=digest(image), timestamp_seconds=frame.timestamp_seconds,
                    timestamp_source=frame.timestamp_source))
            if frame.index >= stop-1:
                break
        if len(manifest['frames']) != len(selected):
            raise ValueError('The source ended before all requested frames were decoded.')
        (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        (output/'manifest.json').chmod(0o600)
        return manifest
    except BaseException:
        shutil.rmtree(output)
        raise
    finally:
        reader.close()


def validate_review(manifest, review):
    if (manifest.get('schema_version') != 1 or review.get('schema_version') != 1 or
            manifest.get('coordinate_space') != 'source_image_xyxy' or
            review.get('coordinate_space') != 'source_image_xyxy'):
        raise ValueError('Use source-image bounding-box review format version 1.')
    for key in ('recording_id', 'source_sha256', 'source_dimensions'):
        if review.get(key) != manifest.get(key):
            raise ValueError('Labels belong to another source or recording.')
    if not SLUG.fullmatch(manifest['recording_id']) or not DIGEST.fullmatch(manifest['source_sha256']):
        raise ValueError('Invalid recording identifier or source checksum.')
    dimensions = manifest['source_dimensions']
    if len(dimensions) != 2 or any(type(v) is not int or v < 2 for v in dimensions):
        raise ValueError('Invalid source dimensions.')
    width, height = dimensions
    if width > 1920 or height > 1080:
        raise ValueError('Source dimensions exceed review limits.')
    frames = manifest['frames']
    if not 0 < len(frames) <= MAX_FRAMES:
        raise ValueError('Review bundle must contain 1–120 frames.')
    by_index = {}
    previous_time = -1
    for frame in frames:
        index = frame['frame_index']
        timestamp = frame['timestamp_seconds']
        if (type(index) is not int or index < 0 or index in by_index or
                frame['filename'] != f'frame-{index:06d}.png' or
                not DIGEST.fullmatch(frame['image_sha256']) or
                not isfinite(timestamp) or timestamp < 0 or timestamp <= previous_time):
            raise ValueError('Invalid source-frame provenance.')
        if by_index and index <= max(by_index):
            raise ValueError('Source frames must be ordered.')
        if frame['timestamp_source'] not in ('presentation', 'fps_fallback'):
            raise ValueError('Invalid timestamp source.')
        by_index[index] = frame
        previous_time = timestamp
    labels = review['labels']
    if not isinstance(labels, list) or len(labels) > len(frames):
        raise ValueError('Invalid review-label count.')
    seen = set()
    for label in labels:
        index = label['frame_index']
        if type(index) is not int or index not in by_index or index in seen:
            raise ValueError('Labels must identify unique prepared source frames.')
        seen.add(index)
        if label.get('image_sha256') != by_index[index]['image_sha256']:
            raise ValueError('Label image checksum does not match the prepared frame.')
        state, box = label.get('visibility'), label.get('bbox')
        if state == 'visible':
            if (not isinstance(box, list) or len(box) != 4 or
                    any(type(v) not in (int, float) or not isfinite(v) for v in box) or
                    not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
                raise ValueError('Visible balls require a nonempty source bounding box.')
        elif state not in ('not_visible', 'uncertain') or box is not None:
            raise ValueError('Use explicit not-visible/uncertain states without a box.')
    return labels


def yolo_line(box, dimensions):
    x1, y1, x2, y2 = box
    width, height = dimensions
    return '0 '+' '.join(f'{value:.8f}' for value in
        ((x1+x2)/(2*width), (y1+y2)/(2*height), (x2-x1)/width, (y2-y1)/height))+'\n'


def export_review(bundle, labels_file, output):
    manifest = json.loads((bundle/'manifest.json').read_text())
    review = json.loads(labels_file.read_text())
    labels = validate_review(manifest, review)
    chosen = [label for label in labels if label['visibility'] != 'uncertain']
    if not chosen:
        raise ValueError('Review at least one visible or explicitly not-visible frame.')
    by_index = {f['frame_index']: f for f in manifest['frames']}
    total_bytes = 0
    for label in chosen:
        image = bundle/by_index[label['frame_index']]['filename']
        if image.is_symlink() or not image.is_file() or image.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError('Missing, linked or oversized review image.')
        total_bytes += image.stat().st_size
        if total_bytes > MAX_BUNDLE_BYTES or digest(image) != label['image_sha256']:
            raise ValueError('Review image integrity check failed.')
        decoded = cv2.imread(str(image))
        if decoded is None or list(decoded.shape[:2][::-1]) != manifest['source_dimensions']:
            raise ValueError('Review image dimensions differ from the source.')
    output = new_output(output)
    try:
        (output/'images').mkdir(mode=0o700)
        (output/'labels').mkdir(mode=0o700)
        for label in chosen:
            frame = by_index[label['frame_index']]
            stem = f"{manifest['recording_id']}-{label['frame_index']:06d}"
            shutil.copyfile(bundle/frame['filename'], output/'images'/f'{stem}.png')
            text = yolo_line(label['bbox'], manifest['source_dimensions']) if label['visibility'] == 'visible' else ''
            (output/'labels'/f'{stem}.txt').write_text(text)
        counts = dict(Counter(label['visibility'] for label in labels))
        provenance = dict(manifest=manifest, review=review, counts=counts,
                          exported_frames=len(chosen), classes={'0': 'ball'},
                          split='unassigned', warning='Single-reviewer labels. Uncertain/unreviewed frames excluded. Split independent recording groups before training; this is not a ready train/validation dataset.')
        (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
        return provenance
    except BaseException:
        shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('video', type=Path)
    prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--recording-id', required=True)
    prep.add_argument('--start', type=int, required=True)
    prep.add_argument('--stop', type=int, required=True, help='Exclusive decoded frame index.')
    prep.add_argument('--stride', type=int, default=1)
    export = sub.add_parser('export')
    export.add_argument('bundle', type=Path)
    export.add_argument('--labels', type=Path, required=True)
    export.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(args.video, args.output, args.recording_id, args.start, args.stop, args.stride)
            print(f"Prepared {len(result['frames'])} exact decoded frames.")
        else:
            result = export_review(args.bundle, args.labels, args.output)
            print(f"Exported {result['exported_frames']} reviewed frames; split remains unassigned.")
    except (ValueError, OSError, KeyError, TypeError, VideoError) as error:
        parser.exit(1, f'Ball dataset failed: {error}\n')


if __name__ == '__main__':
    main()
