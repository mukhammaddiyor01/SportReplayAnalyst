"""Offline candidate evaluation; reference labels are approximate, not physics."""
import argparse
import hashlib
import json
from math import hypot
from pathlib import Path

from backend.adapters.ball_detector import find_ball_candidates
from backend.adapters.video_reader import VideoError, read_frames
from backend.config import MAX_VIDEO_BYTES


def score_candidates(batch, center, tolerance):
    candidates = batch.candidates
    matches = [] if center is None else [candidate for candidate in candidates
                 if hypot(candidate.x - center[0], candidate.y - center[1]) <= tolerance]
    hit = bool(matches)
    return {"hit": hit, "false_candidates": len(candidates) - int(hit),
            "ambiguous": len(candidates) > 1 or batch.truncated, "truncated": batch.truncated}


def verify_source(video: Path, annotations: dict) -> None:
    if not video.is_file() or not 0 < video.stat().st_size <= MAX_VIDEO_BYTES:
        raise ValueError("Choose a bounded existing video file.")
    digest = hashlib.sha256()
    with video.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != annotations["sha256"]:
        raise ValueError("The video does not match this annotation set.")


def evaluate(video: Path, annotations: dict, split: str) -> dict:
    verify_source(video, annotations)
    samples = {row["frame_index"]: row for row in annotations["samples"] if row["split"] == split}
    if not samples:
        raise ValueError("This split contains no labeled frames.")
    totals = {"split": split, "labeled_visible_frames": 0, "visible_frames_with_near_candidate": 0,
              "labeled_negative_frames": 0, "false_candidates": 0, "ambiguous_frames": 0,
              "truncated_frames": 0, "matching_tolerance_px": annotations["matching_tolerance_px"]}
    details = []
    previous = None
    reader = read_frames(video)
    try:
        for frame in reader:
            if [frame.image.shape[1], frame.image.shape[0]] != annotations["source_dimensions"]:
                raise ValueError("Annotation source dimensions do not match the video.")
            row = samples.get(frame.index)
            if row is not None:
                if previous is None:
                    raise ValueError("A candidate label needs a previous decoded frame.")
                batch = find_ball_candidates(previous, frame.image, tuple(annotations["search_region"]))
                score = score_candidates(batch, row["center"], annotations["matching_tolerance_px"])
                if row["visibility"] == "visible":
                    totals["labeled_visible_frames"] += 1
                    totals["visible_frames_with_near_candidate"] += int(score["hit"])
                else:
                    totals["labeled_negative_frames"] += 1
                totals["false_candidates"] += score["false_candidates"]
                totals["ambiguous_frames"] += int(score["ambiguous"])
                totals["truncated_frames"] += int(score["truncated"])
                details.append({"frame_index": frame.index, "manual_center": row["center"],
                                "candidates": [[round(candidate.x, 1), round(candidate.y, 1)]
                                               for candidate in batch.candidates], **score})
            previous = frame.image
            if frame.index >= max(samples):
                break
    finally:
        reader.close()
    if len(details) != len(samples):
        raise ValueError("The video ended before all labeled frames were decoded.")
    return {"summary": totals, "frames": details,
            "limitation": "Candidate coverage on a tiny pilot; not tracking accuracy or calibrated confidence."}


def main():
    parser = argparse.ArgumentParser(description="Evaluate the frozen bright-ball candidate pilot.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--annotations", type=Path, default=Path(__file__).with_name("ball-pilot.json"))
    parser.add_argument("--split", choices=["tuning", "held_out"], default="held_out")
    args = parser.parse_args()
    try:
        result = evaluate(args.video, json.loads(args.annotations.read_text()), args.split)
    except (ValueError, OSError, VideoError) as error:
        parser.exit(1, f"Evaluation failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
