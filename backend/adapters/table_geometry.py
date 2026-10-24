import cv2
import numpy as np


def table_homography(corners: list[tuple[float, float]]) -> list[list[float]]:
    """Map table-plane corners to a unit square, not airborne ball coordinates."""
    source = np.asarray(corners, dtype=np.float32)
    target = np.asarray([(0, 0), (1, 0), (1, 1), (0, 1)], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(source, target)
    if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-15:
        raise ValueError("Table geometry cannot produce a stable homography.")
    return matrix.tolist()
