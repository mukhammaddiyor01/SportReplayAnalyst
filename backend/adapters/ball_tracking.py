"""Compose source decoding/candidates with the pure temporal service."""
from collections import Counter
from dataclasses import asdict

from backend.adapters.ball_detector import find_appearance_candidates, find_ball_candidates
from backend.adapters.video_reader import VideoError, VideoFrame
from backend.config import BALL_CONTINUATION_MIN_AREA, BALL_MIN_AREA, TRACK_MAX_GAP_SECONDS
from backend.services.ball_observations import CandidateBatch
from backend.services.ball_tracker import BallTracker
from backend.services.tracking_review import tracking_gaps


class TrackingRun:
    def __init__(self, region: tuple[int, int, int, int], *, small_candidate_continuation: bool = False,
                 appearance_filter: bool = True):
        self.appearance_filter = appearance_filter and not small_candidate_continuation
        self.small_candidate_continuation = small_candidate_continuation
        self.region = region
        self.previous = None
        self.tracker = None
        self.frames = []
        self.counts = Counter()

    def consume(self, frame: VideoFrame) -> CandidateBatch:
        height, width = frame.image.shape[:2]
        if self.tracker is None:
            left, top, right, bottom = self.region
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise VideoError("The tracking search window is outside the source video.")
            self.tracker = BallTracker(width, height)
        last = self.tracker.last_observation
        continuing = (self.small_candidate_continuation and last is not None and
                      0 < frame.timestamp_seconds - last.timestamp <= TRACK_MAX_GAP_SECONDS)
        minimum_area = BALL_CONTINUATION_MIN_AREA if continuing else BALL_MIN_AREA
        if self.previous is None:
            batch = CandidateBatch([])
        elif self.appearance_filter:
            batch = find_appearance_candidates(self.previous, frame.image, self.region)
        else:
            batch = find_ball_candidates(self.previous, frame.image, self.region, minimum_area=minimum_area)
        update = self.tracker.update(batch, frame.index, frame.timestamp_seconds)
        record = asdict(update)
        record["timestamp_source"] = frame.timestamp_source
        record["candidate_count"] = len(batch.candidates)
        self.frames.append(record)
        self.counts[update.status] += 1
        self.previous = frame.image
        return batch

    def result(self) -> dict:
        return {"mode": "experimental_image_space",
                "detector": "full_shape_v1" if self.appearance_filter else "motion_clipped_v1",
                "search_region": list(self.region),
                "status_counts": dict(self.counts), "frames": self.frames,
                "review_gaps": tracking_gaps(self.frames),
                "track_count": self.tracker.next_track_id - 1 if self.tracker else 0,
                "warning": "Experimental associations in image pixels. Predictions are not observations; contacts and rallies are not inferred."}
