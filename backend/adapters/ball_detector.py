"""Experimental bright-moving-blob candidates, not confirmed ball observations."""
from collections.abc import Callable

import cv2
import numpy as np

from backend.config import (BALL_APPEARANCE_MIN_AREA, BALL_BACKGROUND_PADDING,
                            BALL_MAX_BACKGROUND_VALUE, BALL_MIN_BACKGROUND_CONTRAST, BALL_MIN_FILL_RATIO,
                            BALL_MIN_MOVING_FRACTION, BALL_MIN_MOVING_PIXELS, BALL_CONTRAST_WINDOW, BALL_MAX_AREA, BALL_MAX_ASPECT, BALL_MAX_CANDIDATES,
                            BALL_MAX_EXTENT, BALL_MAX_SATURATION, BALL_MIN_AREA,
                            BALL_MIN_CONTRAST, BALL_MIN_MOTION, BALL_MIN_VALUE,
                            BALL_REFERENCE_WIDTH)
from backend.services.ball_observations import BallCandidate, CandidateBatch


def find_ball_candidates(previous: np.ndarray, current: np.ndarray,
                         region: tuple[int, int, int, int], *,
                         minimum_area: int = BALL_MIN_AREA) -> CandidateBatch:
    if previous.shape != current.shape or current.ndim != 3 or current.shape[2] != 3:
        raise ValueError("Candidate frames must have matching BGR source dimensions.")
    if not isinstance(minimum_area, int) or not 1 <= minimum_area <= BALL_MAX_AREA:
        raise ValueError("The candidate area must be a positive bounded reference-pixel count.")
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
        if not minimum_area * scale ** 2 <= area <= BALL_MAX_AREA * scale ** 2:
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


def find_appearance_candidates(previous: np.ndarray, current: np.ndarray,
                               region: tuple[int, int, int, int], *,
                               on_component: Callable[[dict], None] | None = None,
                               relative_background: bool = False) -> CandidateBatch:
    """Measure full bright shapes; motion validates them without clipping centers."""
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
    window = max(3, round(BALL_CONTRAST_WINDOW * scale) | 1)
    contrast = gray.astype(np.int16) - cv2.GaussianBlur(gray, (window, window), 0).astype(np.int16)
    motion = gray.astype(np.int16) - before.astype(np.int16)
    mask = ((hsv[:, :, 2] >= BALL_MIN_VALUE) & (hsv[:, :, 1] <= BALL_MAX_SATURATION) &
            (contrast >= BALL_MIN_CONTRAST)).astype(np.uint8)
    count, labels, statistics, centers = cv2.connectedComponentsWithStats(mask[top:bottom, left:right])
    padding = max(1, round(BALL_BACKGROUND_PADDING * scale))
    candidates = []
    for label in range(1, count):
        local_x, local_y, blob_width, blob_height, area = map(int, statistics[label])
        x, y = local_x + left, local_y + top
        center_x, center_y = centers[label]
        reason = None
        moving_pixels = None
        background_value = None
        foreground_value = None
        fill = area / (blob_width * blob_height)
        if not BALL_APPEARANCE_MIN_AREA * scale ** 2 <= area <= BALL_MAX_AREA * scale ** 2:
            reason = "area"
        elif max(blob_width, blob_height) > BALL_MAX_EXTENT * scale:
            reason = "extent"
        elif max(blob_width, blob_height) / min(blob_width, blob_height) > BALL_MAX_ASPECT:
            reason = "aspect"
        elif fill < BALL_MIN_FILL_RATIO:
            reason = "fill"
        if reason is None:
            component = labels[local_y:local_y + blob_height, local_x:local_x + blob_width] == label
            moving_pixels = int(np.count_nonzero(component &
                (motion[y:y + blob_height, x:x + blob_width] >= BALL_MIN_MOTION)))
            if moving_pixels < max(BALL_MIN_MOVING_PIXELS * scale ** 2, BALL_MIN_MOVING_FRACTION * area):
                reason = "motion"
        if reason is None:
            x0, y0 = max(0, x - padding), max(0, y - padding)
            x1, y1 = min(width, x + blob_width + padding), min(height, y + blob_height + padding)
            ring = np.ones((y1 - y0, x1 - x0), dtype=bool)
            ring[y - y0:y - y0 + blob_height, x - x0:x - x0 + blob_width] = False
            if np.any(ring):
                background_value = float(np.median(hsv[y0:y1, x0:x1, 2][ring]))
            if background_value is None or background_value > BALL_MAX_BACKGROUND_VALUE:
                reason = "background"
                if relative_background and background_value is not None:
                    foreground_value = float(np.median(hsv[y:y + blob_height, x:x + blob_width, 2][component]))
                    if foreground_value - background_value >= BALL_MIN_BACKGROUND_CONTRAST:
                        reason = None
        if on_component is not None:
            on_component(dict(center=[float(center_x + left), float(center_y + top)],
                              box=[x, y, blob_width, blob_height], area=area, fill=fill,
                              moving_pixels=moving_pixels, background_value=background_value, foreground_value=foreground_value,
                              rejection_reason=reason))
        if reason is None:
            candidates.append(BallCandidate(float(center_x + left), float(center_y + top), area,
                                            (x, y, blob_width, blob_height)))
    candidates.sort(key=lambda candidate: (-candidate.area, candidate.x, candidate.y))
    return CandidateBatch(candidates[:BALL_MAX_CANDIDATES], len(candidates) > BALL_MAX_CANDIDATES)
