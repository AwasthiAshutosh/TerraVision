"""
Change Detection API Routes

Endpoints for temporal forest change analysis.
"""

from fastapi import APIRouter, HTTPException
from backend.utils.validators import ChangeDetectionRequest
from backend.utils.exceptions import NoDataAvailableError
from backend.services.change_service import detect_changes
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/change-detection", tags=["Change Detection"])


@router.post("/", summary="Detect forest changes between two time periods")
def get_change_detection(request: ChangeDetectionRequest):
    """
    Detect forest cover changes by comparing NDVI between two periods.

    **Algorithm**:
    1. Compute median NDVI composite for each period
    2. Calculate ΔNDVI = NDVI₂ - NDVI₁
    3. Classify:
       - ΔNDVI < -threshold → Forest Loss
       - ΔNDVI > +threshold → Forest Gain
       - Otherwise → Stable

    Returns area statistics and change map tile URL.
    """
    try:
        result = detect_changes(
            bbox=request.bbox,
            period1_start=request.period1_start,
            period1_end=request.period1_end,
            period2_start=request.period2_start,
            period2_end=request.period2_end,
            scale=request.scale,
            change_threshold=request.change_threshold,
        )
        return {"status": "success", "data": result}

    except NoDataAvailableError as exc:
        logger.warning("No data available for change detection: %s", exc)
        raise HTTPException(
            status_code=404,
            detail={
                "error_type": "no_data_available",
                "message": str(exc),
                "details": exc.details,
            },
        )
    except ValueError as exc:
        logger.error("Validation error in change detection: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Change detection failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Change detection failed: {str(exc)}")
