"""Experimental image-space association, independent of OpenCV and HTTP."""
from dataclasses import dataclass
from math import hypot, isfinite

from backend.config import (TRACK_AMBIGUITY_MARGIN_DIAGONAL, TRACK_BASE_GATE_DIAGONAL,
                            TRACK_CONFIRMATION_COUNT, TRACK_GATE_GROWTH_DIAGONAL,
                            TRACK_MAX_GAP_SECONDS, TRACK_MAX_SPEED_DIAGONAL,
                            TRACK_MIN_INITIAL_DISPLACEMENT_DIAGONAL, TRACK_INITIAL_GAP_SECONDS,
                            TRACK_MAX_INITIAL_HYPOTHESES)
from backend.services.ball_observations import BallCandidate, CandidateBatch


@dataclass(frozen=True)
class TrackUpdate:
    frame_index: int
    timestamp_seconds: float
    status: str
    track_id: int | None = None
    observation: tuple[float, float] | None = None
    prediction: tuple[float, float] | None = None
    break_before: bool = True


@dataclass(frozen=True)
class Observation:
    frame_index: int
    timestamp: float
    x: float
    y: float


class BallTracker:
    def __init__(self, width: int, height: int, *, temporal_initialization: bool = False):
        if width < 2 or height < 2:
            raise ValueError("Source dimensions must be positive.")
        self.temporal_initialization = temporal_initialization
        self.width = width
        self.height = height
        self.diagonal = hypot(width, height)
        self.reset()

    def reset(self) -> None:
        self.last_input_index = -1
        self.last_input_time = -1.0
        self.last_observation = None
        self.velocity = (0.0, 0.0)
        self.seeds = []
        self.hypotheses = []
        self.track_id = None
        self.next_track_id = 1

    def _validate(self, batch: CandidateBatch, index: int, timestamp: float) -> None:
        if index <= self.last_input_index or not isfinite(timestamp) or timestamp < 0 or timestamp <= self.last_input_time:
            raise ValueError("Tracking requires increasing source frame indices and timestamps.")
        for candidate in batch.candidates:
            if not (isfinite(candidate.x) and isfinite(candidate.y) and
                    0 <= candidate.x < self.width and 0 <= candidate.y < self.height):
                raise ValueError("Candidate coordinates must be finite and inside the source image.")

    def update(self, batch: CandidateBatch, index: int, timestamp: float) -> TrackUpdate:
        self._validate(batch, index, timestamp)
        self.last_input_index = index
        self.last_input_time = timestamp
        if self.last_observation is not None and timestamp - self.last_observation.timestamp > TRACK_MAX_GAP_SECONDS:
            self.last_observation = None
            self.track_id = None
            self.seeds = []
        if self.last_observation is None and self.temporal_initialization:
            return self._initialize_temporal(batch, index, timestamp)
        if self.last_observation is None:
            return self._initialize(batch, index, timestamp)

        last = self.last_observation
        elapsed = timestamp - last.timestamp
        predicted = (last.x + self.velocity[0] * elapsed, last.y + self.velocity[1] * elapsed)
        if batch.truncated:
            return self._missing(index, timestamp, "ambiguous", predicted)
        gate = self.diagonal * (TRACK_BASE_GATE_DIAGONAL + TRACK_GATE_GROWTH_DIAGONAL * elapsed)
        possible = []
        for candidate in batch.candidates:
            distance = hypot(candidate.x - predicted[0], candidate.y - predicted[1])
            speed = hypot(candidate.x - last.x, candidate.y - last.y) / elapsed
            if distance <= gate and speed <= self.diagonal * TRACK_MAX_SPEED_DIAGONAL:
                possible.append((distance, candidate))
        possible.sort(key=lambda pair: pair[0])
        if not possible:
            return self._missing(index, timestamp, "predicted", predicted)
        if len(possible) > 1 and possible[1][0] - possible[0][0] < self.diagonal * TRACK_AMBIGUITY_MARGIN_DIAGONAL:
            return self._missing(index, timestamp, "ambiguous", predicted)
        selected = possible[0][1]
        self.velocity = ((selected.x - last.x) / elapsed, (selected.y - last.y) / elapsed)
        self.last_observation = Observation(index, timestamp, selected.x, selected.y)
        return TrackUpdate(index, timestamp, "observed", self.track_id,
                           (selected.x, selected.y), break_before=index != last.frame_index + 1)

    def _initialize(self, batch: CandidateBatch, index: int, timestamp: float) -> TrackUpdate:
        if batch.truncated or len(batch.candidates) > 1:
            self.seeds = []
            return TrackUpdate(index, timestamp, "ambiguous")
        if not batch.candidates:
            self.seeds = []
            return TrackUpdate(index, timestamp, "searching")
        candidate = batch.candidates[0]
        if self.seeds:
            last = self.seeds[-1]
            elapsed = timestamp - last.timestamp
            speed = hypot(candidate.x - last.x, candidate.y - last.y) / elapsed
            if index != last.frame_index + 1 or elapsed > TRACK_MAX_GAP_SECONDS or speed > self.diagonal * TRACK_MAX_SPEED_DIAGONAL:
                self.seeds = []
            elif len(self.seeds) >= 2:
                before = self.seeds[-2]
                duration = last.timestamp - before.timestamp
                predicted = (last.x + (last.x - before.x) / duration * elapsed,
                             last.y + (last.y - before.y) / duration * elapsed)
                if hypot(candidate.x - predicted[0], candidate.y - predicted[1]) > self.diagonal * TRACK_BASE_GATE_DIAGONAL:
                    self.seeds = []
        self.seeds.append(Observation(index, timestamp, candidate.x, candidate.y))
        self.seeds = self.seeds[-TRACK_CONFIRMATION_COUNT:]
        if len(self.seeds) < TRACK_CONFIRMATION_COUNT:
            return TrackUpdate(index, timestamp, "tentative")
        first, last = self.seeds[0], self.seeds[-1]
        if hypot(last.x - first.x, last.y - first.y) < self.diagonal * TRACK_MIN_INITIAL_DISPLACEMENT_DIAGONAL:
            return TrackUpdate(index, timestamp, "tentative")
        self.track_id = self.next_track_id
        self.next_track_id += 1
        previous = self.seeds[-2]
        elapsed = last.timestamp - previous.timestamp
        self.velocity = ((last.x - previous.x) / elapsed, (last.y - previous.y) / elapsed)
        self.last_observation = last
        self.seeds = []
        return TrackUpdate(index, timestamp, "observed", self.track_id, (last.x, last.y))

    def _initialize_temporal(self, batch: CandidateBatch, index: int, timestamp: float) -> TrackUpdate:
        if batch.truncated:
            self.hypotheses = []
            return TrackUpdate(index, timestamp, "ambiguous")
        # Keep actual observations only; no point is inserted for a missing frame.
        paths = [path for path in self.hypotheses
                 if timestamp - path[-1].timestamp <= TRACK_INITIAL_GAP_SECONDS]
        extended = []
        for path in paths:
            last = path[-1]
            elapsed = timestamp - last.timestamp
            matches = []
            for candidate in batch.candidates:
                if hypot(candidate.x - last.x, candidate.y - last.y) / elapsed > self.diagonal * TRACK_MAX_SPEED_DIAGONAL:
                    continue
                if len(path) >= 2:
                    before = path[-2]
                    duration = last.timestamp - before.timestamp
                    predicted = (last.x + (last.x - before.x) / duration * elapsed,
                                 last.y + (last.y - before.y) / duration * elapsed)
                    if hypot(candidate.x - predicted[0], candidate.y - predicted[1]) > self.diagonal * TRACK_BASE_GATE_DIAGONAL:
                        continue
                matches.append(candidate)
            if not matches:
                extended.append(path)
            for candidate in matches:
                observation = Observation(index, timestamp, candidate.x, candidate.y)
                extended.append((path + [observation])[-TRACK_CONFIRMATION_COUNT:])
        extended.extend([[Observation(index, timestamp, c.x, c.y)] for c in batch.candidates])
        unique = {tuple((o.frame_index, o.x, o.y) for o in path): path for path in extended}
        if len(unique) > TRACK_MAX_INITIAL_HYPOTHESES:
            self.hypotheses = []
            return TrackUpdate(index, timestamp, "ambiguous")
        self.hypotheses = list(unique.values())
        # Competing complete histories with the same endpoint are still ambiguous.
        complete = [path for path in self.hypotheses
                    if len(path) == TRACK_CONFIRMATION_COUNT and path[-1].frame_index == index and
                    hypot(path[-1].x - path[0].x, path[-1].y - path[0].y) >=
                    self.diagonal * TRACK_MIN_INITIAL_DISPLACEMENT_DIAGONAL]
        if len(complete) != 1:
            state = ("ambiguous" if len(complete) > 1 or len(batch.candidates) > 1 else
                     "tentative" if batch.candidates else "searching")
            return TrackUpdate(index, timestamp, state)
        previous, last = complete[0][-2:]
        elapsed = last.timestamp - previous.timestamp
        self.velocity = ((last.x - previous.x) / elapsed, (last.y - previous.y) / elapsed)
        self.last_observation = last
        self.track_id = self.next_track_id
        self.next_track_id += 1
        self.hypotheses = []
        return TrackUpdate(index, timestamp, "observed", self.track_id, (last.x, last.y))

    def _missing(self, index: int, timestamp: float, status: str,
                 predicted: tuple[float, float]) -> TrackUpdate:
        inside = 0 <= predicted[0] < self.width and 0 <= predicted[1] < self.height
        return TrackUpdate(index, timestamp, status, self.track_id,
                           prediction=predicted if inside else None)
