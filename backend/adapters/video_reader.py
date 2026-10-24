"""Bounded local decoding; no detection or tracking decisions belong here."""
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

from backend.config import (MAX_DURATION_SECONDS, MAX_FPS, MAX_HEIGHT,
                            MAX_VIDEO_BYTES, MAX_WIDTH)


class VideoError(ValueError):
    pass


@dataclass(frozen=True)
class VideoFrame:
    index: int
    timestamp_seconds: float
    timestamp_source: str
    image: np.ndarray


def read_frames(path: Path) -> Iterator[VideoFrame]:
    if not path.is_file():
        raise VideoError("Choose an existing local video file.")
    if not 0 < path.stat().st_size <= MAX_VIDEO_BYTES:
        raise VideoError("Video must be nonempty and at most 100 MiB.")
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise VideoError("The video could not be opened.")
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not isfinite(fps) or not 0 < fps <= MAX_FPS:
            raise VideoError("Video FPS must be available and at most 120.")
        width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        _validate_dimensions(width, height)
        declared_count = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        if isfinite(declared_count) and declared_count > fps * MAX_DURATION_SECONDS + 1:
            raise VideoError("Video exceeds the 60-second duration limit.")
        index = 0
        previous_time = -1.0
        while True:
            ok, image = capture.read()
            if not ok:
                break
            actual_height, actual_width = image.shape[:2]
            _validate_dimensions(actual_width, actual_height)
            if (actual_width, actual_height) != (width, height):
                raise VideoError("Video dimensions changed during decoding.")
            # Bound actual decoded work even when container metadata is wrong.
            if index >= fps * MAX_DURATION_SECONDS:
                raise VideoError("Decoded video exceeds the 60-second frame budget.")
            timestamp = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
            source = "presentation"
            if not isfinite(timestamp) or timestamp < 0 or timestamp <= previous_time:
                timestamp = max(index / fps, previous_time + 1 / fps)
                source = "fps_fallback"
            if timestamp >= MAX_DURATION_SECONDS:
                raise VideoError("Video timestamps exceed the 60-second limit.")
            yield VideoFrame(index, timestamp, source, image)
            previous_time = timestamp
            index += 1
        if index == 0:
            raise VideoError("Video contains no decodable frames.")
        if isfinite(declared_count) and declared_count > 0 and index < int(declared_count):
            raise VideoError("Decoding ended before the declared final frame; video may be truncated.")
    finally:
        capture.release()


def _validate_dimensions(width: float, height: float) -> None:
    if not (isfinite(width) and isfinite(height) and
            0 < width <= MAX_WIDTH and 0 < height <= MAX_HEIGHT):
        raise VideoError("Video dimensions must be at most 1920 x 1080.")


def inspect_video(path: Path) -> dict:
    count = 0
    fallback_count = 0
    first_time = None
    last_time = None
    max_gap = 0.0
    dimensions = None
    for frame in read_frames(path):
        if first_time is None:
            first_time = frame.timestamp_seconds
            dimensions = [frame.image.shape[1], frame.image.shape[0]]
        if last_time is not None:
            max_gap = max(max_gap, frame.timestamp_seconds - last_time)
        last_time = frame.timestamp_seconds
        fallback_count += frame.timestamp_source == "fps_fallback"
        count += 1
    return {"decoded_frames": count, "source_dimensions": dimensions,
            "first_timestamp_seconds": first_time, "last_timestamp_seconds": last_time,
            "largest_timestamp_gap_seconds": max_gap,
            "fps_fallback_frames": fallback_count,
            "analysis_status": "Video inspected; tracking and events not evaluated."}
