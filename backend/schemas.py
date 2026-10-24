from pydantic import BaseModel, ConfigDict, Field

from backend.config import MAX_HEIGHT, MAX_WIDTH


class CalibrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    width: int = Field(ge=2, le=MAX_WIDTH)
    height: int = Field(ge=2, le=MAX_HEIGHT)
    corners: list[list[float]] = Field(min_length=4, max_length=4)
