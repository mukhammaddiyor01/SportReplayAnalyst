"""Experimental bright-moving-blob candidates, not confirmed ball observations."""
import cv2
import numpy as np

from backend.config import (BALL_CONTRAST_WINDOW, BALL_MAX_AREA, BALL_MAX_ASPECT, BALL_MAX_CANDIDATES,
                            BALL_MAX_EXTENT, BALL_MAX_SATURATION, BALL_MIN_AREA,
                            BALL_MIN_CONTRAST, BALL_MIN_MOTION, BALL_MIN_VALUE,
                            BALL_REFERENCE_WIDTH)
from backend.services.ball_observations import BallCandidate, CandidateBatch


def find_ball_candidates(previous: np.ndarray, current: np.ndarray,
                         region: tuple[int, int, int, int]) -> CandidateBatch:
    if previous.shape != current.shape or current.ndim != 3 or current.shape[2] != 3:
        raise ValueError("Candidate frames must have matching BGR source dimensions.")
    height, width = current.shape[:2]
    left, top, right, bottom = region
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("The image search window must be inside the source frame.")
    scale = width / BALL_REFERENCE_WIDTH
    gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    before = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(current, cv2.COLOR_BGR2HSV)
    bright = cv2.inRange(hsv, (0, 0, BALL_MIN_VALUE), (179, BALL_MAX_SATURATION, 255))
    window = max(3, round(BALL_CONTRAST_WINDOW * scale) | 1)
    local_background = cv2.GaussianBlur(gray, (window, window), 0)
    contrast = gray.astype(np.int16) - local_background.astype(np.int16)
    positive_motion = gray.astype(np.int16) - before.astype(np.int16)
    mask = np.where((bright > 0) & (contrast >= BALL_MIN_CONTRAST) &
                    (positive_motion >= BALL_MIN_MOTION), 255, 0).astype(np.uint8)
    search = mask[top:bottom, left:right]
    count, _, statistics, centers = cv2.connectedComponentsWithStats(search, connectivity=8)
    candidates = []
    for label in range(1, count):
        x, y, blob_width, blob_height, area = map(int, statistics[label])
        if not BALL_MIN_AREA * scale ** 2 <= area <= BALL_MAX_AREA * scale ** 2:
            continue
        if max(blob_width, blob_height) > BALL_MAX_EXTENT * scale:
            continue
        if max(blob_width, blob_height) / min(blob_width, blob_height) > BALL_MAX_ASPECT:
            continue
        center_x, center_y = centers[label]
        candidates.append(BallCandidate(float(center_x + left), float(center_y + top), area,
                                        (x + left, y + top, blob_width, blob_height)))
    candidates.sort(key=lambda candidate: (-candidate.area, candidate.x, candidate.y))
    return CandidateBatch(candidates[:BALL_MAX_CANDIDATES], len(candidates) > BALL_MAX_CANDIDATES)
