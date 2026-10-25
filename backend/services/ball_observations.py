from dataclasses import dataclass


@dataclass(frozen=True)
class BallCandidate:
    x: float
    y: float
    area: int
    box: tuple[int, int, int, int]


@dataclass(frozen=True)
class CandidateBatch:
    candidates: list[BallCandidate]
    truncated: bool = False
