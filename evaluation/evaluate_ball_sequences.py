"""Dense same-video diagnostics; missing predictions never become ground truth."""
import argparse
import json
from math import hypot
from pathlib import Path

from backend.adapters.video_reader import VideoError
from evaluation.evaluate_ball_tracking import collect_records


def score_sequence(samples: list[dict], records: dict, tolerance: float) -> dict:
    if not samples or any(b['frame_index'] != a['frame_index'] + 1
                          for a, b in zip(samples, samples[1:])):
        raise ValueError('Sequence labels must cover consecutive source frames.')
    counts = dict(visible=0, correct=0, wrong=0, missed=0, uncertain=0,
                  negative=0, observations_on_negatives=0, correct_runs=0,
                  id_changes_between_correct_observations=0)
    detection = dict(evaluated_visible=0, near_reference=0, missing_near_reference=0,
                     near_reference_without_correct_association=0,
                     negative_frames_with_candidates=0, truncated_frames=0)
    details = []
    losses = []
    loss = None
    previous_correct_id = None
    previous_was_correct = False
    for label in samples:
        index = label['frame_index']
        if index not in records:
            raise ValueError('The source ended before all sequence labels were processed.')
        row = records[index]
        visibility = label['visibility']
        observed = row['observation']
        correct = False
        if visibility == 'visible':
            if label['center'] is None:
                raise ValueError('Visible labels require a manual center.')
            counts['visible'] += 1
            if observed is None:
                counts['missed'] += 1
            else:
                correct = hypot(observed[0] - label['center'][0],
                                observed[1] - label['center'][1]) <= tolerance
                counts['correct' if correct else 'wrong'] += 1
        elif visibility == 'uncertain':
            counts['uncertain'] += 1
        elif visibility == 'not_visible_in_search_region':
            counts['negative'] += 1
            counts['observations_on_negatives'] += int(observed is not None)
        else:
            raise ValueError('Unsupported visibility label.')
        candidate_near = None
        if 'candidates' in row and visibility != 'uncertain':
            candidates = row['candidates']
            detection['truncated_frames'] += int(row.get('candidates_truncated', False))
            if visibility == 'visible':
                candidate_near = any(hypot(x - label['center'][0], y - label['center'][1]) <= tolerance
                                     for x, y in candidates)
                detection['evaluated_visible'] += 1
                detection['near_reference' if candidate_near else 'missing_near_reference'] += 1
                detection['near_reference_without_correct_association'] += int(candidate_near and not correct)
            else:
                detection['negative_frames_with_candidates'] += int(bool(candidates))
        details.append(dict(frame_index=index, timestamp_seconds=row['timestamp_seconds'],
                            visibility=visibility, manual_center=label['center'],
                            observation=observed, track_id=row['track_id'],
                            status=row.get('status'), candidate_near_reference=candidate_near,
                            candidate_count=len(row['candidates']) if 'candidates' in row else None))
        if visibility == 'visible' and not correct:
            if loss is None:
                loss = dict(start_frame=index, end_frame=index, frame_count=0,
                            start_seconds=row['timestamp_seconds'], end_seconds=row['timestamp_seconds'])
            loss['end_frame'] = index
            loss['end_seconds'] = row['timestamp_seconds']
            loss['frame_count'] += 1
        elif loss is not None:
            losses.append(loss)
            loss = None
        if correct:
            identity = row['track_id']
            if not previous_was_correct or row['break_before'] or identity != previous_correct_id:
                counts['correct_runs'] += 1
            if previous_correct_id is not None and identity != previous_correct_id:
                counts['id_changes_between_correct_observations'] += 1
            previous_correct_id = identity
        elif visibility != 'visible':
            # Unknown/negative intervals cannot establish identity continuity.
            previous_correct_id = None
        previous_was_correct = correct
    if loss is not None:
        losses.append(loss)
    return {'counts': counts, 'detection': detection, 'frames': details, 'visible_loss_runs': losses,
            'longest_visible_loss_frames': max((r['frame_count'] for r in losses), default=0)}


def evaluate(video: Path, annotations: dict, *, small_candidate_continuation: bool = False) -> dict:
    sequences = annotations['sequences']
    records = collect_records(video, annotations, max(
        row['frame_index'] for seq in sequences for row in seq['samples']), include_candidates=True,
        small_candidate_continuation=small_candidate_continuation)
    return {'small_candidate_continuation': small_candidate_continuation,
            'protocol': annotations['protocol'], 'sequences': {
        seq['name']: score_sequence(seq['samples'], records, annotations['matching_tolerance_px'])
        for seq in sequences},
        'limitation': 'Approximate single-reviewer same-video labels. Loss intervals bound labeled frames, not physical occlusion durations. ID changes are diagnostic, not a standard MOT identity score.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--annotations', type=Path, default=Path(__file__).with_name('ball-sequences.json'))
    parser.add_argument('--small-candidate-continuation', action='store_true',
                        help='Offline experiment: admit smaller candidates only during recent confirmed tracks.')
    args = parser.parse_args()
    try:
        result = evaluate(args.video, json.loads(args.annotations.read_text()),
                          small_candidate_continuation=args.small_candidate_continuation)
    except (ValueError, OSError, VideoError) as error:
        parser.exit(1, f'Sequence evaluation failed: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
