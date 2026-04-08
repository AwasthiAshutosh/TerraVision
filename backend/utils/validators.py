"""
Input Validation Utilities

Provides Pydantic models for validating API request inputs such as
bounding boxes, date ranges, and processing parameters.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    """
    Geographic bounding box defined by [west, south, east, north].

    Validates that coordinates are within valid geographic ranges
    and that west < east, south < north.
    """
    bbox: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="[west, south, east, north] in decimal degrees",
    )

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: List[float]) -> List[float]:
        west, south, east, north = v
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if west >= east:
            raise ValueError("West must be less than East")
        if south >= north:
            raise ValueError("South must be less than North")
        return v


class DateRange(BaseModel):
    """Validated date range for satellite imagery queries."""
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date (YYYY-MM-DD)")

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info) -> date:
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        return v


class NDVIRequest(BaseModel):
    """Request parameters for NDVI computation."""
    bbox: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="[west, south, east, north]",
    )
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")
    scale: int = Field(default=100, ge=10, le=1000, description="Resolution in meters")

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: List[float]) -> List[float]:
        west, south, east, north = v
        if west >= east or south >= north:
            raise ValueError("Invalid bounding box")
        return v


class DensityRequest(BaseModel):
    """Request parameters for forest density classification."""
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    start_date: str = Field(...)
    end_date: str = Field(...)
    scale: int = Field(default=100, ge=10, le=1000)
    thresholds: Optional[dict] = Field(
        default=None,
        description="Custom NDVI thresholds for density classes",
    )


class ChangeDetectionRequest(BaseModel):
    """Request parameters for temporal change detection."""
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    period1_start: str = Field(..., description="Period 1 start date")
    period1_end: str = Field(..., description="Period 1 end date")
    period2_start: str = Field(..., description="Period 2 start date")
    period2_end: str = Field(..., description="Period 2 end date")
    scale: int = Field(default=100, ge=10, le=1000)
    change_threshold: float = Field(
        default=0.2,
        ge=0.05,
        le=0.5,
        description="Minimum NDVI difference to flag as change",
    )


class MLPredictionRequest(BaseModel):
    """Request parameters for ML-based prediction."""
    bbox: List[float] = Field(..., min_length=4, max_length=4)
    start_date: str = Field(...)
    end_date: str = Field(...)
    model_type: str = Field(
        default="random_forest",
        description="Model type: random_forest or cnn",
    )
    scale: int = Field(default=100, ge=10, le=1000)
