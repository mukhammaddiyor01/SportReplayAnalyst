"""Conservative evidence rules for sampled frame calibration drift."""
from dataclasses import dataclass
from math import hypot, isfinite

from backend.config import (CAMERA_DRIFT_DIAGONAL_FRACTION, CAMERA_MIN_COMPARISONS,
                            CAMERA_MIN_COVERAGE, CAMERA_MIN_INLIER_FRACTION,
                            CAMERA_MIN_INLIERS, CAMERA_MIN_SPAN,
                            CAMERA_SAMPLE_INTERVAL_SECONDS)


@dataclass(frozen=True)
class MotionEvidence:
    frame_index: int
    timestamp_seconds: float
    matched_points: int
    inlier_points: int
    coverage_fraction: float
    horizontal_span: float
    vertical_span: float
    displacement_px: float | None


def is_reliable(evidence: MotionEvidence) -> bool:
    return (evidence.matched_points >= CAMERA_MIN_INLIERS and
            evidence.inlier_points >= CAMERA_MIN_INLIERS and
            evidence.inlier_points / evidence.matched_points >= CAMERA_MIN_INLIER_FRACTION and
            evidence.coverage_fraction >= CAMERA_MIN_COVERAGE and
            min(evidence.horizontal_span, evidence.vertical_span) >= CAMERA_MIN_SPAN and
            evidence.displacement_px is not None and isfinite(evidence.displacement_px))


def summarize_motion(samples: list[MotionEvidence], width: int, height: int,
                     largest_timestamp_gap: float) -> dict:
    threshold = hypot(width, height) * CAMERA_DRIFT_DIAGONAL_FRACTION
    reliable = [sample for sample in samples if is_reliable(sample)]
    moving = [sample for sample in reliable if sample.displacement_px > threshold]
    enough_evidence = (len(reliable) >= CAMERA_MIN_COMPARISONS and
                       len(reliable) == len(samples) and
                       largest_timestamp_gap <= CAMERA_SAMPLE_INTERVAL_SECONDS * 1.5)
    if moving:
        status = "movement_detected"
        message = "Camera movement detected. Do not reuse frame calibration across this clip."
    elif enough_evidence:
        status = "no_movement_detected"
        message = "No movement above the threshold in sampled frames. Review table alignment before reuse."
    else:
        status = "uncertain"
        message = "Camera movement is inconclusive. Treat calibration as frame-local."
    maximum = max((sample.displacement_px for sample in reliable), default=None)
    return {"status": status, "message": message,
            "calibration_reuse": "review_required" if status == "no_movement_detected" else "blocked",
            "reference_frame_index": 0, "sample_interval_seconds": CAMERA_SAMPLE_INTERVAL_SECONDS,
            "checked_comparisons": len(samples), "reliable_comparisons": len(reliable),
            "inconclusive_comparisons": len(samples) - len(reliable),
            "maximum_estimated_displacement_px": round(maximum, 3) if maximum is not None else None,
            "displacement_threshold_px": round(threshold, 3),
            "movement_frame_indices": [sample.frame_index for sample in moving]}
