from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.config import MAX_HEIGHT, MAX_WIDTH


class CalibrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    width: int = Field(ge=2, le=MAX_WIDTH)
    height: int = Field(ge=2, le=MAX_HEIGHT)
    corners: list[list[float]] = Field(min_length=4, max_length=4)


class InspectionOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["inspect", "track"] = "inspect"
    search_region: tuple[int, int, int, int] | None = None

    @model_validator(mode="after")
    def check_search_region(self):
        if self.mode == "inspect":
            if self.search_region is not None:
                raise ValueError("Inspection mode does not use a tracking search window.")
            return self
        if self.search_region is None:
            raise ValueError("Tracking requires an explicit image search window.")
        left, top, right, bottom = self.search_region
        if not (0 <= left < right <= MAX_WIDTH and 0 <= top < bottom <= MAX_HEIGHT):
            raise ValueError("The search window must fit within supported source dimensions.")
        return self
