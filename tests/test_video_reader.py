from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import cv2
import numpy as np

from backend.adapters.video_reader import VideoError, inspect_video, read_frames


class VideoReaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "clip.mp4"
        writer = cv2.VideoWriter(str(self.path), cv2.VideoWriter_fourcc(*"mp4v"), 20, (64, 48))
        self.assertTrue(writer.isOpened())
        for index in range(10):
            image = np.zeros((48, 64, 3), dtype=np.uint8)
            cv2.circle(image, (10 + index * 3, 20), 3, (255, 255, 255), -1)
            writer.write(image)
        writer.release()

    def test_all_frames_keep_source_geometry_and_time(self):
        frames = list(read_frames(self.path))
        self.assertEqual([frame.index for frame in frames], list(range(10)))
        self.assertTrue(all(frame.image.shape == (48, 64, 3) for frame in frames))
        self.assertAlmostEqual(frames[-1].timestamp_seconds, .45, places=3)
        self.assertTrue(all(b.timestamp_seconds > a.timestamp_seconds
                            for a, b in zip(frames, frames[1:])))
        self.assertEqual(inspect_video(self.path)["decoded_frames"], 10)

    def test_missing_and_empty_files(self):
        with self.assertRaises(VideoError):
            list(read_frames(self.path.parent / "missing.mp4"))
        self.path.write_bytes(b"")
        with self.assertRaises(VideoError):
            list(read_frames(self.path))

    def test_corrupt_content(self):
        self.path.write_bytes(b"this is not a video")
        with self.assertRaises(VideoError):
            inspect_video(self.path)

    def test_byte_dimension_fps_and_duration_limits(self):
        for setting, value in [("MAX_VIDEO_BYTES", 10), ("MAX_WIDTH", 32),
                               ("MAX_FPS", 10), ("MAX_DURATION_SECONDS", .2)]:
            with self.subTest(setting=setting):
                with patch("backend.adapters.video_reader." + setting, value):
                    with self.assertRaises(VideoError):
                        inspect_video(self.path)

    def test_explicit_fallback_for_broken_presentation_times(self):
        original = cv2.VideoCapture
        class MissingTimestamps:
            def __init__(self, path):
                self.capture = original(path)
            def get(self, property_id):
                if property_id == cv2.CAP_PROP_POS_MSEC:
                    return float("nan")
                return self.capture.get(property_id)
            def isOpened(self):
                return self.capture.isOpened()
            def read(self):
                return self.capture.read()
            def release(self):
                return self.capture.release()
        with patch("backend.adapters.video_reader.cv2.VideoCapture", MissingTimestamps):
            report = inspect_video(self.path)
        self.assertEqual(report["fps_fallback_frames"], 10)
        self.assertAlmostEqual(report["last_timestamp_seconds"], .45)
