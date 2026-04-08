"""
ML Prediction API Routes

Endpoints for machine learning-based forest classification.
"""

from fastapi import APIRouter, HTTPException
from backend.utils.validators import MLPredictionRequest
from backend.services.ml_service import predict_forest_type
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ml-prediction", tags=["ML Prediction"])


@router.post("/", summary="Classify forest types using ML model")
def get_ml_prediction(request: MLPredictionRequest):
    """
    Run ML-based forest type classification.

    Uses a trained Random Forest (or CNN) model to classify each pixel
    into forest type categories. Features include spectral bands
    (B2, B3, B4, B8, B11, B12) and derived indices (NDVI, EVI, SAVI).

    If no trained model is available, returns demo predictions.
    """
    try:
        result = predict_forest_type(
            bbox=request.bbox,
            start_date=request.start_date,
            end_date=request.end_date,
            model_type=request.model_type,
            scale=request.scale,
        )
        return {"status": "success", "data": result}

    except ValueError as exc:
        logger.error("Validation error in ML prediction: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("ML prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {str(exc)}")
