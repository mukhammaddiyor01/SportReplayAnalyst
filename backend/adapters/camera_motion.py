"""Track distributed scene features against the first frame; no stabilization."""
import cv2
import numpy as np

from backend.config import (CAMERA_FLOW_ERROR_PX, CAMERA_FLOW_WINDOW,
                            CAMERA_MAX_FEATURES, CAMERA_PROCESSING_WIDTH,
                            CAMERA_RANSAC_ERROR_PX)
from backend.services.camera_motion import MotionEvidence


class CameraMotionEstimator:
    def __init__(self, reference: np.ndarray):
        self.source_height, self.source_width = reference.shape[:2]
        self.reference = self._gray(reference)
        height, width = self.reference.shape
        mask = np.full((height, width), 255, dtype=np.uint8)
        # Avoid the central play/net region and a common lower-left overlay area.
        # Static overlays must not dominate apparent background correspondence.
        mask[int(height * .4):int(height * .6), :] = 0
        mask[int(height * .85):, :int(width * .3)] = 0
        self.points = cv2.goodFeaturesToTrack(self.reference, maxCorners=CAMERA_MAX_FEATURES,
                                             qualityLevel=.015, minDistance=6, mask=mask)

    def _gray(self, image: np.ndarray) -> np.ndarray:
        width = min(self.source_width, CAMERA_PROCESSING_WIDTH)
        height = round(self.source_height * width / self.source_width)
        resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    def measure(self, image: np.ndarray, index: int, timestamp: float) -> MotionEvidence:
        empty = MotionEvidence(index, timestamp, 0, 0, 0, 0, 0, None)
        if self.points is None or len(self.points) < 3:
            return empty
        current = self._gray(image)
        options = {"winSize": (CAMERA_FLOW_WINDOW, CAMERA_FLOW_WINDOW), "maxLevel": 4}
        moved, forward_ok, _ = cv2.calcOpticalFlowPyrLK(self.reference, current, self.points, None, **options)
        if moved is None:
            return empty
        returned, backward_ok, _ = cv2.calcOpticalFlowPyrLK(current, self.reference, moved, None, **options)
        if returned is None:
            return empty
        height, width = current.shape
        coordinates = moved.reshape(-1, 2)
        valid = ((forward_ok.ravel() == 1) & (backward_ok.ravel() == 1) &
                 (np.linalg.norm(self.points - returned, axis=2).ravel() < CAMERA_FLOW_ERROR_PX) &
                 np.isfinite(coordinates).all(axis=1) &
                 (coordinates[:, 0] >= 0) & (coordinates[:, 0] < width) &
                 (coordinates[:, 1] >= 0) & (coordinates[:, 1] < height))
        source = self.points[valid].reshape(-1, 2)
        target = coordinates[valid]
        if len(source) < 3:
            return empty
        matrix, inliers = cv2.estimateAffinePartial2D(source, target, method=cv2.RANSAC,
                                                     ransacReprojThreshold=CAMERA_RANSAC_ERROR_PX)
        if matrix is None or inliers is None or not np.isfinite(matrix).all():
            return empty
        supported = source[inliers.ravel() == 1]
        if len(supported) < 3:
            return empty
        coverage = cv2.contourArea(cv2.convexHull(supported)) / (width * height)
        span = np.ptp(supported, axis=0) / np.array([width, height])
        frame_corners = np.float32([[[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]])
        warped = cv2.transform(frame_corners, matrix)
        # Convert processing-space shifts back to the original source axes.
        source_scale = np.array([self.source_width / width, self.source_height / height])
        displacement = np.max(np.linalg.norm((warped - frame_corners) * source_scale, axis=2))
        return MotionEvidence(index, timestamp, len(source), len(supported), float(coverage),
                              float(span[0]), float(span[1]), float(displacement))
