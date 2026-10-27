"""Score actual associated observations; predictions never count as detections."""
import argparse
import json
from math import hypot
from pathlib import Path

from backend.adapters.ball_tracking import TrackingRun
from backend.adapters.video_reader import VideoError, read_frames
from evaluation.evaluate_ball_candidates import verify_source


def collect_records(video: Path, annotations: dict, last_index: int, *, include_candidates: bool = False,
                    small_candidate_continuation: bool = False, appearance_filter: bool = True, sparse_motion: bool = False) -> dict:
    """Run all preceding frames as inference context, without consulting labels."""
    verify_source(video, annotations)
    run = TrackingRun(tuple(annotations["search_region"]),
                      small_candidate_continuation=small_candidate_continuation,
                      appearance_filter=appearance_filter, sparse_motion=sparse_motion)
    reader = read_frames(video)
    try:
        for frame in reader:
            if [frame.image.shape[1], frame.image.shape[0]] != annotations["source_dimensions"]:
                raise ValueError("Annotation dimensions do not match the source video.")
            batch = run.consume(frame)
            if include_candidates:
                # Offline diagnostics only; do not add candidates to worker/API results.
                run.frames[-1]['candidates'] = [(c.x, c.y) for c in batch.candidates]
                run.frames[-1]['candidates_truncated'] = batch.truncated
            if frame.index >= last_index:
                break
    finally:
        reader.close()
    return {row["frame_index"]: row for row in run.frames}


def evaluate(video: Path, annotations: dict, split: str, *, legacy_detector: bool = False) -> dict:
    samples = {row["frame_index"]: row for row in annotations["samples"] if row["split"] == split}
    if not samples:
        raise ValueError("This split contains no labeled frames.")
    records = collect_records(video, annotations, max(samples), appearance_filter=not legacy_detector)
    summary = {"split": split, "visible_labels": 0, "observed_near_reference": 0,
               "observed_away_from_reference": 0, "not_observed_on_visible": 0,
               "negative_labels": 0, "observations_on_negatives": 0}
    details = []
    for index, label in sorted(samples.items()):
        if index not in records:
            raise ValueError("The source ended before all labels were processed.")
        record = records[index]
        observed = record["observation"]
        if label["visibility"] == "visible":
            summary["visible_labels"] += 1
            if observed is None:
                summary["not_observed_on_visible"] += 1
            elif hypot(observed[0] - label["center"][0], observed[1] - label["center"][1]) <= annotations["matching_tolerance_px"]:
                summary["observed_near_reference"] += 1
            else:
                summary["observed_away_from_reference"] += 1
        else:
            summary["negative_labels"] += 1
            summary["observations_on_negatives"] += int(observed is not None)
        details.append({"frame_index": index, "manual_center": label["center"],
                        "status": record["status"], "observation": observed,
                        "track_id": record["track_id"]})
    return {"summary": summary, "frames": details,
            "limitation": "Sparse reused pilot, not a dense temporal-identity or generalization benchmark."}


def main():
    parser = argparse.ArgumentParser(description="Evaluate temporal association on the existing pilot.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--annotations", type=Path, default=Path(__file__).with_name("ball-pilot.json"))
    parser.add_argument("--split", choices=["tuning", "held_out"], default="held_out")
    parser.add_argument('--legacy-detector', action='store_true', help='Reproduce the original motion-clipped detector.')
    args = parser.parse_args()
    try:
        result = evaluate(args.video, json.loads(args.annotations.read_text()), args.split, legacy_detector=args.legacy_detector)
    except (ValueError, OSError, VideoError) as error:
        parser.exit(1, f"Tracking evaluation failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
