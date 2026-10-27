from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from backend.adapters.table_geometry import table_homography
from backend.config import (MAX_DURATION_SECONDS, MAX_HEIGHT, MAX_VIDEO_BYTES,
                            MAX_WIDTH, TEMPLATE_DIRECTORY)
from backend.schemas import CalibrationRequest
from backend.services.calibration import CalibrationError, validate_corners

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATE_DIRECTORY)


@router.get("/")
def workspace(request: Request):
    limits = {"max_bytes": MAX_VIDEO_BYTES, "max_duration": MAX_DURATION_SECONDS,
              "max_width": MAX_WIDTH, "max_height": MAX_HEIGHT}
    return templates.TemplateResponse(request=request, name="index.html", context={"limits": limits})


@router.get("/labels")
def label_workspace(request: Request):
    return templates.TemplateResponse(request=request, name="labels.html")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/api/calibration")
def calibrate(payload: CalibrationRequest, request: Request):
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        raise HTTPException(403, "Cross-origin calibration requests are not allowed.")
    try:
        corners = validate_corners(payload.corners, payload.width, payload.height)
        matrix = table_homography(corners)
    except (CalibrationError, ValueError) as error:
        raise HTTPException(422, str(error)) from error
    return {"corners": corners, "homography": matrix, "coordinate_space": "unit_table_plane",
            "warning": "Frame geometry only; not valid for airborne ball coordinates."}
