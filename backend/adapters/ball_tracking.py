"""Compose source decoding/candidates with the pure temporal service."""
from collections import Counter
from dataclasses import asdict

from backend.adapters.ball_detector import find_ball_candidates
from backend.adapters.video_reader import VideoError, VideoFrame
from backend.services.ball_observations import CandidateBatch
from backend.services.ball_tracker import BallTracker


class TrackingRun:
    def __init__(self, region: tuple[int, int, int, int]):
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
        batch = CandidateBatch([]) if self.previous is None else find_ball_candidates(
            self.previous, frame.image, self.region)
        update = self.tracker.update(batch, frame.index, frame.timestamp_seconds)
        record = asdict(update)
        record["timestamp_source"] = frame.timestamp_source
        record["candidate_count"] = len(batch.candidates)
        self.frames.append(record)
        self.counts[update.status] += 1
        self.previous = frame.image
        return batch

    def result(self) -> dict:
        return {"mode": "experimental_image_space", "search_region": list(self.region),
                "status_counts": dict(self.counts), "frames": self.frames,
                "track_count": self.tracker.next_track_id - 1 if self.tracker else 0,
                "warning": "Experimental associations in image pixels. Predictions are not observations; contacts and rallies are not inferred."}
