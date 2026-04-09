"""
NDVI API Routes

Endpoints for computing and retrieving NDVI analysis results.
"""

from fastapi import APIRouter, HTTPException
from backend.utils.validators import NDVIRequest
from backend.utils.exceptions import NoDataAvailableError
from backend.services.ndvi_service import calculate_ndvi
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ndvi", tags=["NDVI"])


@router.post("/", summary="Compute NDVI for a given AOI and date range")
def get_ndvi(request: NDVIRequest):
    """
    Compute NDVI (Normalized Difference Vegetation Index).

    **Formula**: NDVI = (NIR - Red) / (NIR + Red)

    Uses Sentinel-2 Band 8 (NIR, 842nm) and Band 4 (Red, 665nm).
    Returns a tile URL for map visualization and statistical summary.

    **Request Body**:
    - `bbox`: [west, south, east, north] in decimal degrees
    - `start_date`: Start date (YYYY-MM-DD)
    - `end_date`: End date (YYYY-MM-DD)
    - `scale`: Resolution in meters (default: 100)
    """
    try:
        result = calculate_ndvi(
            bbox=request.bbox,
            start_date=request.start_date,
            end_date=request.end_date,
            scale=request.scale,
        )
        return {"status": "success", "data": result}

    except NoDataAvailableError as exc:
        logger.warning("No data available for NDVI request: %s", exc)
        raise HTTPException(
            status_code=404,
            detail={
                "error_type": "no_data_available",
                "message": str(exc),
                "details": exc.details,
            },
        )
    except ValueError as exc:
        logger.error("Validation error in NDVI: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("NDVI computation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"NDVI computation failed: {str(exc)}")
