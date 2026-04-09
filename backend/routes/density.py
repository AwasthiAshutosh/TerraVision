"""
Forest Density API Routes

Endpoints for forest canopy density classification.
"""

from fastapi import APIRouter, HTTPException
from backend.utils.validators import DensityRequest
from backend.utils.exceptions import NoDataAvailableError
from backend.services.density_service import classify_density, DEFAULT_THRESHOLDS
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/density", tags=["Density"])


@router.post("/", summary="Classify forest canopy density")
def get_density(request: DensityRequest):
    """
    Classify forest canopy density from NDVI values.

    Applies scientifically-defined thresholds to classify each pixel into:
    - Dense Forest (NDVI > 0.7)
    - Moderate Forest (0.5 – 0.7)
    - Sparse Vegetation (0.3 – 0.5)
    - Grassland/Crops (0.1 – 0.3)
    - Non-Vegetation (< 0.1)

    Returns area statistics (hectares and percentages) per category.
    """
    try:
        result = classify_density(
            bbox=request.bbox,
            start_date=request.start_date,
            end_date=request.end_date,
            scale=request.scale,
            thresholds=request.thresholds or DEFAULT_THRESHOLDS,
        )
        return {"status": "success", "data": result}

    except NoDataAvailableError as exc:
        logger.warning("No data available for density request: %s", exc)
        raise HTTPException(
            status_code=404,
            detail={
                "error_type": "no_data_available",
                "message": str(exc),
                "details": exc.details,
            },
        )
    except ValueError as exc:
        logger.error("Validation error in density: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Density classification failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Density classification failed: {str(exc)}")


@router.get("/thresholds", summary="Get default density thresholds")
def get_thresholds():
    """Return the default NDVI thresholds used for density classification."""
    return {"status": "success", "data": DEFAULT_THRESHOLDS}
