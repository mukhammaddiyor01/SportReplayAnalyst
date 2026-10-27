"""Inspect detector rejection stages around manual references; never retune rules."""
import argparse
import json
from math import hypot
from pathlib import Path

from backend.adapters.ball_detector import find_appearance_candidates
from backend.adapters.video_reader import VideoError, read_frames
from evaluation.evaluate_ball_tracking import collect_records

MAX_NEARBY_COMPONENTS = 16


def diagnose_frame(previous, current, region, center, tolerance):
    nearby = []
    omitted = 0

    def inspect(component):
        nonlocal omitted
        x, y, width, height = component['box']
        distance = hypot(max(x - center[0], 0, center[0] - (x + width - 1)),
                         max(y - center[1], 0, center[1] - (y + height - 1)))
        if distance > tolerance:
            return
        if len(nearby) < MAX_NEARBY_COMPONENTS:
            nearby.append(component)
        else:
            omitted += 1

    batch = find_appearance_candidates(previous, current, region, on_component=inspect)
    near_candidates = sum(hypot(c.x - center[0], c.y - center[1]) <= tolerance
                          for c in batch.candidates)
    return dict(near_reference_candidates=near_candidates, candidate_batch_truncated=batch.truncated,
                nearby_components=nearby, omitted_nearby_components=omitted)


def diagnose(video: Path, annotations: dict):
    labels = {row['frame_index']: row for seq in annotations['sequences']
              for row in seq['samples'] if row['visibility'] == 'visible'}
    if not labels:
        raise ValueError('Diagnostics need at least one visible manual reference.')
    records = collect_records(video, annotations, max(labels))
    if any(index not in records for index in labels):
        raise ValueError('The source ended before all diagnostic labels were processed.')
    tolerance = annotations['matching_tolerance_px']
    failures = {i: label for i, label in labels.items() if records[i]['observation'] is None or
                hypot(records[i]['observation'][0] - label['center'][0],
                      records[i]['observation'][1] - label['center'][1]) > tolerance}
    details = []
    previous = None
    reader = read_frames(video)
    try:
        for frame in reader:
            if frame.index in failures:
                label = failures[frame.index]
                if previous is None:
                    detail = dict(near_reference_candidates=0, nearby_components=[],
                                  candidate_batch_truncated=False, omitted_nearby_components=0,
                                  note='First frame has no previous image for motion evidence.')
                else:
                    detail = diagnose_frame(previous, frame.image, tuple(annotations['search_region']),
                                            label['center'], tolerance)
                details.append(dict(frame_index=frame.index, timestamp_seconds=frame.timestamp_seconds,
                                    manual_center=label['center'], status=records[frame.index]['status'],
                                    observation=records[frame.index]['observation'], **detail))
            previous = frame.image
            if frame.index >= max(labels):
                break
    finally:
        reader.close()
    return dict(visible_labels=len(labels), failed_associations=len(failures), frames=details,
                limitation='Spatially nearby component boxes are diagnostic context, not confirmed ball identity. Only the first failed filter is reported; later metrics are null. A null rejection means component filters passed, not guaranteed retention after candidate truncation. No component can also mean brightness, saturation or contrast masking failed. No threshold was tuned.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--annotations', type=Path, default=Path(__file__).with_name('ball-sequences.json'))
    args = parser.parse_args()
    try:
        result = diagnose(args.video, json.loads(args.annotations.read_text()))
    except (ValueError, OSError, VideoError) as error:
        parser.exit(1, f'Tracking diagnostics failed: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
