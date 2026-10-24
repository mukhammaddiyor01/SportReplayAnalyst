"""Validate table geometry without web or vision dependencies."""
from math import isfinite


class CalibrationError(ValueError):
    pass


def validate_corners(corners: list, width: int, height: int) -> list[tuple[float, float]]:
    if width < 2 or height < 2:
        raise CalibrationError("Video dimensions are invalid.")
    if len(corners) != 4:
        raise CalibrationError("Select exactly four table corners.")
    points = []
    for corner in corners:
        if len(corner) != 2:
            raise CalibrationError("Each corner needs an x and y coordinate.")
        x, y = corner
        if not isfinite(x) or not isfinite(y) or not (0 <= x < width and 0 <= y < height):
            raise CalibrationError("Table corners must be inside the source frame.")
        points.append((float(x), float(y)))
    # In image coordinates y increases downward: clockwise turns are positive.
    for index in range(4):
        a, b, c = (points[(index + offset) % 4] for offset in range(3))
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cross <= 0:
            raise CalibrationError("Select distinct corners clockwise around a convex table.")
    area = abs(sum(points[i][0] * points[(i + 1) % 4][1] -
                   points[(i + 1) % 4][0] * points[i][1] for i in range(4))) / 2
    if area < width * height * .01:
        raise CalibrationError("The selected table is too small; select the full playing surface.")
    return points
